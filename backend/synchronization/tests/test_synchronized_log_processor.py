"""
Tests for synchronized log processing.
"""

from pathlib import Path

from backend.synchronization.config.synchronization_config import (
    SynchronizationConfig,
)
from backend.synchronization.models.log_source import LogSource
from backend.synchronization.processor.synchronized_log_processor import (
    SynchronizedLogProcessor,
)


class FakePipeline:
    """
    Fake preprocessing pipeline used to isolate
    synchronized log processing from the real parser system.
    """

    def __init__(self):
        self.calls = []

    def process(self, file_path):
        self.calls.append(
            Path(file_path)
        )

        return [
            f"record:{Path(file_path).name}"
        ]


def create_config(tmp_path):

    return SynchronizationConfig(
        sources=[
            LogSource(
                source_id="server-a",
                hostname="server-a",
                log_paths=[
                    Path("/var/log/auth.log"),
                ],
            ),
            LogSource(
                source_id="server-b",
                hostname="server-b",
                log_paths=[
                    Path("/var/log/syslog"),
                ],
            ),
        ],
        sync_interval=60,
        destination=str(
            tmp_path / "synchronized"
        ),
    )


def test_discover_files_for_source(tmp_path):

    config = create_config(tmp_path)

    source_directory = (
        tmp_path
        / "synchronized"
        / "server-a"
    )

    source_directory.mkdir(
        parents=True
    )

    auth_file = (
        source_directory
        / "auth.log"
    )

    syslog_file = (
        source_directory
        / "syslog"
    )

    auth_file.write_text(
        "test auth log",
        encoding="utf-8",
    )

    syslog_file.write_text(
        "test syslog",
        encoding="utf-8",
    )

    pipeline = FakePipeline()

    processor = SynchronizedLogProcessor(
        config=config,
        pipeline=pipeline,
    )

    files = processor.discover_files(
        config.sources[0]
    )

    assert set(files) == {
        auth_file,
        syslog_file,
    }


def test_process_source_processes_all_files(tmp_path):

    config = create_config(tmp_path)

    source_directory = (
        tmp_path
        / "synchronized"
        / "server-a"
    )

    source_directory.mkdir(
        parents=True
    )

    auth_file = (
        source_directory
        / "auth.log"
    )

    syslog_file = (
        source_directory
        / "syslog"
    )

    auth_file.write_text(
        "auth",
        encoding="utf-8",
    )

    syslog_file.write_text(
        "syslog",
        encoding="utf-8",
    )

    pipeline = FakePipeline()

    processor = SynchronizedLogProcessor(
        config=config,
        pipeline=pipeline,
    )

    records = processor.process_source(
        config.sources[0]
    )

    assert len(pipeline.calls) == 2

    assert set(pipeline.calls) == {
        auth_file,
        syslog_file,
    }

    assert set(records) == {
        "record:auth.log",
        "record:syslog",
    }


def test_process_all_keeps_sources_separate(tmp_path):

    config = create_config(tmp_path)

    server_a_directory = (
        tmp_path
        / "synchronized"
        / "server-a"
    )

    server_b_directory = (
        tmp_path
        / "synchronized"
        / "server-b"
    )

    server_a_directory.mkdir(
        parents=True
    )

    server_b_directory.mkdir(
        parents=True
    )

    server_a_file = (
        server_a_directory
        / "auth.log"
    )

    server_b_file = (
        server_b_directory
        / "syslog"
    )

    server_a_file.write_text(
        "server a",
        encoding="utf-8",
    )

    server_b_file.write_text(
        "server b",
        encoding="utf-8",
    )

    pipeline = FakePipeline()

    processor = SynchronizedLogProcessor(
        config=config,
        pipeline=pipeline,
    )

    results = processor.process_all()

    assert set(results.keys()) == {
        "server-a",
        "server-b",
    }

    assert results["server-a"] == [
        "record:auth.log"
    ]

    assert results["server-b"] == [
        "record:syslog"
    ]


def test_missing_source_directory_returns_empty_list(tmp_path):

    config = create_config(tmp_path)

    pipeline = FakePipeline()

    processor = SynchronizedLogProcessor(
        config=config,
        pipeline=pipeline,
    )

    files = processor.discover_files(
        config.sources[0]
    )

    assert files == []

    records = processor.process_source(
        config.sources[0]
    )

    assert records == []

    assert pipeline.calls == []


def test_processor_info(tmp_path):

    config = create_config(tmp_path)

    processor = SynchronizedLogProcessor(
        config=config,
        pipeline=FakePipeline(),
    )

    info = processor.info()

    assert info["component"] == (
        "SynchronizedLogProcessor"
    )

    assert info["source_count"] == 2

    assert info["destination"] == str(
        tmp_path / "synchronized"
    )