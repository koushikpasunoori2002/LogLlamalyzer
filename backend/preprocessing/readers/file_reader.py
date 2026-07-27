"""
file_reader.py

Reads plain text log files (.log, .1, etc.).
"""

from pathlib import Path


class FileReader:
    """
    Reads normal text log files.
    """

    def __init__(self, encoding="utf-8", errors="ignore"):

        self.encoding = encoding

        self.errors = errors

    # ------------------------------------------------------------------
    # Read Entire File
    # ------------------------------------------------------------------

    def read(self, file_path):
        """
        Reads the entire text log file and returns it as a string.
        """

        file_path = Path(file_path)

        if not file_path.exists():

            raise FileNotFoundError(
                f"{file_path} does not exist."
            )

        if file_path.suffix == ".gz":

            raise ValueError(
                f"{file_path} is a gzip file. Use GzipReader instead."
            )

        with file_path.open(
            mode="r",
            encoding=self.encoding,
            errors=self.errors,
        ) as file:

            return file.read()

    # ------------------------------------------------------------------
    # Read Line By Line
    # ------------------------------------------------------------------

    def read_lines(self, file_path):
        """
        Reads the text log file and returns a list of lines.
        """

        file_path = Path(file_path)

        if not file_path.exists():

            raise FileNotFoundError(
                f"{file_path} does not exist."
            )

        if file_path.suffix == ".gz":

            raise ValueError(
                f"{file_path} is a gzip file. Use GzipReader instead."
            )

        with file_path.open(
            mode="r",
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

            "reader": "FileReader",

            "version": "1.0",

            "supports": [

                ".log",
                ".txt",
                ".1",
                ".2",
                ".3",
                ".4",

            ],

            "mode": "text",

        }