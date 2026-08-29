"""
Tests for synchronized log ingestion.

Pipeline:

LogRecord
    ↓
SynchronizedLogIngestor
    ↓
ChunkManager
    ↓
EmbeddingManager
    ↓
ChromaDB
"""


from pathlib import Path

from backend.preprocessing.models.log_record import LogRecord
from backend.rag.chunking import ChunkManager
from backend.llm.embeddings import EmbeddingManager
from backend.database.chroma import ChromaDatabase
from backend.synchronization.ingestion import (
    SynchronizedLogIngestor,
)


def create_records():
    """
    Create representative synchronized log records.
    """

    return [
        LogRecord(
            log_type="auth",
            source_file="auth.log",
            timestamp="Aug 29 14:00:01",
            hostname="server-a",
            process="sshd",
            pid=1234,
            severity="HIGH",
            event="Failed password",
            event_type="AUTH_FAILURE",
            user="root",
            ip="192.168.1.20",
            port=22,
            protocol="ssh",
            message=(
                "Failed password for root "
                "from 192.168.1.20 port 22 ssh2"
            ),
        ),
        LogRecord(
            log_type="auth",
            source_file="auth.log",
            timestamp="Aug 29 14:00:05",
            hostname="server-a",
            process="sshd",
            pid=1235,
            severity="HIGH",
            event="Failed password",
            event_type="AUTH_FAILURE",
            user="admin",
            ip="192.168.1.30",
            port=22,
            protocol="ssh",
            message=(
                "Failed password for admin "
                "from 192.168.1.30 port 22 ssh2"
            ),
        ),
        LogRecord(
            log_type="auth",
            source_file="auth.log",
            timestamp="Aug 29 14:00:10",
            hostname="server-a",
            process="sshd",
            pid=1236,
            severity="INFO",
            event="Successful login",
            event_type="AUTH_SUCCESS",
            user="osboxes",
            ip="192.168.1.40",
            port=22,
            protocol="ssh",
            message=(
                "Accepted password for osboxes "
                "from 192.168.1.40 port 22 ssh2"
            ),
        ),
    ]


def test_ingest_records(tmp_path):

    database_path = (
        tmp_path
        / "synchronized_ingestion"
    )

    database = ChromaDatabase(
        persist_directory=database_path,
        collection_name="synchronized_logs",
    )

    embedding_manager = EmbeddingManager()

    chunk_manager = ChunkManager(
        chunk_size=500,
        overlap=50,
    )

    ingestor = SynchronizedLogIngestor(
        database=database,
        embedding_manager=embedding_manager,
        chunk_manager=chunk_manager,
    )

    records = create_records()

    chunks = ingestor.ingest_source_records(
        source_id="server-a",
        records=records,
    )

    assert len(chunks) == len(records)

    assert database.count() == len(records)

    for chunk in chunks:

        assert chunk.chunk_id
        assert chunk.text
        assert chunk.source == "server-a"

        assert (
            chunk.metadata["log_type"]
            == "auth"
        )

        assert (
            chunk.metadata["hostname"]
            == "server-a"
        )

        assert (
            chunk.metadata[
                "synchronized_source"
            ]
            == "server-a"
        )

    stored = database.get()

    assert len(stored["ids"]) == len(records)

    assert len(
        stored["documents"]
    ) == len(records)

    assert len(
        stored["metadatas"]
    ) == len(records)

    database.clear()

    assert database.count() == 0

    ingestor.close()


def test_ingest_empty_records(tmp_path):

    database_path = (
        tmp_path
        / "empty_ingestion"
    )

    database = ChromaDatabase(
        persist_directory=database_path,
        collection_name="empty_logs",
    )

    ingestor = SynchronizedLogIngestor(
        database=database,
        embedding_manager=EmbeddingManager(),
        chunk_manager=ChunkManager(),
    )

    chunks = ingestor.ingest_records([])

    assert chunks == []

    assert database.count() == 0

    ingestor.close()


def test_ingestor_info(tmp_path):

    database_path = (
        tmp_path
        / "info_ingestion"
    )

    database = ChromaDatabase(
        persist_directory=database_path,
        collection_name="info_logs",
    )

    ingestor = SynchronizedLogIngestor(
        database=database,
        embedding_manager=EmbeddingManager(),
        chunk_manager=ChunkManager(),
    )

    info = ingestor.info()

    assert (
        info["component"]
        == "SynchronizedLogIngestor"
    )

    assert (
        info["default_source"]
        == "synchronized"
    )

    assert (
        info["database"]["database"]
        == "ChromaDB"
    )

    ingestor.close()