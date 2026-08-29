"""
Tests for LogSource.
"""

from pathlib import Path

from backend.synchronization.models.log_source import LogSource


def test_log_source_creation():

    source = LogSource(
        source_id="server-a",
        hostname="server-a",
        log_paths=[
            "/var/log/auth.log",
            "/var/log/syslog",
        ],
    )

    assert source.source_id == "server-a"
    assert source.hostname == "server-a"

    assert source.log_paths == [
        Path("/var/log/auth.log"),
        Path("/var/log/syslog"),
    ]


def test_log_source_serialization():

    source = LogSource(
        source_id="server-a",
        hostname="server-a",
        log_paths=[
            "/var/log/auth.log",
        ],
    )

    data = source.to_dict()

    assert data["source_id"] == "server-a"
    assert data["hostname"] == "server-a"

    assert data["log_paths"] == [
        "/var/log/auth.log",
    ]