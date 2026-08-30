"""
Phase 34 - Multi-server end-to-end integration test.

Validates the complete synchronized multi-source workflow:

Configured Sources
        ↓
Synchronization
        ↓
Synchronized Files
        ↓
Preprocessing
        ↓
LogRecords
        ↓
RAG Ingestion
        ↓
ChromaDB

The test uses temporary local files and mocked rsync execution
so that the test does not require real remote SSH servers.
"""

from pathlib import Path

from backend.synchronization.config.synchronization_config import (
    SynchronizationConfig,
)
from backend.synchronization.models.log_source import LogSource
from backend.synchronization.rsync.rsync_synchronizer import (
    RsyncSynchronizer,
)
from backend.synchronization.runner.synchronization_runner import (
    SynchronizationRunner,
)
from backend.synchronization.processor.synchronized_log_processor import (
    SynchronizedLogProcessor,
)
from backend.synchronization.ingestion.synchronized_log_ingestor import (
    SynchronizedLogIngestor,
)
from backend.synchronization.pipeline.synchronized_rag_pipeline import (
    SynchronizedRAGPipeline,
)
from backend.synchronization.pipeline.synchronized_rag_runner import (
    SynchronizedRAGRunner,
)


class FakeRsyncSynchronizer:
    """
    Fake synchronizer used to simulate two remote servers.

    The actual synchronization architecture remains unchanged.
    Only the network/SSH boundary is replaced for deterministic
    integration testing.
    """

    def __init__(self, destination):
        self.destination = Path(destination)
        self.calls = []

    def sync_all(self, sources):
        results = {}

        for source in sources:
            self.calls.append(source.source_id)

            source_directory = (
                self.destination
                / source.source_id
            )

            source_directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            if source.source_id == "server-a":
                log_file = (
                    source_directory
                    / "auth.log"
                )

                log_file.write_text(
                    "Jan 10 10:00:00 "
                    "server-a sshd[100]: "
                    "Failed password for invalid user admin "
                    "from 192.168.1.10 port 22 ssh2\n",
                    encoding="utf-8",
                )

            elif source.source_id == "server-b":
                log_file = (
                    source_directory
                    / "syslog"
                )

                log_file.write_text(
                    "Jan 10 10:01:00 "
                    "server-b sshd[200]: "
                    "Failed password for invalid user root "
                    "from 192.168.1.20 port 22 ssh2\n",
                    encoding="utf-8",
                )

            results[source.source_id] = True

        return results


class FakeDatabase:
    """
    Lightweight database substitute for the integration test.

    Stores documents and metadata so that source separation
    can be verified without relying on an existing ChromaDB
    collection.
    """

    def __init__(self):
        self.documents = []
        self.metadatas = []

    def add(
        self,
        ids,
        embeddings,
        documents,
        metadatas,
    ):
        self.documents.extend(documents)
        self.metadatas.extend(metadatas)

    def count(self):
        return len(self.documents)

    def info(self):
        return {
            "component": "FakeDatabase",
            "count": self.count(),
        }

    def close(self):
        pass


