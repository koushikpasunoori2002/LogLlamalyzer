"""
Performance and reliability regression evaluation.

Verifies that the Phase 39 performance, reliability and
incremental-processing changes preserve existing functionality.

The regression suite covers:

- performance baseline execution
- embedding generation
- vector retrieval
- context construction
- LLM analysis
- reliability error handling
- repeated requests
- incremental duplicate detection
- new-record processing
- source-aware retrieval
- security-analysis compatibility
"""

from pathlib import Path
import sys
import shutil
import time
from unittest.mock import Mock, patch

import requests


# ------------------------------------------------------------------
# Project path
# ------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# ------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------

from backend.llm.embeddings import EmbeddingManager
from backend.llm.generation import LLMClient
from backend.llm.generation import RAGAnalyzer

from backend.database.chroma import ChromaDatabase

from backend.rag.retriever import Retriever
from backend.rag.context import ContextBuilder
from backend.rag.context import RAGContext

from backend.rag.chunking import ChunkManager

from backend.synchronization.ingestion.synchronized_log_ingestor import (
    SynchronizedLogIngestor,
)


# ------------------------------------------------------------------
# Test configuration
# ------------------------------------------------------------------

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "performance_reliability_regression_test"
)

COLLECTION_NAME = (
    "performance_reliability_regression_test"
)

TOP_K = 3

QUERIES = [
    "failed SSH authentication brute force attack",
    "suspicious sudo privilege escalation activity",
    "possible malware execution detected",
    "possible network scanning suspicious connections",
    "repeated failed login attempts",
]


# ------------------------------------------------------------------
# Regression documents
# ------------------------------------------------------------------

DOCUMENTS = [
    (
        "Multiple failed SSH authentication attempts were "
        "detected from a remote IP address. Repeated failed "
        "password attempts may indicate an SSH brute force attack."
    ),
    (
        "The system recorded repeated failed login attempts "
        "for the same account. This pattern may indicate a "
        "credential attack."
    ),
    (
        "A user executed sudo commands to obtain elevated "
        "privileges. Suspicious privilege escalation activity "
        "should be investigated."
    ),
    (
        "A suspicious executable was launched from a temporary "
        "directory. Unexpected process execution may indicate "
        "malware activity."
    ),
    (
        "Multiple connections were attempted against different "
        "network ports. Repeated connection attempts may indicate "
        "network scanning or reconnaissance activity."
    ),
]


IDS = [
    "regression_001",
    "regression_002",
    "regression_003",
    "regression_004",
    "regression_005",
]


METADATAS = [
    {
        "scenario": "ssh_brute_force",
        "classification": "ssh_brute_force",
        "severity": "HIGH",
        "source": "server-a",
        "log_type": "auth",
    },
    {
        "scenario": "credential_attack",
        "classification": "credential_attack",
        "severity": "MEDIUM",
        "source": "server-b",
        "log_type": "auth",
    },
    {
        "scenario": "privilege_escalation",
        "classification": "privilege_escalation",
        "severity": "HIGH",
        "source": "server-b",
        "log_type": "auth",
    },
    {
        "scenario": "malware",
        "classification": "malware",
        "severity": "HIGH",
        "source": "server-c",
        "log_type": "syslog",
    },
    {
        "scenario": "network_scanning",
        "classification": "network_scanning",
        "severity": "HIGH",
        "source": "server-c",
        "log_type": "syslog",
    },
]


# ------------------------------------------------------------------
# Minimal test record
# ------------------------------------------------------------------

class TestRecord:
    """
    Minimal LogRecord-compatible object.
    """

    def __init__(
        self,
        message,
        source_file,
        event_id,
    ):

        self.message = message
        self.source_file = source_file
        self.event_id = event_id

    def to_dict(self):

        return {
            "message": self.message,
            "source_file": self.source_file,
            "event_id": self.event_id,
        }


# ------------------------------------------------------------------
# Counting embedding manager
# ------------------------------------------------------------------

class CountingEmbeddingManager(
    EmbeddingManager
):
    """
    Tracks embedding calls and number of chunks embedded.
    """

    def __init__(self):

        super().__init__()

        self.embedding_calls = 0
        self.total_chunks_embedded = 0

    def embed_chunks(
        self,
        chunks,
    ):

        self.embedding_calls += 1

        self.total_chunks_embedded += len(
            chunks
        )

        return super().embed_chunks(
            chunks
        )


# ------------------------------------------------------------------
# Helper
# ------------------------------------------------------------------

