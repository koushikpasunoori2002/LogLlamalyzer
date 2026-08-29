"""
synchronization_config.py

Configuration model for multi-source log synchronization.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from ..models.log_source import LogSource


@dataclass
class SynchronizationConfig:
    """
    Stores configuration for multiple log sources.

    The number of sources is determined by configuration and
    is not restricted by the synchronization implementation.
    """

    sources: List[LogSource] = field(default_factory=list)

    sync_interval: int = 60

    destination: str = "data/synchronized"

    def add_source(self, source: LogSource):
        """
        Add a log source to the configuration.
        """

        if not isinstance(source, LogSource):
            raise TypeError(
                "source must be a LogSource instance."
            )

        self.sources.append(source)

    def get_source(self, source_id: str):
        """
        Retrieve a source by its identifier.
        """

        for source in self.sources:

            if source.source_id == source_id:
                return source

        return None

    @classmethod
    def from_dict(cls, data):
        """
        Create a SynchronizationConfig from a dictionary.
        """

        sources = [
            LogSource(
                source_id=source["source_id"],
                hostname=source["hostname"],
                log_paths=source.get("log_paths", []),
            )
            for source in data.get("sources", [])
        ]

        return cls(
            sources=sources,
            sync_interval=data.get(
                "sync_interval",
                60,
            ),
            destination=data.get(
                "destination",
                "data/synchronized",
            ),
        )

    @classmethod
    def from_file(cls, config_path):
        """
        Load synchronization configuration from JSON.
        """

        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}"
            )

        with config_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        return cls.from_dict(data)

    def to_dict(self):
        """
        Convert configuration into a serializable dictionary.
        """

        return {
            "sources": [
                source.to_dict()
                for source in self.sources
            ],
            "sync_interval": self.sync_interval,
            "destination": self.destination,
        }

    def info(self):
        """
        Return configuration metadata.
        """

        return {
            "component": "SynchronizationConfig",
            "source_count": len(self.sources),
            "sync_interval": self.sync_interval,
            "destination": self.destination,
        }