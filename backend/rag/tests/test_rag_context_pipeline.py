"""
test_rag_context_pipeline.py

End-to-end integration test for the Phase 15 RAG
context pipeline.

Pipeline:

Query
    ↓
Log Retriever
    ↓
Knowledge Retriever
    ↓
ContextBuilder
    ↓
RAGContext
    ↓
ContextFormatter
    ↓
LLM-ready Context
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

from backend.rag.context import (
    ContextBuilder,
    ContextFormatter,
)

from backend.rag.retriever import Retriever

from backend.knowledge import (
    KnowledgeManager,
    KnowledgeIngestor,
    KnowledgeRetriever,
)

from backend.database.chroma import ChromaDatabase

from backend.llm.embeddings import EmbeddingManager


# --------------------------------------------------------------
# Main
# --------------------------------------------------------------

def main():

    print("=" * 70)
    print("PHASE 15 RAG CONTEXT PIPELINE TEST")
    print("=" * 70)

    # ----------------------------------------------------------
    # Shared embedding model
    # ----------------------------------------------------------

    embedding_manager = EmbeddingManager()

    print("\nEmbedding Model")
    print(
        embedding_manager.model_information()
    )

    # ==========================================================
    # LOG RETRIEVER
    # ==========================================================

    print("\n" + "=" * 70)
    print("STEP 1 - LOG RETRIEVER")
    print("=" * 70)

    log_database_path = (
        PROJECT_ROOT
        / "data"
        / "test_rag_context_logs"
    )

    log_database = ChromaDatabase(
        persist_directory=log_database_path,
        collection_name="rag_context_logs",
    )

    log_database.clear()

    log_documents = [
        (
            "Failed password for root from "
            "192.168.1.20 port 22 ssh2"
        ),
        (
            "Failed password for admin from "
            "192.168.1.30 port 22 ssh2"
        ),
        (
            "Successful login for user osboxes"
        ),
    ]

    log_ids = [
        "rag_log_001",
        "rag_log_002",
        "rag_log_003",
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

    log_retriever = Retriever(
        database=log_database,
        embedding_manager=embedding_manager,
        top_k=2,
    )

    print(
        f"Log Vectors Stored : "
        f"{log_database.count()}"
    )

    if log_database.count() != 3:

        raise AssertionError(
            "Log database should contain 3 records."
        )

    print("Log Retriever: PASS")

    # ==========================================================
    # KNOWLEDGE RETRIEVER
    # ==========================================================

    print("\n" + "=" * 70)
    print("STEP 2 - KNOWLEDGE RETRIEVER")
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
        / "test_rag_context_knowledge"
    )

    knowledge_database = ChromaDatabase(
        persist_directory=knowledge_database_path,
        collection_name="rag_context_knowledge",
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

    knowledge_retriever = KnowledgeRetriever(
        database=knowledge_database,
        embedding_manager=embedding_manager,
        top_k=2,
    )

    print(
        f"Knowledge Chunks : "
        f"{len(knowledge_chunks)}"
    )

    if not knowledge_chunks:

        raise AssertionError(
            "Knowledge ingestion failed."
        )

    print("Knowledge Retriever: PASS")

    # ==========================================================
    # CONTEXT BUILDER
    # ==========================================================

    print("\n" + "=" * 70)
    print("STEP 3 - CONTEXT BUILDER")
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

    context = builder.build(
        query
    )

    print(context)

    if context.log_count() != 2:

        raise AssertionError(
            "Expected 2 retrieved log results."
        )

    if context.knowledge_count() != 2:

        raise AssertionError(
            "Expected 2 retrieved knowledge results."
        )

    print(
        "\nContext Builder: PASS"
    )

    # ==========================================================
    # CONTEXT FORMATTER
    # ==========================================================

    print("\n" + "=" * 70)
    print("STEP 4 - CONTEXT FORMATTER")
    print("=" * 70)

    formatter = ContextFormatter()

    formatted_context = formatter.format(
        context
    )

    prompt_context = (
        formatter.format_for_prompt(
            context
        )
    )

    print("\nFormatted Context")
    print("-" * 70)
    print(formatted_context)

    print("\nLLM Prompt Context")
    print("-" * 70)
    print(prompt_context)

    # ----------------------------------------------------------
    # Verify formatted context
    # ----------------------------------------------------------

    required_sections = [
        "USER QUERY",
        "RETRIEVED LOGS",
        "SECURITY KNOWLEDGE",
    ]

    for section in required_sections:

        if section not in formatted_context:

            raise AssertionError(
                f"Missing section: {section}"
            )

    if query not in formatted_context:

        raise AssertionError(
            "User query is missing from formatted context."
        )

    if (
        "Failed password"
        not in formatted_context
    ):

        raise AssertionError(
            "Retrieved log evidence is missing."
        )

    if (
        "brute-force"
        not in formatted_context
    ):

        raise AssertionError(
            "Retrieved security knowledge is missing."
        )

    if (
        "Base the analysis on the retrieved evidence."
        not in prompt_context
    ):

        raise AssertionError(
            "LLM prompt instructions are missing."
        )

    print(
        "\nContext Formatter: PASS"
    )

    # ==========================================================
    # FINAL CONTEXT VERIFICATION
    # ==========================================================

    print("\n" + "=" * 70)
    print("STEP 5 - FINAL CONTEXT VERIFICATION")
    print("=" * 70)

    print(
        f"Query              : "
        f"{context.query}"
    )

    print(
        f"Log Results        : "
        f"{context.log_count()}"
    )

    print(
        f"Knowledge Results  : "
        f"{context.knowledge_count()}"
    )

    print(
        f"Formatted Length   : "
        f"{len(formatted_context)} characters"
    )

    print(
        f"Prompt Length      : "
        f"{len(prompt_context)} characters"
    )

    if len(formatted_context) == 0:

        raise AssertionError(
            "Formatted context is empty."
        )

    if len(prompt_context) == 0:

        raise AssertionError(
            "Prompt context is empty."
        )

    print(
        "\nFinal Context Verification: PASS"
    )

    # ==========================================================
    # CLEANUP
    # ==========================================================

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

    # ==========================================================
    # FINAL RESULT
    # ==========================================================

    print("\n" + "=" * 70)
    print(
        "PHASE 15 RAG CONTEXT PIPELINE TEST PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()