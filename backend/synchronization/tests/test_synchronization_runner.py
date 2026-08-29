"""
Tests for the synchronization runner.
"""

from pathlib import Path

from backend.synchronization.config.synchronization_config import (
    SynchronizationConfig,
)
from backend.synchronization.models.log_source import LogSource
from backend.synchronization.runner.synchronization_runner import (
    SynchronizationRunner,
)


class FakeSynchronizer:

    def __init__(self):
        self.calls = []

    def sync_all(self, sources):

        self.calls.append(
            list(sources)
        )

        return {
            source.source_id: []
            for source in sources
        }


def create_config():

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

    return SynchronizationConfig(
        sources=[
            source_a,
            source_b,
        ],
        sync_interval=60,
        destination="data/synchronized",
    )


def test_sync_once_processes_all_sources():

    config = create_config()

    synchronizer = FakeSynchronizer()

    runner = SynchronizationRunner(
        config=config,
        synchronizer=synchronizer,
    )

    result = runner.sync_once()

    assert len(synchronizer.calls) == 1

    assert len(
        synchronizer.calls[0]
    ) == 2

    assert set(result.keys()) == {
        "server-a",
        "server-b",
    }


def test_runner_waits_using_configured_interval():

    config = create_config()

    synchronizer = FakeSynchronizer()

    sleep_calls = []

    def fake_sleep(seconds):

        sleep_calls.append(seconds)

        runner.stop()

    runner = SynchronizationRunner(
        config=config,
        synchronizer=synchronizer,
        sleep_function=fake_sleep,
    )

    runner.run()

    assert sleep_calls == [60]

    assert len(
        synchronizer.calls
    ) == 1


def test_runner_info():

    config = create_config()

    synchronizer = FakeSynchronizer()

    runner = SynchronizationRunner(
        config=config,
        synchronizer=synchronizer,
    )

    info = runner.info()

    assert info["component"] == (
        "SynchronizationRunner"
    )

    assert info["source_count"] == 2

    assert info["sync_interval"] == 60

    assert info["running"] is False