"""
Tests for RsyncSynchronizer.
"""

from pathlib import Path

from backend.synchronization.models.log_source import LogSource
from backend.synchronization.rsync.rsync_synchronizer import (
    RsyncSynchronizer,
)


def test_build_command():

    source = LogSource(
        source_id="server-a",
        hostname="server-a",
        log_paths=[
            Path("/var/log/auth.log"),
        ],
    )

    synchronizer = RsyncSynchronizer(
        destination="data/synchronized"
    )

    command = synchronizer.build_command(
        source,
        source.log_paths[0],
    )

    assert command[0] == "rsync"
    assert "-av" in command
    assert "--partial" in command
    assert "server-a:/var/log/auth.log" in command


def test_multiple_sources_generate_independent_destinations():

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

    synchronizer = RsyncSynchronizer(
        destination="data/synchronized"
    )

    command_a = synchronizer.build_command(
        source_a,
        source_a.log_paths[0],
    )

    command_b = synchronizer.build_command(
        source_b,
        source_b.log_paths[0],
    )

    assert "server-a:/var/log/auth.log" in command_a
    assert "server-b:/var/log/syslog" in command_b

    assert command_a[-1].endswith(
        "data\\synchronized\\server-a"
    )

    assert command_b[-1].endswith(
        "data\\synchronized\\server-b"
    )