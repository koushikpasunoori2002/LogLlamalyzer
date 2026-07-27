"""
gzip_reader.py

Reads compressed (.gz) log files.
"""

import gzip
from pathlib import Path


class GzipReader:
    """
    Reads gzip compressed log files.
    """

    def __init__(self, encoding="utf-8", errors="ignore"):

        self.encoding = encoding

        self.errors = errors

    # ------------------------------------------------------------------
    # Read Entire File
    # ------------------------------------------------------------------

    def read(self, file_path):
        """
        Reads the entire compressed file and returns it as a string.
        """

        file_path = Path(file_path)

        if not file_path.exists():

            raise FileNotFoundError(
                f"{file_path} does not exist."
            )

        if file_path.suffix != ".gz":

            raise ValueError(
                f"{file_path} is not a gzip (.gz) file."
            )

        with gzip.open(
            file_path,
            mode="rt",
            encoding=self.encoding,
            errors=self.errors,
        ) as file:

            return file.read()

    # ------------------------------------------------------------------
    # Read Line By Line
    # ------------------------------------------------------------------

    def read_lines(self, file_path):
        """
        Reads the compressed file and returns a list of lines.
        """

        file_path = Path(file_path)

        if not file_path.exists():

            raise FileNotFoundError(
                f"{file_path} does not exist."
            )

        if file_path.suffix != ".gz":

            raise ValueError(
                f"{file_path} is not a gzip (.gz) file."
            )

        with gzip.open(
            file_path,
            mode="rt",
            encoding=self.encoding,
            errors=self.errors,
        ) as file:

            return file.readlines()

    # ------------------------------------------------------------------
    # Reader Information
    # ------------------------------------------------------------------

    def info(self):
        """
        Returns reader metadata.
        """

        return {

            "reader": "GzipReader",

            "version": "1.0",

            "supports": [

                ".gz",

            ],

            "mode": "text",

        }