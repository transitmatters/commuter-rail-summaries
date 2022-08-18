# commuter-rail-summaries

This repo does some analysis of MBTA Commuter Rail schedules from GTFS. You'll
need Python 3.8 or above and [Poetry](https://python-poetry.org/) for dependency
management. To run the analysis:

```
poetry install
make output
```

The `archives/` directory is pre-populated with Python `.pickle` files
containing a summary of Commuter Rail trips from each GTFS archive found here:
https://cdn.mbta.com/archive/archived_feeds.txt. If you want, you can change
`START_DATE` and `END_DATE` in `config.py` and then run:

```
make download-data
make output
```

to run the analysis on a wider range of dates.
