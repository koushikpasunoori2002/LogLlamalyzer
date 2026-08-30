"""
Source-aware retrieval integration tests.

Verifies that synchronized source information is preserved
from ingestion into retrieval metadata.
"""

from pathlib import Path

from backend.database.chroma import ChromaDatabase
from backend.llm.embeddings import EmbeddingManager
from backend.rag.chunking import ChunkManager
from backend.rag.retriever import Retriever
from backend.synchronization.ingestion.synchronized_log_ingestor import (
    SynchronizedLogIngestor,
)


def create_retriever(tmp_path):
    database = ChromaDatabase(
        persist_directory=tmp_path / "source_retrieval",
        collection_name="source_retrieval_test",
    )

    embedding_manager = EmbeddingManager()

    chunk_manager = ChunkManager()

    ingestor = SynchronizedLogIngestor(
        database=database,
        embedding_manager=embedding_manager,
        chunk_manager=chunk_manager,
    )

    retriever = Retriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=5,
    )

    return ingestor, retriever


def test_source_metadata_survives_retrieval(tmp_path):
    """
    Verify that synchronized_source metadata is preserved
    when synchronized records are ingested and retrieved.
    """

    ingestor, retriever = create_retriever(tmp_path)

    try:
        server_a_records = [
            "server-a failed SSH authentication attempt",
            "server-a repeated SSH login failure",
        ]

        server_b_records = [
            "server-b suspicious privilege escalation attempt",
            "server-b sudo command executed",
        ]

        ingestor.ingest_source_records(
            source_id="server-a",
            records=server_a_records,
        )

        ingestor.ingest_source_records(
            source_id="server-b",
            records=server_b_records,
        )

        results = retriever.retrieve(
            query="failed SSH authentication",
            top_k=5,
        )

        metadatas = results.get(
            "metadatas",
            [],
        )

        assert metadatas

        metadata_list = metadatas[0]

        assert metadata_list

        sources = [
            metadata.get("synchronized_source")
            for metadata in metadata_list
        ]

        assert "server-a" in sources

    finally:
        retriever.close()


def test_multiple_sources_are_represented_in_metadata(tmp_path):
    """
    Verify that retrieval metadata can distinguish
    between multiple synchronized sources.
    """

    ingestor, retriever = create_retriever(tmp_path)

    try:
        server_a_records = [
            "server-a SSH authentication failure",
        ]

        server_b_records = [
            "server-b SSH authentication failure",
        ]

        ingestor.ingest_source_records(
            source_id="server-a",
            records=server_a_records,
        )

        ingestor.ingest_source_records(
            source_id="server-b",
            records=server_b_records,
        )

        results = retriever.retrieve(
            query="SSH authentication failure",
            top_k=5,
        )

        metadatas = results.get(
            "metadatas",
            [],
        )

        assert metadatas

        metadata_list = metadatas[0]

        sources = {
            metadata.get("synchronized_source")
            for metadata in metadata_list
        }

        assert "server-a" in sources
        assert "server-b" in sources

    finally:
        retriever.close()
def test_source_filter_limits_retrieval_to_requested_source(
    tmp_path,
):
    """
    Verify that source filtering restricts retrieval
    to the requested synchronized source.
    """

    ingestor, retriever = create_retriever(tmp_path)

    try:
        server_a_records = [
            "server-a failed SSH authentication attempt",
            "server-a repeated SSH login failure",
        ]

        server_b_records = [
            "server-b failed SSH authentication attempt",
            "server-b repeated SSH login failure",
        ]

        ingestor.ingest_source_records(
            source_id="server-a",
            records=server_a_records,
        )

        ingestor.ingest_source_records(
            source_id="server-b",
            records=server_b_records,
        )

        results = retriever.retrieve(
            query="failed SSH authentication",
            top_k=5,
            source="server-a",
        )

        metadatas = results.get(
            "metadatas",
            [],
        )

        assert metadatas

        metadata_list = metadatas[0]

        assert metadata_list

        sources = {
            metadata.get("synchronized_source")
            for metadata in metadata_list
        }

        assert sources == {"server-a"}

    finally:
        retriever.close()
