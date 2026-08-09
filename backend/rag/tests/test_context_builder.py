"""
test_context_builder.py

Integration test for ContextBuilder.

Tests:

Log Retriever
    +
Knowledge Retriever
    ↓
ContextBuilder
    ↓
RAGContext
"""

from pathlib import Path
import sys


# --------------------------------------------------------------
# Project Root
# --------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --------------------------------------------------------------
# Imports
# --------------------------------------------------------------

from backend.rag.context import ContextBuilder

from backend.rag.retriever import Retriever

from backend.knowledge import (
    KnowledgeManager,
    KnowledgeIngestor,
    KnowledgeRetriever,
)

from backend.database.chroma import ChromaDatabase

from backend.llm.embeddings import EmbeddingManager


# --------------------------------------------------------------
# Main Test
# --------------------------------------------------------------

def main():

    print("=" * 70)
    print("CONTEXT BUILDER TEST")
    print("=" * 70)

    # ----------------------------------------------------------
    # Shared embedding model
    # ----------------------------------------------------------

    embedding_manager = EmbeddingManager()

    print("\nEmbedding Model")
    print(
        embedding_manager.model_information()
    )

    # ----------------------------------------------------------
    # LOG DATABASE
    # ----------------------------------------------------------

    print("\n" + "=" * 70)
    print("LOG RETRIEVER SETUP")
    print("=" * 70)

    log_database_path = (
        PROJECT_ROOT
        / "data"
        / "test_context_logs"
    )

    log_database = ChromaDatabase(
        persist_directory=log_database_path,
        collection_name="context_logs_test",
    )

    log_database.clear()

    log_documents = [
        "Failed password for root from 192.168.1.20 port 22 ssh2",
        "Failed password for admin from 192.168.1.30 port 22 ssh2",
        "User successfully logged into the system",
    ]

    log_ids = [
        "context_log_001",
        "context_log_002",
        "context_log_003",
    ]

    log_metadatas = [
        {
            "log_type": "auth",
            "severity": "HIGH",
            "source": "auth.log",
        },
        {
            "log_type": "auth",
            "severity": "HIGH",
            "source": "auth.log",
        },
        {
            "log_type": "auth",
            "severity": "LOW",
            "source": "auth.log",
        },
    ]

    log_embeddings = (
        embedding_manager.embed_texts(
            log_documents
        )
    )

    log_database.add(
        ids=log_ids,
        embeddings=log_embeddings,
        documents=log_documents,
        metadatas=log_metadatas,
    )

    print(
        f"Log Records Stored : "
        f"{log_database.count()}"
    )

    if log_database.count() != 3:

        raise AssertionError(
            "Log database should contain 3 records."
        )

    log_retriever = Retriever(
        database=log_database,
        embedding_manager=embedding_manager,
        top_k=2,
    )

    print(
        "Log Retriever: READY"
    )

    # ----------------------------------------------------------
    # KNOWLEDGE DATABASE
    # ----------------------------------------------------------

    print("\n" + "=" * 70)
    print("KNOWLEDGE RETRIEVER SETUP")
    print("=" * 70)

    knowledge_file = (
        PROJECT_ROOT
        / "backend"
        / "knowledge"
        / "documents"
        / "test_knowledge.txt"
    )

    if not knowledge_file.exists():

        raise FileNotFoundError(
            f"Knowledge file not found: "
            f"{knowledge_file}"
        )

    knowledge_manager = KnowledgeManager()

    knowledge_document = (
        knowledge_manager.load_file(
            knowledge_file,
            category="authentication",
        )
    )

    knowledge_database_path = (
        PROJECT_ROOT
        / "data"
        / "test_context_knowledge"
    )

    knowledge_database = ChromaDatabase(
        persist_directory=knowledge_database_path,
        collection_name="context_knowledge_test",
    )

    knowledge_database.clear()

    knowledge_ingestor = KnowledgeIngestor(
        database=knowledge_database,
        embedding_manager=embedding_manager,
        chunk_size=100,
        overlap=20,
    )

    knowledge_chunks = (
        knowledge_ingestor.ingest_document(
            knowledge_document
        )
    )

    print(
        f"Knowledge Chunks Stored : "
        f"{len(knowledge_chunks)}"
    )

    if not knowledge_chunks:

        raise AssertionError(
            "Knowledge ingestion produced no chunks."
        )

    knowledge_retriever = KnowledgeRetriever(
        database=knowledge_database,
        embedding_manager=embedding_manager,
        top_k=2,
    )

    print(
        "Knowledge Retriever: READY"
    )

    # ----------------------------------------------------------
    # CONTEXT BUILDER
    # ----------------------------------------------------------

    print("\n" + "=" * 70)
    print("CONTEXT BUILDER")
    print("=" * 70)

    builder = ContextBuilder(
        log_retriever=log_retriever,
        knowledge_retriever=knowledge_retriever,
        top_k_logs=2,
        top_k_knowledge=2,
    )

    query = (
        "failed SSH authentication "
        "brute force attack"
    )

    print(
        f"Query: {query}"
    )

    context = builder.build(
        query
    )

    # ----------------------------------------------------------
    # Verify Context
    # ----------------------------------------------------------

    print("\n" + "=" * 70)
    print("COMBINED RAG CONTEXT")
    print("=" * 70)

    print(context)

    print("\nLog Results")

    for index, result in enumerate(
        context.log_results,
        start=1,
    ):

        print(
            f"\nResult {index}"
        )

        print(
            f"Document : "
            f"{result['document']}"
        )

        print(
            f"Metadata : "
            f"{result['metadata']}"
        )

        print(
            f"Distance : "
            f"{result['distance']}"
        )

    print("\nKnowledge Results")

    for index, result in enumerate(
        context.knowledge_results,
        start=1,
    ):

        print(
            f"\nResult {index}"
        )

        print(
            f"Document : "
            f"{result['document']}"
        )

        print(
            f"Metadata : "
            f"{result['metadata']}"
        )

        print(
            f"Distance : "
            f"{result['distance']}"
        )

    # ----------------------------------------------------------
    # Assertions
    # ----------------------------------------------------------

    if context.query != query:

        raise AssertionError(
            "Context query is incorrect."
        )

    if context.log_count() != 2:

        raise AssertionError(
            "Expected 2 log retrieval results."
        )

    if context.knowledge_count() != 2:

        raise AssertionError(
            "Expected 2 knowledge retrieval results."
        )

    if context.metadata["log_count"] != 2:

        raise AssertionError(
            "Log count metadata is incorrect."
        )

    if context.metadata["knowledge_count"] != 2:

        raise AssertionError(
            "Knowledge count metadata is incorrect."
        )

    print(
        "\nContext Builder: PASS"
    )

    # ----------------------------------------------------------
    # Builder Information
    # ----------------------------------------------------------

    print("\nBuilder Information")

    print(
        builder.info()
    )

    # ----------------------------------------------------------
    # Cleanup
    # ----------------------------------------------------------

    log_database.clear()
    knowledge_database.clear()

    if log_database.count() != 0:

        raise AssertionError(
            "Log database cleanup failed."
        )

    if knowledge_database.count() != 0:

        raise AssertionError(
            "Knowledge database cleanup failed."
        )

    print(
        "\nCleanup: PASS"
    )

    # ----------------------------------------------------------
    # Final Result
    # ----------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        "CONTEXT BUILDER TEST PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":

    main()