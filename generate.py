from datetime import date
from functools import cached_property
from typing import List, Dict
from collections import defaultdict
from os import path
from csv import DictWriter
from dataclasses import dataclass

from gtfs.archive import load_feeds_and_summaries_from_archive
from gtfs.config import EARLIEST_DATE, LATEST_DATE, OUTPUT_PATH
from gtfs.models import ServiceExceptionType, Service
from gtfs.summarize import FeedSummary, TripSummary
from gtfs.time import (
    DAYS_OF_WEEK,
    is_early_am,
    is_evening_pm,
    is_late_pm,
    is_midday,
    is_peak_am,
)
from gtfs.util import (
    bucket_by,
    date_range,
    date_range_contains,
    ensure_dir,
    format_timedelta,
    listify,
)


@dataclass(frozen=True)
class DaySummary(object):
    line_id: str
    route_id: str
    trips: List[TripSummary]

    def _filter_and_count_trips(self, predicate):
        return len(list(filter(predicate, self.trips)))

    @cached_property
    def all_trips(self):
        return self._filter_and_count_trips(lambda t: True)

    @cached_property
    def early_am_trips(self):
        return self._filter_trips(lambda trip: is_early_am(trip.stop_times[-1].time))

    @cached_property
    def peak_am_trips(self):
        return self._filter_trips(lambda trip: is_peak_am(trip.stop_times[-1].time))

    @cached_property
    def midday_trips(self):
        return self._filter_trips(
            lambda trip: is_midday(trip.stop_times[0].time)
            or is_midday(trip.stop_times[-1].time)
        )

    @cached_property
    def evening_pm_trips(self):
        return self._filter_trips(lambda trip: is_evening_pm(trip.stop_times[0].time))

    @cached_property
    def late_pm_trips(self):
        return self._filter_trips(lambda trip: is_late_pm(trip.stop_times[0].time))


@dataclass
class TripOnDate(object):
    trip: TripSummary
    date: date


def get_all_feeds_for_dates(from_date: date, to_date: date):
    return list(
        reversed(
            [
                feed
                for (_, feed) in load_feeds_and_summaries_from_archive(
                    from_date, to_date
                )
            ]
        )
    )


def service_runs_on_date(service: Service, date: date):
    is_in_service_range = service.start_date <= date <= service.end_date
    service_runs_on_day_of_week = DAYS_OF_WEEK[date.weekday()] in service.days
    service_is_removed_by_exception = any(
        (
            ed.date == date and ed.exception_type == ServiceExceptionType.REMOVED
            for ed in service.exception_dates
        )
    )
    service_is_added_by_exception = any(
        (
            ed.date == date and ed.exception_type == ServiceExceptionType.ADDED
            for ed in service.exception_dates
        )
    )
    return service_is_added_by_exception or (
        is_in_service_range
        and service_runs_on_day_of_week
        and not service_is_removed_by_exception
    )


def get_feed_for_date(today: date, chron_feeds: List[FeedSummary]):
    for feed in reversed(chron_feeds):
        if date_range_contains(
            (feed.feed_info.start_date, feed.feed_info.end_date),
            today,
        ):
            return feed


@listify
def get_trips_on_date(today: date, chron_feeds: List[FeedSummary]):
    feed_for_date = get_feed_for_date(today, chron_feeds)
    for trip in feed_for_date.trips:
        if service_runs_on_date(trip.service, today):
            yield TripOnDate(trip=trip, date=today)


def get_trips_for_date_range(
    from_date: date,
    to_date: date,
    chron_feeds: List[FeedSummary],
):
    all_trips_by_route_id = defaultdict(list)
    day_summaries = defaultdict(list)
    for today in date_range(from_date, to_date):
        all_trips_for_date = sorted(
            get_trips_on_date(today, chron_feeds),
            key=lambda tod: tod.trip.stop_times[0].time,
        )
        trip_buckets = bucket_by(all_trips_for_date, lambda tod: tod.trip.route_id)
        for (route_id, trips) in trip_buckets.items():
            all_trips_by_route_id[route_id] += trips
            day_summary = DaySummary(
                line_id=trips[0].trip.line.id,
                route_id=route_id,
                trips=[t.trip for t in trips],
            )
            day_summaries[today].append(day_summary)
    return all_trips_by_route_id, day_summaries


def write_trips_csv_for_route_id(route_id: str, trips_on_date: List[TripOnDate]):
    ensure_dir(path.join(OUTPUT_PATH, "lines"))
    csv_path = path.join(OUTPUT_PATH, "lines", f"{route_id}.csv")
    with open(csv_path, "w") as csv_file:
        writer = DictWriter(
            csv_file,
            fieldnames=[
                "date",
                "time",
                "trip_id",
                "line_id",
                "route_id",
                "route_pattern_id",
                "route_name",
                "route_pattern_name",
                "service_id",
                "service_typicality",
                "direction",
                "from_station",
                "to_station",
            ],
        )
        writer.writeheader()
        for trip_on_date in trips_on_date:
            trip = trip_on_date.trip
            date = trip_on_date.date
            writer.writerow(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "time": format_timedelta(trip.stop_times[0].time),
                    "trip_id": trip.id,
                    "line_id": trip.line.id,
                    "route_id": trip.route_id,
                    "route_pattern_id": trip.route_pattern_id,
                    "route_name": trip.route_name,
                    "route_pattern_name": trip.route_pattern_name,
                    "service_id": trip.service.id,
                    "service_typicality": trip.service.schedule_typicality,
                    "direction": trip.direction,
                    "from_station": trip.stop_times[0].station_name,
                    "to_station": trip.stop_times[-1].station_name,
                }
            )


def write_summary_csv(trips_by_date: Dict[date, List[DaySummary]]):
    csv_path = path.join(OUTPUT_PATH, "summary.csv")
    for (date, day_summaries) in trips_by_date.items():
        for day_summary in day_summaries:
            print(date, day_summary.route_id, day_summary.all_trips)


def main():
    ensure_dir(OUTPUT_PATH)
    feeds = get_all_feeds_for_dates(EARLIEST_DATE, LATEST_DATE)
    trips_by_route_id, day_summaries = get_trips_for_date_range(
        EARLIEST_DATE,
        LATEST_DATE,
        feeds,
    )
    write_summary_csv(day_summaries)
    for (route_id, trips_for_route) in trips_by_route_id.items():
        write_trips_csv_for_route_id(route_id, trips_for_route)


if __name__ == "__main__":
    main()
