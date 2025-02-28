__all__ = [
	'filter_filepaths_by_dates',
	'get_filepaths'
]

import math
import platform
import re
from pathlib import Path, PurePath

import pendulum

from .decorators import cast_to_list


@cast_to_list(0)
def filter_filepaths_by_dates(
	filepaths,
	*,
	created_in=None,
	created_on=None,
	created_before=None,
	created_after=None,
	modified_in=None,
	modified_on=None,
	modified_before=None,
	modified_after=None
):
	def _match_created_date(filepaths, period):
		for filepath in filepaths:
			file_stat = filepath.stat()

			if platform.system() == 'Windows':
				created_timestamp = file_stat.st_ctime
			else:
				try:
					created_timestamp = file_stat.st_birthtime
				except AttributeError:
					# Settle for modified time on *nix systems
					# not supporting birth time.
					created_timestamp = file_stat.st_mtime

			if pendulum.from_timestamp(created_timestamp) in period:
				yield filepath

	def _match_modified_date(filepaths, period):
		for filepath in filepaths:
			modified_timestamp = filepath.stat().st_mtime

			if pendulum.from_timestamp(modified_timestamp) in period:
				yield filepath

	for period in [
		created_in,
		created_on,
		created_before,
		created_after,
	]:
		if period is not None:
			filepaths = _match_created_date(filepaths, period)

	for period in [
		modified_in,
		modified_on,
		modified_before,
		modified_after,
	]:
		if period is not None:
			filepaths = _match_modified_date(filepaths, period)

	return filepaths


@cast_to_list(0)
def get_filepaths(
	paths,
	*,
	max_depth=math.inf,
	exclude_paths=None,
	exclude_regexes=None,
	exclude_globs=None
):
	exclude_paths = exclude_paths or []
	exclude_regexes = exclude_regexes or []
	exclude_globs = exclude_globs or []

	def _exclude_paths(path, exclude_paths):
		return any(
			str(PurePath(exclude_path)) in str(path)
			for exclude_path in exclude_paths
		)

	def _exclude_regexes(path, exclude_regexes):
		return any(
			re.search(regex, str(path.resolve()))
			for regex in exclude_regexes
		)

	for path in paths:
		path = Path(path).resolve()

		if path.is_dir():
			dirpath = path
			start_level = len(dirpath.parts)

			exclude_files = set()
			for exclude_glob in exclude_globs:
				exclude_files |= set(path.rglob(exclude_glob))

			for path in dirpath.glob('**/*'):
				if (
					path.is_file()
					and len(path.parent.parts) - start_level <= max_depth
					and path not in exclude_files
					and not _exclude_paths(path, exclude_paths)
					and not _exclude_regexes(path, exclude_regexes)
				):
					yield path
		else:
			if (
				path.is_file()
				and not _exclude_paths(path, exclude_paths)
				and not _exclude_regexes(path, exclude_regexes)
			):
				yield path
