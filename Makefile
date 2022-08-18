.PHONY: download-data

download-data:
	poetry run python3 -m gtfs.archive

make output:
	poetry run python3 -m generate