def test_source_filter_returns_only_requested_source(tmp_path):
    """
    Verify that source filtering restricts retrieval
    to the requested synchronized source.
    """

    ingestor, retriever = create_retriever(tmp_path)

    try:
        server_a_records = [
            "server-a failed SSH authentication attempt",
            "server-a repeated SSH login failure",
        ]

        server_b_records = [
            "server-b failed SSH authentication attempt",
            "server-b repeated SSH login failure",
        ]

        ingestor.ingest_source_records(
            source_id="server-a",
            records=server_a_records,
        )

        ingestor.ingest_source_records(
            source_id="server-b",
            records=server_b_records,
        )

        results = retriever.retrieve(
            query="failed SSH authentication",
            top_k=5,
            source="server-a",
        )

        metadatas = results.get(
            "metadatas",
            [],
        )

        assert metadatas

        metadata_list = metadatas[0]

        assert metadata_list

        sources = {
            metadata.get("synchronized_source")
            for metadata in metadata_list
        }

        assert sources == {"server-a"}

    finally:
        retriever.close()


def test_source_filter_excludes_other_sources(tmp_path):
    """
    Verify that records from other synchronized sources
    are excluded when a source filter is provided.
    """

    ingestor, retriever = create_retriever(tmp_path)

    try:
        server_a_records = [
            "server-a suspicious privilege escalation attempt",
        ]

        server_b_records = [
            "server-b suspicious privilege escalation attempt",
        ]

        ingestor.ingest_source_records(
            source_id="server-a",
            records=server_a_records,
        )

        ingestor.ingest_source_records(
            source_id="server-b",
            records=server_b_records,
        )

        results = retriever.retrieve(
            query="suspicious privilege escalation",
            top_k=5,
            source="server-b",
        )

        metadatas = results.get(
            "metadatas",
            [],
        )

        assert metadatas

        metadata_list = metadatas[0]

        assert metadata_list

        sources = [
            metadata.get("synchronized_source")
            for metadata in metadata_list
        ]

        assert "server-b" in sources
        assert "server-a" not in sources

    finally:
        retriever.close()
def test_source_filter_works_with_retrieve_documents(tmp_path):
    """
    Verify that retrieve_documents respects the source filter.
    """

    ingestor, retriever = create_retriever(tmp_path)

    try:
        ingestor.ingest_source_records(
            source_id="server-a",
            records=[
                "server-a failed SSH authentication attempt",
            ],
        )

        ingestor.ingest_source_records(
            source_id="server-b",
            records=[
                "server-b failed SSH authentication attempt",
            ],
        )

        documents = retriever.retrieve_documents(
            query="failed SSH authentication",
            top_k=5,
            source="server-a",
        )

        assert documents

        for document in documents:
            assert "server-a" in document
            assert "server-b" not in document

    finally:
        retriever.close()


def test_source_filter_works_with_retrieve_metadata(tmp_path):
    """
    Verify that retrieve_metadata respects the source filter.
    """

    ingestor, retriever = create_retriever(tmp_path)

    try:
        ingestor.ingest_source_records(
            source_id="server-a",
            records=[
                "server-a failed SSH authentication attempt",
            ],
        )

        ingestor.ingest_source_records(
            source_id="server-b",
            records=[
                "server-b failed SSH authentication attempt",
            ],
        )

        metadata = retriever.retrieve_metadata(
            query="failed SSH authentication",
            top_k=5,
            source="server-a",
        )

        assert metadata

        sources = {
            item.get("synchronized_source")
            for item in metadata
        }

        assert sources == {"server-a"}

    finally:
        retriever.close()


def test_source_filter_works_with_retrieve_with_scores(tmp_path):
    """
    Verify that retrieve_with_scores respects the source filter.
    """

    ingestor, retriever = create_retriever(tmp_path)

    try:
        ingestor.ingest_source_records(
            source_id="server-a",
            records=[
                "server-a failed SSH authentication attempt",
            ],
        )

        ingestor.ingest_source_records(
            source_id="server-b",
            records=[
                "server-b failed SSH authentication attempt",
            ],
        )

        results = retriever.retrieve_with_scores(
            query="failed SSH authentication",
            top_k=5,
            source="server-a",
        )

        assert results

        for result in results:
            assert result["document"]
            assert result["distance"] is not None
            assert "server-a" in result["document"]
            assert "server-b" not in result["document"]

    finally:
        retriever.close()