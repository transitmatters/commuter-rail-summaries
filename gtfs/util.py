from types import GeneratorType
from typing import Tuple, Union
from datetime import date, timedelta
from functools import wraps
from os import mkdir, path


def listify(func):
    @wraps(func)
    def new_func(*args, **kwargs):
        r = func(*args, **kwargs)
        if isinstance(r, GeneratorType):
            return list(r)
        else:
            return r

    return new_func


def index_by(items, key_getter):
    res = {}
    if isinstance(key_getter, str):
        key_getter_as_str = key_getter
        key_getter = lambda dict: dict[key_getter_as_str]
    for item in items:
        res[key_getter(item)] = item
    return res


def bucket_by(items, key_getter):
    res = {}
    if isinstance(key_getter, str):
        key_getter_as_str = key_getter
        key_getter = lambda dict: dict[key_getter_as_str]
    for item in items:
        key = key_getter(item)
        key_items = res.setdefault(key, [])
        key_items.append(item)
    return res


def get_ranges_of_same_value(items_dict):
    current_value = None
    current_keys = None
    sorted_items = sorted(items_dict.items(), key=lambda item: item[0])
    for key, value in sorted_items:
        if value == current_value:
            current_keys.append(key)
        else:
            if current_keys:
                yield current_keys, current_value
            current_keys = [key]
            current_value = value
    if len(current_keys) > 0:
        yield current_keys, current_value


def get_date_ranges_of_same_value(items_dict):
    for dates, value in get_ranges_of_same_value(items_dict):
        min_date = min(dates)
        max_date = max(dates)
        yield (min_date, max_date), value


def date_range_contains(containing: Tuple[date], contained: Union[date, Tuple[date]]):
    (containing_from, containing_to) = containing
    if type(contained) is tuple:
        (contained_from, contained_to) = contained
    else:
        contained_from = contained
        contained_to = contained
    return contained_from >= containing_from and contained_to <= containing_to


def date_range(from_date: date, to_date: date):
    assert from_date < to_date
    today = from_date
    while today <= to_date:
        yield today
        today += timedelta(days=1)


def format_timedelta(td: timedelta):
    seconds = td.total_seconds()
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02n}:{minutes:02n}:{seconds:02n}"


def ensure_dir(dir_path):
    if not path.exists(dir_path):
        mkdir(dir_path)
