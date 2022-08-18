import datetime

PEAK_AM_START = datetime.timedelta(hours=7)
PEAK_AM_END = datetime.timedelta(hours=10)
PEAK_PM_START = datetime.timedelta(hours=16)
PEAK_PM_END = datetime.timedelta(hours=19)
LATE_PM_START = datetime.timedelta(hours=22)


def date_from_string(date_str):
    return datetime.datetime.strptime(date_str, "%Y%m%d").date()


def date_to_string(date):
    return date.strftime("%Y%m%d")


def time_from_string(time_string):
    pieces = [int(x) for x in time_string.split(":")]
    if len(pieces) == 3:
        hours, minutes, seconds = pieces
        return datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
    hours, minutes = pieces
    return datetime.timedelta(hours=hours, minutes=minutes)


def time_range_from_string(time_string):
    pieces = time_string.split("-")
    assert len(pieces) == 2
    return tuple(time_from_string(piece.strip()) for piece in pieces)


def stringify_timedelta(td):
    seconds = td.total_seconds()
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return "{:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds))


def is_early_am(td: datetime.timedelta):
    return td <= PEAK_AM_START


def is_peak_am(td: datetime.timedelta):
    return PEAK_AM_START < td <= PEAK_AM_END


def is_midday(td: datetime.timedelta):
    return PEAK_AM_END < td < PEAK_PM_START


def is_peak_pm(td: datetime.timedelta):
    return PEAK_PM_START <= td <= PEAK_PM_END


def is_evening_pm(td: datetime.timedelta):
    return PEAK_PM_END < td < LATE_PM_START


def is_late_pm(td: datetime.timedelta):
    return td >= LATE_PM_START


DAYS_OF_WEEK = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]
