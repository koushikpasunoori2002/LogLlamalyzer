"""
log_source.py

Defines a generic source of log files for synchronization.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class LogSource:
    """
    Represents a configurable source of log files.

    A source can represent a local machine, remote machine,
    server, or any other system whose logs are accessible
    to LogLlamalyzer.
    """

    source_id: str
    hostname: str
    log_paths: List[Path] = field(default_factory=list)

    def __post_init__(self):
        """
        Normalize configured paths.
        """

        self.log_paths = [
            Path(path)
            for path in self.log_paths
        ]

    def to_dict(self):
        """
        Convert the source into a serializable dictionary.

        Source paths are serialized using POSIX-style separators
        so that Linux paths remain portable when LogLlamalyzer
        is running on Windows.
        """

        return {
            "source_id": self.source_id,
            "hostname": self.hostname,
            "log_paths": [
                path.as_posix()
                for path in self.log_paths
            ],
        }

    def __str__(self):
        return (
            f"LogSource("
            f"source_id='{self.source_id}', "
            f"hostname='{self.hostname}', "
            f"log_paths={len(self.log_paths)}"
            f")"
        )