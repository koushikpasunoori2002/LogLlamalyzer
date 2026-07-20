"""
file_info.py

Stores metadata about a log file.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileInfo:
    path: Path
    filename: str
    log_type: str
    compressed: bool
    rotation: int
    extension: str
    reader: str

    def __str__(self):
        return (
            f"\nFilename    : {self.filename}"
            f"\nType        : {self.log_type}"
            f"\nCompressed  : {self.compressed}"
            f"\nRotation    : {self.rotation}"
            f"\nExtension   : {self.extension}"
            f"\nReader      : {self.reader}"
        )