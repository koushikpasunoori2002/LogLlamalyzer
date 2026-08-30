"""
Tests for SynchronizedRAGApplication.
"""

from pathlib import Path

import pytest

from backend.synchronization.application.synchronized_rag_application import (
    SynchronizedRAGApplication,
)

from backend.synchronization.config.synchronization_config import (
    SynchronizationConfig,
)

from backend.synchronization.models.log_source import LogSource


class FakeRAGRunner:
    """
    Fake combined runner used to isolate the application
    from synchronization, preprocessing, RAG, and ChromaDB.
    """

    def __init__(self):
        self.calls = []
        self.vector_count = 0

    def run_once(self):
        self.calls.append("run_once")

        return {
            "server-a": [
                "chunk:server-a:0",
                "chunk:server-a:1",
            ],
            "server-b": [
                "chunk:server-b:0",
            ],
        }

    def count(self):
        self.calls.append("count")

        return self.vector_count

    def info(self):
        self.calls.append("info")

        return {
            "component": "FakeRAGRunner",
        }

    def close(self):
        self.calls.append("close")


def create_config(tmp_path):
    """
    Create a test synchronization configuration.
    """

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
        destination=str(
            tmp_path / "synchronized"
        ),
    )


def test_application_accepts_valid_configuration(
    tmp_path,
):
    """
    Verify that the application accepts a
    SynchronizationConfig instance.
    """

    config = create_config(tmp_path)

    runner = FakeRAGRunner()

    application = SynchronizedRAGApplication(
        config=config,
        rag_runner=runner,
    )

    assert application.config is config
    assert application.rag_runner is runner


def test_application_rejects_invalid_configuration(
    tmp_path,
):
    """
    Verify that invalid configuration objects
    are rejected.
    """

    runner = FakeRAGRunner()

    with pytest.raises(TypeError):

        SynchronizedRAGApplication(
            config="invalid-config",
            rag_runner=runner,
        )


def test_run_once_delegates_to_rag_runner(
    tmp_path,
):
    """
    Verify that run_once delegates to the
    combined RAG runner.
    """

    config = create_config(tmp_path)

    runner = FakeRAGRunner()

    application = SynchronizedRAGApplication(
        config=config,
        rag_runner=runner,
    )

    result = application.run_once()

    assert result == {
        "server-a": [
            "chunk:server-a:0",
            "chunk:server-a:1",
        ],
        "server-b": [
            "chunk:server-b:0",
        ],
    }

    assert runner.calls == [
        "run_once",
    ]


def test_count_delegates_to_rag_runner(
    tmp_path,
):
    """
    Verify that count exposes the RAG vector count.
    """

    config = create_config(tmp_path)

    runner = FakeRAGRunner()

    runner.vector_count = 3

    application = SynchronizedRAGApplication(
        config=config,
        rag_runner=runner,
    )

    assert application.count() == 3

    assert runner.calls == [
        "count",
    ]


def test_info_returns_application_metadata(
    tmp_path,
):
    """
    Verify that application information contains
    configuration and runner information.
    """

    config = create_config(tmp_path)

    runner = FakeRAGRunner()

    application = SynchronizedRAGApplication(
        config=config,
        rag_runner=runner,
    )

    info = application.info()

    assert info["component"] == (
        "SynchronizedRAGApplication"
    )

    assert info["configuration"]["component"] == (
        "SynchronizationConfig"
    )

    assert info["configuration"]["source_count"] == 2

    assert info["configuration"]["sync_interval"] == 60

    assert info["runner"]["component"] == (
        "FakeRAGRunner"
    )

    assert info["vector_count"] == 0


def test_close_delegates_to_rag_runner(
    tmp_path,
):
    """
    Verify that closing the application delegates
    resource cleanup to the RAG runner.
    """

    config = create_config(tmp_path)

    runner = FakeRAGRunner()

    application = SynchronizedRAGApplication(
        config=config,
        rag_runner=runner,
    )

    application.close()

    assert runner.calls == [
        "close",
    ]


def test_from_file_loads_configuration(
    tmp_path,
):
    """
    Verify that the application can be constructed
    from a JSON synchronization configuration.
    """

    config_file = (
        tmp_path
        / "synchronization.json"
    )

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
                },
                {
                    "source_id": "server-b",
                    "hostname": "server-b",
                    "log_paths": [
                        "/var/log/syslog"
                    ]
                }
            ]
        }
        """,
        encoding="utf-8",
    )

    application = (
        SynchronizedRAGApplication.from_file(
            config_file
        )
    )

    assert isinstance(
        application.config,
        SynchronizationConfig,
    )

    assert len(
        application.config.sources
    ) == 2

    assert (
        application.config.sources[0].source_id
        == "server-a"
    )

    assert (
        application.config.sources[1].source_id
        == "server-b"
    )

    assert (
        application.config.sync_interval
        == 30
    )

    assert (
        application.config.destination
        == "data/synchronized"
    )

    application.close()


def test_application_repr(
    tmp_path,
):
    """
    Verify the application representation.
    """

    config = create_config(tmp_path)

    runner = FakeRAGRunner()

    runner.vector_count = 5

    application = SynchronizedRAGApplication(
        config=config,
        rag_runner=runner,
    )

    assert repr(application) == (
        "SynchronizedRAGApplication("
        "vectors=5)"
    )