def create_config(tmp_path):
    """
    Create a two-server synchronization configuration.
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


def test_multi_server_end_to_end(
    tmp_path,
):
    """
    Validate one complete multi-server cycle.

    Expected flow:

        server-a + server-b
                ↓
        synchronization
                ↓
        synchronized files
                ↓
        preprocessing
                ↓
        RAG ingestion
                ↓
        source-aware vector metadata
    """

    # ------------------------------------------------------
    # STEP 1 - Configuration
    # ------------------------------------------------------

    config = create_config(tmp_path)

    assert len(config.sources) == 2

    assert {
        source.source_id
        for source in config.sources
    } == {
        "server-a",
        "server-b",
    }

    # ------------------------------------------------------
    # STEP 2 - Synchronization
    # ------------------------------------------------------

    synchronizer = FakeRsyncSynchronizer(
        config.destination
    )

    synchronization_runner = (
        SynchronizationRunner(
            config=config,
            synchronizer=synchronizer,
        )
    )

    sync_result = (
        synchronization_runner.sync_once()
    )

    assert set(sync_result.keys()) == {
        "server-a",
        "server-b",
    }

    assert synchronizer.calls == [
        "server-a",
        "server-b",
    ]

    # ------------------------------------------------------
    # STEP 3 - Verify synchronized files
    # ------------------------------------------------------

    server_a_file = (
        Path(config.destination)
        / "server-a"
        / "auth.log"
    )

    server_b_file = (
        Path(config.destination)
        / "server-b"
        / "syslog"
    )

    assert server_a_file.exists()
    assert server_b_file.exists()

    # ------------------------------------------------------
    # STEP 4 - Processing
    # ------------------------------------------------------

    processor = SynchronizedLogProcessor(
        config=config,
    )

    processed = processor.process_all()

    assert set(processed.keys()) == {
        "server-a",
        "server-b",
    }

    assert len(
        processed["server-a"]
    ) > 0

    assert len(
        processed["server-b"]
    ) > 0

    # ------------------------------------------------------
    # STEP 5 - RAG ingestion
    # ------------------------------------------------------

    database = FakeDatabase()

    ingestor = SynchronizedLogIngestor(
        database=database,
    )

    pipeline = SynchronizedRAGPipeline(
        config=config,
        processor=processor,
        ingestor=ingestor,
    )

    results = pipeline.process_all()

    assert set(results.keys()) == {
        "server-a",
        "server-b",
    }

    assert len(results["server-a"]) > 0
    assert len(results["server-b"]) > 0

    # ------------------------------------------------------
    # STEP 6 - Verify source separation
    # ------------------------------------------------------

    metadata_sources = {
        metadata["synchronized_source"]
        for metadata in database.metadatas
    }

    assert "server-a" in metadata_sources
    assert "server-b" in metadata_sources

    # ------------------------------------------------------
    # STEP 7 - Verify vector count
    # ------------------------------------------------------

    assert pipeline.count() > 0

    # ------------------------------------------------------
    # STEP 8 - Combined runner
    # ------------------------------------------------------

    combined_runner = SynchronizedRAGRunner(
        synchronization_runner=(
            synchronization_runner
        ),
        rag_pipeline=pipeline,
    )

    combined_result = (
        combined_runner.run_once()
    )

    assert set(
        combined_result.keys()
    ) == {
        "server-a",
        "server-b",
    }

    # ------------------------------------------------------
    # STEP 9 - Cleanup
    # ------------------------------------------------------

    combined_runner.close()
def test_multi_server_multiple_log_files(
    tmp_path,
):
    """
    Validate processing of multiple log files from
    multiple synchronized servers.

    server-a:
        auth.log
        syslog

    server-b:
        auth.log
        kern.log
    """

    # ------------------------------------------------------
    # STEP 1 - Configuration
    # ------------------------------------------------------

    source_a = LogSource(
        source_id="server-a",
        hostname="server-a",
        log_paths=[
            Path("/var/log/auth.log"),
            Path("/var/log/syslog"),
        ],
    )

    source_b = LogSource(
        source_id="server-b",
        hostname="server-b",
        log_paths=[
            Path("/var/log/auth.log"),
            Path("/var/log/kern.log"),
        ],
    )

    config = SynchronizationConfig(
        sources=[
            source_a,
            source_b,
        ],
        sync_interval=60,
        destination=str(
            tmp_path / "synchronized"
        ),
    )

    # ------------------------------------------------------
    # STEP 2 - Simulate synchronization
    # ------------------------------------------------------

    synchronizer = FakeRsyncSynchronizer(
        config.destination
    )

    synchronization_runner = (
        SynchronizationRunner(
            config=config,
            synchronizer=synchronizer,
        )
    )

    synchronization_runner.sync_once()

    # ------------------------------------------------------
    # STEP 3 - Add multiple synchronized files
    # ------------------------------------------------------

    server_a_directory = (
        Path(config.destination)
        / "server-a"
    )

    server_b_directory = (
        Path(config.destination)
        / "server-b"
    )

    (server_a_directory / "syslog").write_text(
        "Jan 10 10:05:00 server-a "
        "systemd[1]: Started system service\n",
        encoding="utf-8",
    )

    (server_b_directory / "auth.log").write_text(
        "Jan 10 10:06:00 server-b "
        "sshd[300]: Failed password for root "
        "from 192.168.1.30 port 22 ssh2\n",
        encoding="utf-8",
    )

    (server_b_directory / "kern.log").write_text(
        "Jan 10 10:07:00 server-b "
        "kernel: Network interface event detected\n",
        encoding="utf-8",
    )

    # ------------------------------------------------------
    # STEP 4 - Verify file discovery
    # ------------------------------------------------------

    processor = SynchronizedLogProcessor(
        config=config,
    )

    server_a_files = (
        processor.discover_files(
            source_a
        )
    )

    server_b_files = (
        processor.discover_files(
            source_b
        )
    )

    assert len(server_a_files) == 2
    assert len(server_b_files) == 3

    assert {
        path.name
        for path in server_a_files
    } == {
        "auth.log",
        "syslog",
    }

    assert {
        path.name
        for path in server_b_files
    } == {
        "auth.log",
        "syslog",
        "kern.log",
    }

    # ------------------------------------------------------
    # STEP 5 - Process all sources
    # ------------------------------------------------------

    processed = processor.process_all()

    assert set(processed.keys()) == {
        "server-a",
        "server-b",
    }

    assert len(
        processed["server-a"]
    ) >= 2

    assert len(
        processed["server-b"]
    ) >= 2

    # ------------------------------------------------------
    # STEP 6 - Verify source separation
    # ------------------------------------------------------

    database = FakeDatabase()

    ingestor = SynchronizedLogIngestor(
        database=database,
    )

    pipeline = SynchronizedRAGPipeline(
        config=config,
        processor=processor,
        ingestor=ingestor,
    )

    results = pipeline.process_all()

    assert set(results.keys()) == {
        "server-a",
        "server-b",
    }

    assert len(results["server-a"]) > 0
    assert len(results["server-b"]) > 0

    # ------------------------------------------------------
    # STEP 7 - Verify metadata
    # ------------------------------------------------------

    source_metadata = [
        metadata["synchronized_source"]
        for metadata in database.metadatas
    ]

    assert "server-a" in source_metadata
    assert "server-b" in source_metadata

    assert all(
        source in {
            "server-a",
            "server-b",
        }
        for source in source_metadata
    )

    # ------------------------------------------------------
    # STEP 8 - Verify total ingestion
    # ------------------------------------------------------

    assert database.count() > 0
    assert pipeline.count() == database.count()

    pipeline.close()
def test_missing_source_directory_is_handled(
    tmp_path,
):
    """
    Verify that a source with no synchronized
    directory returns an empty file list.
    """

    config = create_config(tmp_path)

    processor = SynchronizedLogProcessor(
        config=config,
    )

    source = config.sources[0]

    files = processor.discover_files(
        source
    )

    assert files == []


def test_empty_log_file_does_not_crash(
    tmp_path,
):
    """
    Verify that an empty synchronized log file
    can be processed without crashing.
    """

    config = create_config(tmp_path)

    source_directory = (
        Path(config.destination)
        / "server-a"
    )

    source_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    empty_file = (
        source_directory
        / "auth.log"
    )

    empty_file.write_text(
        "",
        encoding="utf-8",
    )

    processor = SynchronizedLogProcessor(
        config=config,
    )

    records = processor.process_source(
        config.sources[0]
    )

    assert isinstance(
        records,
        list,
    )


def test_one_source_without_logs_does_not_affect_other_source(
    tmp_path,
):
    """
    Verify that one source having no synchronized
    logs does not prevent another source from
    being processed.
    """

    config = create_config(tmp_path)

    # ------------------------------------------------------
    # Create logs only for server-a
    # ------------------------------------------------------

    server_a_directory = (
        Path(config.destination)
        / "server-a"
    )

    server_a_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        server_a_directory
        / "auth.log"
    ).write_text(
        "Jan 10 10:00:00 "
        "server-a sshd[100]: "
        "Failed password for invalid user admin "
        "from 192.168.1.10 port 22 ssh2\n",
        encoding="utf-8",
    )

    # ------------------------------------------------------
    # server-b directory intentionally does not exist
    # ------------------------------------------------------

    processor = SynchronizedLogProcessor(
        config=config,
    )

    processed = processor.process_all()

    # ------------------------------------------------------
    # Verify source separation
    # ------------------------------------------------------

    assert set(processed.keys()) == {
        "server-a",
        "server-b",
    }

    assert len(
        processed["server-a"]
    ) > 0

    assert processed["server-b"] == []


def test_empty_source_does_not_trigger_ingestion(
    tmp_path,
):
    """
    Verify that a source with no processed records
    does not trigger RAG ingestion.
    """

    config = create_config(tmp_path)

    processor = SynchronizedLogProcessor(
        config=config,
    )

    database = FakeDatabase()

    ingestor = SynchronizedLogIngestor(
        database=database,
    )

    pipeline = SynchronizedRAGPipeline(
        config=config,
        processor=processor,
        ingestor=ingestor,
    )

    results = pipeline.process_all()

    assert results == {
        "server-a": [],
        "server-b": [],
    }

    assert database.count() == 0

    pipeline.close()