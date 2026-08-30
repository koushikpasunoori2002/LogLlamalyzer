"""
Tests for SynchronizedRAGPipeline.
"""

from pathlib import Path

from backend.synchronization.config.synchronization_config import (
    SynchronizationConfig,
)
from backend.synchronization.models.log_source import LogSource
from backend.synchronization.pipeline.synchronized_rag_pipeline import (
    SynchronizedRAGPipeline,
)


class FakeProcessor:
    """
    Fake synchronized log processor used to isolate
    the RAG pipeline from file processing.
    """

    def __init__(self, records_by_source):
        self.records_by_source = records_by_source
        self.calls = []

    def process_source(self, source):
        self.calls.append(source.source_id)

        return self.records_by_source.get(
            source.source_id,
            [],
        )

    def process_all(self):
        return {
            source_id: records
            for source_id, records
            in self.records_by_source.items()
        }

    def info(self):
        return {
            "component": "FakeProcessor",
        }


class FakeIngestor:
    """
    Fake ingestion component used to isolate
    pipeline coordination from ChromaDB and embeddings.
    """

    def __init__(self):
        self.calls = []
        self.vector_count = 0

    def ingest_source_records(
        self,
        source_id,
        records,
    ):
        self.calls.append(
            {
                "source_id": source_id,
                "records": list(records),
            }
        )

        chunks = [
            f"chunk:{source_id}:{index}"
            for index, _ in enumerate(records)
        ]

        self.vector_count += len(chunks)

        return chunks

    def count(self):
        return self.vector_count

    def info(self):
        return {
            "component": "FakeIngestor",
        }

    def close(self):
        pass


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


def test_process_source_processes_and_ingests_records(
    tmp_path,
):
    """
    Verify that one source is processed and its
    records are passed to the ingestor.
    """

    config = create_config(tmp_path)

    records = [
        "failed login",
        "successful login",
    ]

    processor = FakeProcessor(
        {
            "server-a": records,
        }
    )

    ingestor = FakeIngestor()

    pipeline = SynchronizedRAGPipeline(
        config=config,
        processor=processor,
        ingestor=ingestor,
    )

    result = pipeline.process_source(
        config.sources[0]
    )

    assert result == [
        "chunk:server-a:0",
        "chunk:server-a:1",
    ]

    assert processor.calls == [
        "server-a"
    ]

    assert len(ingestor.calls) == 1

    assert ingestor.calls[0]["source_id"] == (
        "server-a"
    )

    assert ingestor.calls[0]["records"] == records


def test_process_source_empty_records(
    tmp_path,
):
    """
    Verify that empty processing results do not
    trigger ingestion.
    """

    config = create_config(tmp_path)

    processor = FakeProcessor(
        {
            "server-a": [],
        }
    )

    ingestor = FakeIngestor()

    pipeline = SynchronizedRAGPipeline(
        config=config,
        processor=processor,
        ingestor=ingestor,
    )

    result = pipeline.process_source(
        config.sources[0]
    )

    assert result == []

    assert processor.calls == [
        "server-a"
    ]

    assert ingestor.calls == []


def test_process_all_keeps_sources_separate(
    tmp_path,
):
    """
    Verify that records from multiple synchronized
    sources remain associated with their source IDs.
    """

    config = create_config(tmp_path)

    processor = FakeProcessor(
        {
            "server-a": [
                "auth failure",
            ],
            "server-b": [
                "kernel message",
                "system event",
            ],
        }
    )

    ingestor = FakeIngestor()

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

    assert results["server-a"] == [
        "chunk:server-a:0",
    ]

    assert results["server-b"] == [
        "chunk:server-b:0",
        "chunk:server-b:1",
    ]

    assert len(ingestor.calls) == 2

    assert ingestor.calls[0]["source_id"] == (
        "server-a"
    )

    assert ingestor.calls[1]["source_id"] == (
        "server-b"
    )


def test_pipeline_count(
    tmp_path,
):
    """
    Verify that the pipeline exposes the
    ingestor vector count.
    """

    config = create_config(tmp_path)

    processor = FakeProcessor(
        {
            "server-a": [
                "record one",
                "record two",
            ],
        }
    )

    ingestor = FakeIngestor()

    pipeline = SynchronizedRAGPipeline(
        config=config,
        processor=processor,
        ingestor=ingestor,
    )

    pipeline.process_source(
        config.sources[0]
    )

    assert pipeline.count() == 2


def test_pipeline_info(
    tmp_path,
):
    """
    Verify pipeline information.
    """

    config = create_config(tmp_path)

    processor = FakeProcessor({})

    ingestor = FakeIngestor()

    pipeline = SynchronizedRAGPipeline(
        config=config,
        processor=processor,
        ingestor=ingestor,
    )

    info = pipeline.info()

    assert info["component"] == (
        "SynchronizedRAGPipeline"
    )

    assert info["processor"]["component"] == (
        "FakeProcessor"
    )

    assert info["ingestor"]["component"] == (
        "FakeIngestor"
    )

    assert info["vector_count"] == 0


def test_pipeline_close(
    tmp_path,
):
    """
    Verify that closing the pipeline delegates
    to the ingestion component.
    """

    config = create_config(tmp_path)

    processor = FakeProcessor({})

    ingestor = FakeIngestor()

    pipeline = SynchronizedRAGPipeline(
        config=config,
        processor=processor,
        ingestor=ingestor,
    )

    pipeline.close()