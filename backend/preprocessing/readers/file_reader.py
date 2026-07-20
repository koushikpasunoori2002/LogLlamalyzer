"""
file_reader.py

Reads plain text log files (.log, .1, etc.)
"""

from pathlib import Path


class FileReader:
    """Reads normal text log files."""

    def __init__(self, encoding="utf-8"):
        self.encoding = encoding

    def read(self, file_path):
        """
        Read an entire text log file.

        Args:
            file_path (str | Path)

        Returns:
            str
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"{file_path} does not exist.")

        with file_path.open("r", encoding=self.encoding, errors="ignore") as file:
            return file.read()

    def read_lines(self, file_path):
        """
        Read log file line by line.

        Returns:
            list[str]
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"{file_path} does not exist.")

        with file_path.open("r", encoding=self.encoding, errors="ignore") as file:
            return file.readlines()