def extract_documents(results):
    """
    Extract documents from a ChromaDB result.
    """

    if not results:
        return []

    documents = results.get(
        "documents",
        [],
    )

    if not documents:
        return []

    if not isinstance(
        documents,
        list,
    ):
        return []

    if not isinstance(
        documents[0],
        list,
    ):
        return []

    return documents[0]


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():

    print("=" * 70)
    print(
        "PERFORMANCE / RELIABILITY REGRESSION TEST"
    )
    print("=" * 70)

    passed = 0
    failed = 0

    def check(
        name,
        condition,
    ):

        nonlocal passed, failed

        if condition:

            print(
                f"{name}: PASS"
            )

            passed += 1

        else:

            print(
                f"{name}: FAIL"
            )

            failed += 1

    # --------------------------------------------------------------
    # Fresh benchmark database
    # --------------------------------------------------------------

    if DATABASE_PATH.exists():

        try:

            shutil.rmtree(
                DATABASE_PATH
            )

        except PermissionError:

            pass

    database = ChromaDatabase(
        persist_directory=DATABASE_PATH,
        collection_name=COLLECTION_NAME,
    )

    embedding_manager = (
        CountingEmbeddingManager()
    )

    # --------------------------------------------------------------
    # Prepare benchmark vectors
    # --------------------------------------------------------------

    print()
    print("Preparing regression database...")

    embeddings = embedding_manager.embed_texts(
        DOCUMENTS
    )

    database.add(
        ids=IDS,
        embeddings=embeddings,
        documents=DOCUMENTS,
        metadatas=METADATAS,
    )

    print(
        "Records stored:",
        database.count(),
    )

    check(
        "Regression database setup",
        database.count() == len(DOCUMENTS),
    )

    # --------------------------------------------------------------
    # Create retriever
    # --------------------------------------------------------------

    retriever = Retriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=TOP_K,
        distance_threshold=0.98,
    )

    # --------------------------------------------------------------
    # Create context builder
    # --------------------------------------------------------------

    context_builder = ContextBuilder(
        log_retriever=retriever,
        knowledge_retriever=None,
        top_k_logs=TOP_K,
        top_k_knowledge=0,
    )

    # --------------------------------------------------------------
    # Create RAG analyzer
    # --------------------------------------------------------------

    analyzer = RAGAnalyzer()

    # ==============================================================
    # TEST 1 - EMBEDDING REGRESSION
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 1 - EMBEDDING REGRESSION")

    start = time.perf_counter()

    query_embedding = (
        embedding_manager.embed_text(
            QUERIES[0]
        )
    )

    embedding_time = (
        time.perf_counter()
        - start
    )

    embedding_valid = (
        query_embedding is not None
    )

    print(
        f"Embedding time: "
        f"{embedding_time:.4f} seconds"
    )

    print(
        "Embedding generated:",
        embedding_valid,
    )

    check(
        "Embedding regression",
        embedding_valid,
    )

    # ==============================================================
    # TEST 2 - RETRIEVAL REGRESSION
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 2 - RETRIEVAL REGRESSION")

    start = time.perf_counter()

    retrieval_result = retriever.retrieve(
        query=QUERIES[0],
        top_k=TOP_K,
    )

    retrieval_time = (
        time.perf_counter()
        - start
    )

    retrieved_documents = extract_documents(
        retrieval_result
    )

    print(
        f"Retrieval time: "
        f"{retrieval_time:.4f} seconds"
    )

    print(
        "Retrieved documents:",
        len(retrieved_documents),
    )

    check(
        "Retrieval regression",
        len(retrieved_documents) > 0,
    )

    # ==============================================================
    # TEST 3 - RANKING ORDER
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 3 - RANKING ORDER")

    scored_results = (
        retriever.retrieve_with_scores(
            query=QUERIES[0],
            top_k=TOP_K,
        )
    )

    distances = [
        item["distance"]
        for item in scored_results
        if item.get("distance") is not None
    ]

    ranking_valid = (
        len(distances) > 0
        and distances
        == sorted(distances)
    )

    print(
        "Distances:",
        distances,
    )

    check(
        "Ranking order regression",
        ranking_valid,
    )

    # ==============================================================
    # TEST 4 - CONTEXT REGRESSION
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 4 - CONTEXT CONSTRUCTION")

    start = time.perf_counter()

    context = context_builder.build(
        QUERIES[0]
    )

    context_time = (
        time.perf_counter()
        - start
    )

    print(
        f"Context time: "
        f"{context_time:.4f} seconds"
    )

    print(
        "Log results:",
        context.log_count(),
    )

    context_valid = (
        isinstance(
            context,
            RAGContext,
        )
        and context.log_count() > 0
    )

    check(
        "Context construction regression",
        context_valid,
    )

    # ==============================================================
    # TEST 5 - LLM REGRESSION
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 5 - LLM ANALYSIS")

    start = time.perf_counter()

    llm_response = analyzer.analyze(
        context
    )

    analysis_time = (
        time.perf_counter()
        - start
    )

    print(
        f"LLM analysis time: "
        f"{analysis_time:.4f} seconds"
    )

    print(
        "Response generated:",
        llm_response is not None,
    )

    analysis_valid = (
        llm_response is not None
        and isinstance(
            llm_response.answer,
            str,
        )
        and bool(
            llm_response.answer.strip()
        )
    )

    check(
        "LLM analysis regression",
        analysis_valid,
    )

    # ==============================================================
    # TEST 6 - LLM CONFIGURATION
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 6 - LLM OPTIMIZATION CONFIGURATION")

    llm_information = (
        analyzer.llm_client.info()
    )

    print(
        "LLM configuration:",
        llm_information,
    )

    optimization_config_valid = (
        llm_information.get(
            "num_predict"
        )
        is not None
        and llm_information.get(
            "keep_alive"
        )
        is not None
    )

    check(
        "LLM optimization configuration regression",
        optimization_config_valid,
    )

    # ==============================================================
    # TEST 7 - CONNECTION FAILURE HANDLING
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 7 - CONNECTION FAILURE HANDLING")

    failure_handled = False

    test_client = LLMClient()

    with patch(
        "backend.llm.generation.llm_client.requests.post"
    ) as mock_post:

        mock_post.side_effect = (
            requests.exceptions.ConnectionError(
                "connection refused"
            )
        )

        try:

            test_client.generate(
                "reliability regression test"
            )

        except RuntimeError as exc:

            failure_handled = (
                "Could not connect to Ollama"
                in str(exc)
            )

            print(
                "Handled failure:",
                exc,
            )

    check(
        "Connection failure regression",
        failure_handled,
    )

    # ==============================================================
    # TEST 8 - TIMEOUT HANDLING
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 8 - TIMEOUT HANDLING")

    timeout_handled = False

    with patch(
        "backend.llm.generation.llm_client.requests.post"
    ) as mock_post:

        mock_post.side_effect = (
            requests.exceptions.Timeout(
                "timeout"
            )
        )

        try:

            test_client.generate(
                "timeout regression test"
            )

        except RuntimeError as exc:

            timeout_handled = (
                "timed out"
                in str(exc).lower()
            )

            print(
                "Handled timeout:",
                exc,
            )

    check(
        "Timeout regression",
        timeout_handled,
    )

    # ==============================================================
    # TEST 9 - REPEATED RETRIEVAL
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 9 - REPEATED RETRIEVAL")

    repeated_retrieval_success = True
    repeated_counts = []

    for _ in range(3):

        try:

            result = retriever.retrieve(
                query=QUERIES[0],
                top_k=TOP_K,
            )

            documents = extract_documents(
                result
            )

            repeated_counts.append(
                len(documents)
            )

            if not documents:

                repeated_retrieval_success = False

        except Exception as exc:

            repeated_retrieval_success = False

            print(
                "Repeated retrieval error:",
                exc,
            )

    print(
        "Retrieved counts:",
        repeated_counts,
    )

    check(
        "Repeated retrieval regression",
        repeated_retrieval_success,
    )

    # ==============================================================
    # TEST 10 - SOURCE FILTERING
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 10 - SOURCE FILTERING")

    source_metadata = (
        retriever.retrieve_metadata(
            query=(
                "failed SSH authentication "
                "brute force attack"
            ),
            top_k=TOP_K,
            source="server-a",
        )
    )

    source_values = [
        item.get("source")
        for item in source_metadata
    ]

    print(
        "Retrieved sources:",
        source_values,
    )

    source_valid = (
        len(source_values) > 0
        and all(
            value == "server-a"
            for value in source_values
        )
    )

    check(
        "Source filtering regression",
        source_valid,
    )

    # ==============================================================
    # TEST 11 - INCREMENTAL INGESTION
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 11 - INCREMENTAL PROCESSING")

    incremental_path = (
        PROJECT_ROOT
        / "data"
        / "incremental_regression_database"
    )

    if incremental_path.exists():

        try:

            shutil.rmtree(
                incremental_path
            )

        except PermissionError:

            pass

    incremental_database = ChromaDatabase(
        persist_directory=incremental_path,
        collection_name="incremental_regression",
    )

    incremental_embeddings = (
        CountingEmbeddingManager()
    )

    incremental_ingestor = (
        SynchronizedLogIngestor(
            database=incremental_database,
            embedding_manager=incremental_embeddings,
            chunk_manager=ChunkManager(),
        )
    )

    record = TestRecord(
        message=(
            "Failed SSH authentication attempt "
            "from 192.168.1.20"
        ),
        source_file="server-a/auth.log",
        event_id="incremental-001",
    )

    first = (
        incremental_ingestor.ingest_source_records(
            source_id="server-a",
            records=[record],
        )
    )

    first_embedding_count = (
        incremental_embeddings.total_chunks_embedded
    )

    second = (
        incremental_ingestor.ingest_source_records(
            source_id="server-a",
            records=[record],
        )
    )

    second_embedding_count = (
        incremental_embeddings.total_chunks_embedded
    )

    incremental_database_count = (
        incremental_database.count()
    )

    print(
        "First ingestion chunks:",
        len(first),
    )

    print(
        "Second ingestion chunks:",
        len(second),
    )

    print(
        "Embeddings after first:",
        first_embedding_count,
    )

    print(
        "Embeddings after second:",
        second_embedding_count,
    )

    print(
        "Final vector count:",
        incremental_database_count,
    )

    incremental_valid = (
        len(first) == 1
        and len(second) == 0
        and first_embedding_count == 1
        and second_embedding_count == 1
        and incremental_database_count == 1
    )

    check(
        "Incremental processing regression",
        incremental_valid,
    )

    # ==============================================================
    # TEST 12 - NEW RECORD AFTER DUPLICATE
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 12 - NEW RECORD AFTER DUPLICATE")

    new_record = TestRecord(
        message=(
            "Suspicious network connection "
            "attempted against port 22"
        ),
        source_file="server-c/network.log",
        event_id="incremental-002",
    )

    before_new = (
        incremental_database.count()
    )

    new_chunks = (
        incremental_ingestor.ingest_source_records(
            source_id="server-c",
            records=[new_record],
        )
    )

    after_new = (
        incremental_database.count()
    )

    print(
        "New chunks:",
        len(new_chunks),
    )

    print(
        "Vector count before:",
        before_new,
    )

    print(
        "Vector count after:",
        after_new,
    )

    new_record_valid = (
        len(new_chunks) == 1
        and after_new == before_new + 1
    )

    check(
        "New-record incremental regression",
        new_record_valid,
    )

    # ==============================================================
    # Close resources
    # ==============================================================

    try:
        incremental_ingestor.close()
    except Exception:
        pass

    try:
        retriever.close()
    except Exception:
        pass

    # ==============================================================
    # RESULTS
    # ==============================================================

    print()
    print("=" * 70)
    print(
        "PERFORMANCE / RELIABILITY REGRESSION RESULTS"
    )
    print("=" * 70)

    print(
        f"Tests passed: {passed}/13"
    )

    print(
        f"Tests failed: {failed}"
    )

    # --------------------------------------------------------------
    # Validation
    # --------------------------------------------------------------

    if failed != 0:

        raise AssertionError(
            "Performance/reliability regression "
            "testing failed."
        )

    if passed != 13:

        raise AssertionError(
            "Expected all 13 regression tests "
            "to pass."
        )

    print()
    print(
        "Performance regression: PASS"
    )

    print(
        "LLM optimization configuration: PASS"
    )

    print(
        "Reliability regression: PASS"
    )

    print(
        "Repeated retrieval regression: PASS"
    )

    print(
        "Source filtering regression: PASS"
    )

    print(
        "Incremental processing regression: PASS"
    )

    print(
        "New-record processing regression: PASS"
    )

    print()
    print("=" * 70)
    print(
        "PERFORMANCE / RELIABILITY REGRESSION PASSED"
    )
    print("=" * 70)

    # ==============================================================
    # Cleanup
    # ==============================================================

    try:

        if DATABASE_PATH.exists():

            shutil.rmtree(
                DATABASE_PATH
            )

            print(
                "Benchmark database cleanup: PASS"
            )

    except PermissionError:

        print(
            "Benchmark database cleanup: SKIPPED "
            "(files still locked by ChromaDB)"
        )

    except Exception as exc:

        print(
            "Benchmark database cleanup: SKIPPED "
            f"({exc})"
        )

    try:

        if incremental_path.exists():

            shutil.rmtree(
                incremental_path
            )

            print(
                "Incremental database cleanup: PASS"
            )

    except PermissionError:

        print(
            "Incremental database cleanup: SKIPPED "
            "(files still locked by ChromaDB)"
        )

    except Exception as exc:

        print(
            "Incremental database cleanup: SKIPPED "
            f"({exc})"
        )

    print("=" * 70)


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    main()