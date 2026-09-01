"""
Tests for security-aware evidence retrieval.
"""

from backend.database.chroma import ChromaDatabase
from backend.llm.embeddings import EmbeddingManager
from backend.rag.retriever import Retriever


def test_security_evidence_prioritises_security_events(
    tmp_path,
):
    database = ChromaDatabase(
        persist_directory=tmp_path,
        collection_name="security_evidence_test",
    )

    embedding_manager = EmbeddingManager()

    retriever = Retriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=3,
    )

    documents = [
        "Successfully dropped privileges.",
        "User executed sudo command as root to inspect system files.",
        "Normal SSH agent environment initialised.",
        "Audit event recorded during privileged command execution.",
    ]

    ids = [
        "security_001",
        "security_002",
        "security_003",
        "security_004",
    ]

    metadatas = [
        {
            "event_type": "SYSTEM_EVENT",
            "severity": "INFO",
            "source": "server-c",
        },
        {
            "event_type": "SUDO_COMMAND",
            "severity": "MEDIUM",
            "source": "server-a",
        },
        {
            "event_type": "SYSTEM_EVENT",
            "severity": "INFO",
            "source": "server-c",
        },
        {
            "event_type": "AUDIT",
            "severity": "MEDIUM",
            "source": "server-b",
        },
    ]

    embeddings = embedding_manager.embed_texts(
        documents
    )

    database.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    results = retriever.retrieve_security_evidence(
        query="sudo privilege escalation",
        top_k=3,
        candidate_k=4,
    )

    retrieved_metadata = results[
        "metadatas"
    ][0]

    retrieved_documents = results[
        "documents"
    ][0]

    # ----------------------------------------------------------
    # Privilege queries use strict security-event filtering.
    # Only SUDO_COMMAND is considered directly relevant.
    # ----------------------------------------------------------

    assert len(retrieved_documents) == 1

    event_types = [
        metadata.get("event_type")
        for metadata in retrieved_metadata
    ]

    assert event_types == [
        "SUDO_COMMAND"
    ]

    assert (
        retrieved_metadata[0]["severity"]
        == "MEDIUM"
    )

    assert (
        retrieved_metadata[0]["source"]
        == "server-a"
    )

    assert (
        retrieved_documents[0]
        == "User executed sudo command as root "
        "to inspect system files."
    )

    # ----------------------------------------------------------
    # Unrelated event types must not be returned.
    # ----------------------------------------------------------

    assert "AUDIT" not in event_types
    assert "SYSTEM_EVENT" not in event_types

    database.clear()
    retriever.close()