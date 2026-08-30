"""
Source-filtered retrieval integration tests.

Verifies that Retriever can restrict search results
to a specific synchronized source.
"""

from backend.database.chroma import ChromaDatabase
from backend.llm.embeddings import EmbeddingManager
from backend.rag.chunking import ChunkManager
from backend.rag.retriever import Retriever
from backend.synchronization.ingestion.synchronized_log_ingestor import (
    SynchronizedLogIngestor,
)


def create_retriever(tmp_path):
    """
    Create an isolated database, ingestor, and retriever
    for source-filtered retrieval testing.
    """

    database = ChromaDatabase(
        persist_directory=tmp_path / "source_filtered_retrieval",
        collection_name="source_filtered_test",
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


def test_retrieval_without_source_returns_multiple_sources(tmp_path):
    """
    Verify that retrieval without a source filter can return
    records from multiple synchronized sources.
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

        sources = {
            metadata.get("synchronized_source")
            for metadata in metadata_list
        }

        assert "server-a" in sources
        assert "server-b" in sources

    finally:
        retriever.close()


def test_source_filter_returns_only_requested_source(tmp_path):
    """
    Verify that source filtering returns records only from
    the requested synchronized source.
    """

    ingestor, retriever = create_retriever(tmp_path)

    try:
        ingestor.ingest_source_records(
            source_id="server-a",
            records=[
                "server-a failed SSH authentication attempt",
                "server-a repeated SSH login failure",
            ],
        )

        ingestor.ingest_source_records(
            source_id="server-b",
            records=[
                "server-b failed SSH authentication attempt",
                "server-b repeated SSH login failure",
            ],
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

        sources = {
            metadata.get("synchronized_source")
            for metadata in metadata_list
        }

        assert sources == {"server-a"}

    finally:
        retriever.close()


def test_source_filter_returns_second_source_only(tmp_path):
    """
    Verify that a different source filter returns only
    records belonging to that source.
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

        results = retriever.retrieve(
            query="failed SSH authentication",
            top_k=5,
            source="server-b",
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

        assert sources == {"server-b"}

    finally:
        retriever.close()


def test_nonexistent_source_returns_no_results(tmp_path):
    """
    Verify that filtering by an unknown source does not
    return records from other sources.
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

        results = retriever.retrieve(
            query="failed SSH authentication",
            top_k=5,
            source="server-c",
        )

        documents = results.get(
            "documents",
            [],
        )

        assert not documents or documents[0] == []
        
    finally:
        retriever.close()


def test_source_filter_preserves_metadata(tmp_path):
    """
    Verify that source filtering does not remove other
    metadata fields from retrieved records.
    """

    ingestor, retriever = create_retriever(tmp_path)

    try:
        ingestor.ingest_source_records(
            source_id="server-a",
            records=[
                "server-a failed SSH authentication attempt",
            ],
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

        for metadata in metadata_list:
            assert metadata.get("synchronized_source") == "server-a"

    finally:
        retriever.close()