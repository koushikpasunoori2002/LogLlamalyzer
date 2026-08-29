"""
Tests for synchronization configuration.
"""

from pathlib import Path

from backend.synchronization.config.synchronization_config import (
    SynchronizationConfig,
)
from backend.synchronization.models.log_source import LogSource


def test_configuration_supports_multiple_sources():

    source_a = LogSource(
        source_id="server-a",
        hostname="server-a",
        log_paths=[
            Path("/var/log/auth.log"),
        ],
    )

    source_b = LogSource(
        source_id="server-b",
        hostname="server-b",
        log_paths=[
            Path("/var/log/syslog"),
        ],
    )

    config = SynchronizationConfig()

    config.add_source(source_a)
    config.add_source(source_b)

    assert len(config.sources) == 2
    assert config.get_source("server-a") == source_a
    assert config.get_source("server-b") == source_b


def test_configuration_serialization():

    source = LogSource(
        source_id="server-a",
        hostname="server-a",
        log_paths=[
            Path("/var/log/auth.log"),
        ],
    )

    config = SynchronizationConfig(
        sources=[source],
        sync_interval=60,
        destination="data/synchronized",
    )

    data = config.to_dict()

    assert data["sync_interval"] == 60
    assert data["destination"] == "data/synchronized"

    assert data["sources"][0]["source_id"] == "server-a"
def test_configuration_from_dict():

    data = {
        "sync_interval": 60,
        "destination": "data/synchronized",
        "sources": [
            {
                "source_id": "server-a",
                "hostname": "server-a",
                "log_paths": [
                    "/var/log/auth.log",
                ],
            },
            {
                "source_id": "server-b",
                "hostname": "server-b",
                "log_paths": [
                    "/var/log/syslog",
                ],
            },
        ],
    }

    config = SynchronizationConfig.from_dict(data)

    assert len(config.sources) == 2

    assert config.sources[0].source_id == "server-a"
    assert config.sources[1].source_id == "server-b"

    assert config.sync_interval == 60
    assert config.destination == "data/synchronized"


def test_configuration_from_file(tmp_path):

    config_file = tmp_path / "synchronization.json"

    config_file.write_text(
        """
        {
            "sync_interval": 30,
            "destination": "data/synchronized",
            "sources": [
                {
                    "source_id": "server-a",
                    "hostname": "server-a",
                    "log_paths": [
                        "/var/log/auth.log"
                    ]
                }
            ]
        }
        """,
        encoding="utf-8",
    )

    config = SynchronizationConfig.from_file(
        config_file
    )

    assert len(config.sources) == 1
    assert config.sources[0].source_id == "server-a"
    assert config.sync_interval == 30