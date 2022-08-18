from datetime import date
from os import path

EARLIEST_DATE = date(2019, 10, 3)
LATEST_DATE = date(2022, 8, 10)

IGNORE_LINE_IDS = ["line-CapeFlyer", "line-Foxboro"]

GTFS_ARCHIVE_URL = "https://cdn.mbta.com/archive/archived_feeds.txt"

GTFS_DATA_PATH = path.join(path.dirname(__file__), "..", "archives")
OUTPUT_PATH = path.join(path.dirname(__file__), "..", "output")
