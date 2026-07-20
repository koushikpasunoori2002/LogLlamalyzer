"""
gzip_reader.py

Reads compressed (.gz) log files.
"""

import gzip
from pathlib import Path


class GzipReader:
    """Reads gzip compressed log files."""

    def __init__(self, encoding="utf-8"):
        self.encoding = encoding

    def read(self, file_path):
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"{file_path} does not exist.")

        with gzip.open(file_path, "rt", encoding=self.encoding, errors="ignore") as file:
            return file.read()

    def read_lines(self, file_path):
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"{file_path} does not exist.")

        with gzip.open(file_path, "rt", encoding=self.encoding, errors="ignore") as file:
            return file.readlines()