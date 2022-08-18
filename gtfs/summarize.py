from dataclasses import dataclass
import datetime
from typing import List

from gtfs.models import Network, Service, Line, FeedInfo
from gtfs.util import listify


@dataclass
class StopTime:
    stop_id: str
    station_id: str
    station_name: str
    time: datetime.timedelta


@dataclass
class TripSummary:
    id: str
    route_id: str
    route_name: str
    route_pattern_id: str
    route_pattern_name: str
    direction: int
    service: Service
    line: Line
    stop_times: List[StopTime]


@dataclass
class FeedSummary:
    feed_info: FeedInfo
    trips: List[TripSummary]


@listify
def get_cr_trip_summaries_for_network(network: Network):
    for trip in network.trips_by_id.values():
        if trip.route_id.startswith("CR-"):
            route = network.routes_by_id[trip.route_id]
            route_pattern = next((rp for rp in route.route_patterns if rp.id == trip.route_pattern_id))
            yield TripSummary(
                id=trip.id,
                route_id=route.id,
                route_name=route.long_name,
                route_pattern_id=route_pattern.id,
                route_pattern_name=route_pattern.name,
                direction=route_pattern.direction,
                service=trip.service,
                line=network.routes_by_id[trip.route_id].line,
                stop_times=[
                    StopTime(
                        stop_id=st.stop.id,
                        station_id=st.stop.parent_station.id,
                        station_name=st.stop.parent_station.name,
                        time=st.time,
                    )
                    for st in trip.stop_times
                ],
            )


def get_feed_summary_for_network(network: Network):
    return FeedSummary(
        trips=get_cr_trip_summaries_for_network(network),
        feed_info=network.feed_info,
    )
