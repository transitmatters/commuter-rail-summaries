from csv import DictReader
from dataclasses import dataclass
from datetime import date
from functools import cached_property
from os import path, mkdir
from zipfile import BadZipFile, ZipFile
import pickle

import requests
from tqdm import tqdm

from gtfs.config import GTFS_ARCHIVE_URL, GTFS_DATA_PATH, EARLIEST_DATE
from gtfs.loader import GtfsLoader
from gtfs.network import build_network_from_gtfs
from gtfs.summarize import get_feed_summary_for_network
from gtfs.time import date_from_string, date_to_string
from gtfs.util import ensure_dir


@dataclass
class GtfsFeed:
    start_date: date
    end_date: date
    url: str
    version: str

    @cached_property
    def subdirectory(self):
        return path.join(GTFS_DATA_PATH, date_to_string(self.start_date))

    def child_by_name(self, filename):
        return path.join(self.subdirectory, filename)

    @cached_property
    def gtfs_zip_path(self):
        return self.child_by_name("data.zip")

    @cached_property
    def gtfs_subdir_path(self):
        return self.child_by_name("feed")

    @cached_property
    def feed_pickle_path(self):
        return self.child_by_name("feed.pickle")

    @cached_property
    def service_levels_json_path(self):
        return self.child_by_name("service_levels.json")

    @cached_property
    def loader(self):
        return GtfsLoader(root=self.gtfs_subdir_path)


def download_gtfs_zip(feed: GtfsFeed):
    target_file = feed.gtfs_zip_path
    if path.exists(target_file):
        return
    ensure_dir(feed.subdirectory)
    response = requests.get(feed.url, stream=True)
    total_size_in_bytes = int(response.headers.get("content-length", 0))
    block_size = 1024
    progress_bar = tqdm(
        total=total_size_in_bytes,
        unit="iB",
        unit_scale=True,
        desc=f"Downloading {feed.url}",
    )
    with open(target_file, "wb") as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    progress_bar.close()


def extract_gtfs_zip(feed: GtfsFeed):
    if path.exists(feed.gtfs_subdir_path):
        return
    download_gtfs_zip(feed)
    print(f"Extracting {feed.url} to {feed.gtfs_subdir_path}")
    try:
        zf = ZipFile(feed.gtfs_zip_path)
        zf.extractall(feed.gtfs_subdir_path)
    except BadZipFile:
        print(feed.gtfs_zip_path)


def get_feed_summary(feed: GtfsFeed):
    pickle_path = feed.feed_pickle_path
    if path.exists(pickle_path):
        with open(pickle_path, "rb") as file:
            try:
                return pickle.load(file)
            except Exception:
                print("Error loading pickled feed summary")
    extract_gtfs_zip(feed)
    print("Creating network from scratch...")
    network = build_network_from_gtfs(feed.loader)
    feed_summary = get_feed_summary_for_network(network)
    print(feed_summary.feed_info, len(feed_summary.trips))
    with open(pickle_path, "wb") as file:
        pickle.dump(feed_summary, file)
    return feed_summary


def load_feeds_from_archive(load_start_date: date, load_end_date: date = date.today()):
    feeds = []
    req = requests.get(GTFS_ARCHIVE_URL)
    lines = req.text.splitlines()
    reader = DictReader(lines, delimiter=",")
    for entry in reader:
        start_date = date_from_string(entry["feed_start_date"])
        end_date = date_from_string(entry["feed_end_date"])
        version = entry["feed_version"]
        url = entry["archive_url"]
        if start_date < load_start_date or start_date > load_end_date:
            continue
        gtfs_feed = GtfsFeed(
            start_date=start_date,
            end_date=end_date,
            version=version,
            url=url,
        )
        feeds.append(gtfs_feed)
    return feeds


def load_feeds_and_summaries_from_archive(load_start_date: date, load_end_date: date):
    for feed in load_feeds_from_archive(load_start_date, load_end_date):
        yield feed, get_feed_summary(feed)


if __name__ == "__main__":
    ensure_dir(GTFS_DATA_PATH)
    for _ in load_feeds_and_summaries_from_archive(EARLIEST_DATE):
        pass
