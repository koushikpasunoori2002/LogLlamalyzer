"""
Full regression evaluation.

Validates the major LogLlamalyzer components after the latest
retrieval, security, performance, API, frontend, and
incremental-processing changes.

The regression suite covers:

- database setup
- embedding generation
- chunking
- basic retrieval
- source filtering
- security classification
- severity preservation
- multi-source retrieval
- distance threshold
- context construction
- security analysis
- Retriever API compatibility
- API integration
- query-only API compatibility
- API input validation
- health endpoints
- source leak prevention
"""

from pathlib import Path
import shutil
import sys
from unittest.mock import patch


# ------------------------------------------------------------------
# Project root
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

from fastapi.testclient import TestClient

from backend.api.app import app
from backend.api.schemas import AnalyzeRequest, AnalyzeResponse

from backend.database.chroma import ChromaDatabase
from backend.llm.embeddings import EmbeddingManager
from backend.rag.chunking import ChunkManager
from backend.rag.retriever import Retriever
from backend.rag.context import ContextBuilder
from backend.llm.generation import RAGAnalyzer


# ------------------------------------------------------------------
# Test paths
# ------------------------------------------------------------------

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "full_regression_test"
)

KNOWLEDGE_DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "full_regression_knowledge_test"
)

COLLECTION_NAME = (
    "full_regression"
)

KNOWLEDGE_COLLECTION_NAME = (
    "full_regression_knowledge"
)


# ------------------------------------------------------------------
# Regression documents
# ------------------------------------------------------------------

DOCUMENTS = [
    (
        "Multiple failed SSH authentication attempts were "
        "detected from a remote IP address. Repeated password "
        "failures may indicate an SSH brute force attack."
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
    (
        "The Apache web server started successfully and is "
        "operating normally."
    ),
]


# ------------------------------------------------------------------
# IDs
# ------------------------------------------------------------------

IDS = [
    "full_regression_001",
    "full_regression_002",
    "full_regression_003",
    "full_regression_004",
    "full_regression_005",
    "full_regression_006",
]


# ------------------------------------------------------------------
# Metadata
# ------------------------------------------------------------------

METADATAS = [
    {
        "source": "server-a",
        "synchronized_source": "server-a",
        "scenario": "ssh_brute_force",
        "classification": "ssh_brute_force",
        "severity": "HIGH",
        "log_type": "auth",
    },
    {
        "source": "server-b",
        "synchronized_source": "server-b",
        "scenario": "credential_attack",
        "classification": "credential_attack",
        "severity": "MEDIUM",
        "log_type": "auth",
    },
    {
        "source": "server-b",
        "synchronized_source": "server-b",
        "scenario": "privilege_escalation",
        "classification": "privilege_escalation",
        "severity": "HIGH",
        "log_type": "auth",
    },
    {
        "source": "server-c",
        "synchronized_source": "server-c",
        "scenario": "malware",
        "classification": "malware",
        "severity": "HIGH",
        "log_type": "syslog",
    },
    {
        "source": "server-c",
        "synchronized_source": "server-c",
        "scenario": "network_scanning",
        "classification": "network_scanning",
        "severity": "HIGH",
        "log_type": "syslog",
    },
    {
        "source": "server-a",
        "synchronized_source": "server-a",
        "scenario": "normal_web_server",
        "classification": "normal",
        "severity": "INFO",
        "log_type": "apache",
    },
]


# ------------------------------------------------------------------
# Database creation
# ------------------------------------------------------------------

def create_database():

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
        EmbeddingManager()
    )

    embeddings = (
        embedding_manager.embed_texts(
            DOCUMENTS
        )
    )

    database.add(
        ids=IDS,
        embeddings=embeddings,
        documents=DOCUMENTS,
        metadatas=METADATAS,
    )

    if database.count() != len(
        DOCUMENTS
    ):

        raise AssertionError(
            "Regression database setup failed."
        )

    return (
        database,
        embedding_manager,
    )


# ------------------------------------------------------------------
# Validation retriever
# ------------------------------------------------------------------

class ValidationRetriever:
    """
    Wrapper used for API regression checks.

    It shares the controlled database but does not close the
    shared database when the endpoint calls close().
    """

    def __init__(
        self,
        database,
        embedding_manager,
        top_k=3,
        distance_threshold=0.98,
    ):

        self._retriever = Retriever(
            database=database,
            embedding_manager=embedding_manager,
            top_k=top_k,
            distance_threshold=distance_threshold,
        )

    def retrieve(
        self,
        query,
        top_k=None,
        source=None,
    ):

        return self._retriever.retrieve(
            query=query,
            top_k=top_k,
            source=source,
        )

    def retrieve_documents(
        self,
        query,
        top_k=None,
        source=None,
    ):

        return self._retriever.retrieve_documents(
            query=query,
            top_k=top_k,
            source=source,
        )

    def retrieve_metadata(
        self,
        query,
        top_k=None,
        source=None,
    ):

        return self._retriever.retrieve_metadata(
            query=query,
            top_k=top_k,
            source=source,
        )

    def retrieve_with_scores(
        self,
        query,
        top_k=None,
        source=None,
    ):

        return self._retriever.retrieve_with_scores(
            query=query,
            top_k=top_k,
            source=source,
        )

    def count(self):

        return self._retriever.count()

    def info(self):

        return self._retriever.info()

    def close(self):

        return None


# ------------------------------------------------------------------
# Main regression evaluation
# ------------------------------------------------------------------

def main():

    print("=" * 70)
    print(
        "FULL REGRESSION EVALUATION"
    )
    print("=" * 70)

    passed = 0
    failed = 0

    # --------------------------------------------------------------
    # Check helper
    # --------------------------------------------------------------

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
    # Create database
    # --------------------------------------------------------------

    print()
    print(
        "Preparing regression database..."
    )

    database, embedding_manager = (
        create_database()
    )

    print(
        "Records stored:",
        database.count(),
    )

    check(
        "Database regression setup",
        database.count()
        == len(DOCUMENTS),
    )

    # --------------------------------------------------------------
    # Shared retriever
    # --------------------------------------------------------------

    retriever = Retriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=3,
        distance_threshold=0.98,
    )

    # ==============================================================
    # TEST 1 - EMBEDDING GENERATION
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 1 - EMBEDDING GENERATION"
    )

    embeddings = (
        embedding_manager.embed_texts(
            [
                "failed SSH authentication"
            ]
        )
    )

    embedding_valid = (
        embeddings is not None
        and len(embeddings) == 1
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
    # TEST 2 - CHUNKING
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 2 - CHUNKING"
    )

    chunk_manager = ChunkManager()

    chunks = (
        chunk_manager.add_text(
            text=DOCUMENTS[0],
            source="server-a",
            metadata={
                "source": "server-a"
            },
        )
    )

    print(
        "Chunks created:",
        len(chunks),
    )

    chunking_valid = (
        len(chunks) > 0
        and all(
            hasattr(
                chunk,
                "chunk_id",
            )
            and hasattr(
                chunk,
                "text",
            )
            for chunk in chunks
        )
    )

    check(
        "Chunking regression",
        chunking_valid,
    )

    # ==============================================================
    # TEST 3 - BASIC RETRIEVAL
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 3 - BASIC RETRIEVAL"
    )

    results = retriever.retrieve(
        query=(
            "failed SSH authentication "
            "brute force attack"
        ),
        top_k=3,
    )

    retrieved_documents = (
        results.get(
            "documents",
            [],
        )
    )

    if retrieved_documents:

        retrieved_documents = (
            retrieved_documents[0]
        )

    else:

        retrieved_documents = []

    print(
        "Documents retrieved:",
        len(retrieved_documents),
    )

    check(
        "Basic retrieval regression",
        len(retrieved_documents) > 0,
    )

    # ==============================================================
    # TEST 4 - SOURCE FILTERING
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 4 - SOURCE FILTERING"
    )

    source_metadata = (
        retriever.retrieve_metadata(
            query=(
                "failed SSH authentication "
                "brute force"
            ),
            top_k=3,
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

    source_filter_valid = (
        len(source_values) > 0
        and all(
            source == "server-a"
            for source in source_values
        )
    )

    check(
        "Source filtering regression",
        source_filter_valid,
    )

    # ==============================================================
    # TEST 5 - CLASSIFICATION PRESERVATION
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 5 - CLASSIFICATION PRESERVATION"
    )

    privilege_metadata = (
        retriever.retrieve_metadata(
            query=(
                "suspicious sudo "
                "privilege escalation"
            ),
            top_k=3,
        )
    )

    classifications = [
        item.get("classification")
        for item in privilege_metadata
    ]

    print(
        "Classifications:",
        classifications,
    )

    classification_valid = (
        "privilege_escalation"
        in classifications
    )

    check(
        "Security classification regression",
        classification_valid,
    )

    # ==============================================================
    # TEST 6 - SEVERITY PRESERVATION
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 6 - SEVERITY PRESERVATION"
    )

    malware_metadata = (
        retriever.retrieve_metadata(
            query=(
                "suspicious executable "
                "malware execution"
            ),
            top_k=3,
        )
    )

    severities = [
        item.get("severity")
        for item in malware_metadata
    ]

    print(
        "Severities:",
        severities,
    )

    severity_valid = (
        "HIGH"
        in severities
    )

    check(
        "Severity preservation regression",
        severity_valid,
    )

    # ==============================================================
    # TEST 7 - MULTI-SOURCE RETRIEVAL
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 7 - MULTI-SOURCE RETRIEVAL"
    )

    multi_source_queries = [
        "failed authentication activity",
        "suspicious system security activity",
        "network scanning suspicious connections",
    ]

    observed_sources = set()

    for query in multi_source_queries:

        metadata = (
            retriever.retrieve_metadata(
                query=query,
                top_k=6,
            )
        )

        sources = [
            item.get("source")
            for item in metadata
            if item.get("source")
        ]

        observed_sources.update(
            sources
        )

        print(
            f"Query: {query}"
        )

        print(
            "Sources:",
            sources,
        )

    print(
        "Observed sources:",
        sorted(
            observed_sources
        ),
    )

    multi_source_valid = (
        {
            "server-a",
            "server-b",
            "server-c",
        }.issubset(
            observed_sources
        )
    )

    check(
        "Multi-source retrieval regression",
        multi_source_valid,
    )

    # ==============================================================
    # TEST 8 - DISTANCE THRESHOLD
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 8 - DISTANCE THRESHOLD"
    )

    scored_results = (
        retriever.retrieve_with_scores(
            query=(
                "failed SSH authentication "
                "brute force"
            ),
            top_k=3,
        )
    )

    distances = [
        float(
            item["distance"]
        )
        for item in scored_results
        if (
            isinstance(
                item,
                dict,
            )
            and item.get(
                "distance"
            ) is not None
        )
    ]

    print(
        "Distances:",
        distances,
    )

    distance_valid = (
        len(distances) > 0
        and all(
            distance
            <= 0.98 + 1e-6
            for distance in distances
        )
    )

    check(
        "Distance threshold regression",
        distance_valid,
    )

    # ==============================================================
    # TEST 9 - CONTEXT CONSTRUCTION
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 9 - CONTEXT CONSTRUCTION"
    )

    context_builder = (
        ContextBuilder(
            log_retriever=retriever,
            knowledge_retriever=None,
            top_k_logs=3,
            top_k_knowledge=3,
        )
    )

    context = (
        context_builder.build(
            "failed SSH authentication"
        )
    )

    log_count = (
        context.log_count()
    )

    print(
        "Log results in context:",
        log_count,
    )

    context_valid = (
        log_count > 0
    )

    check(
        "Context construction regression",
        context_valid,
    )

    # ==============================================================
    # TEST 10 - SECURITY ANALYSIS
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 10 - SECURITY ANALYSIS"
    )

    analysis_valid = False

    try:

        analyzer = RAGAnalyzer()

        analysis_response = (
            analyzer.analyze(
                context
            )
        )

        answer = getattr(
            analysis_response,
            "answer",
            "",
        )

        analysis_valid = (
            isinstance(
                answer,
                str,
            )
            and bool(
                answer.strip()
            )
        )

        print(
            "Analysis generated:",
            analysis_valid,
        )

    except Exception as exc:

        print(
            "Analysis error:",
            exc,
        )

    check(
        "Security analysis regression",
        analysis_valid,
    )

    # ==============================================================
    # TEST 11 - RETRIEVER API COMPATIBILITY
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 11 - RETRIEVER API COMPATIBILITY"
    )

    api_query = (
        "failed SSH authentication"
    )

    api_results = (
        retriever.retrieve(
            query=api_query,
            top_k=3,
        )
    )

    api_documents = (
        retriever.retrieve_documents(
            query=api_query,
            top_k=3,
        )
    )

    api_metadata = (
        retriever.retrieve_metadata(
            query=api_query,
            top_k=3,
        )
    )

    api_scores = (
        retriever.retrieve_with_scores(
            query=api_query,
            top_k=3,
        )
    )

    api_valid = (
        bool(api_results)
        and len(api_documents) > 0
        and len(api_metadata) > 0
        and len(api_scores) > 0
    )

    print(
        "retrieve():",
        bool(api_results),
    )

    print(
        "retrieve_documents():",
        len(api_documents),
    )

    print(
        "retrieve_metadata():",
        len(api_metadata),
    )

    print(
        "retrieve_with_scores():",
        len(api_scores),
    )

    check(
        "Retriever API regression",
        api_valid,
    )

    # ==============================================================
    # API SETUP
    # ==============================================================

    client = TestClient(
        app
    )

    globals_embedding_manager = (
        embedding_manager
    )

    def api_database_factory(
        collection_name="log_embeddings",
        persist_directory=None,
    ):

        if collection_name == (
            "knowledge_embeddings"
        ):

            KNOWLEDGE_DATABASE_PATH.mkdir(
                parents=True,
                exist_ok=True,
            )

            return ChromaDatabase(
                persist_directory=(
                    KNOWLEDGE_DATABASE_PATH
                ),
                collection_name=(
                    KNOWLEDGE_COLLECTION_NAME
                ),
            )

        return database

    def api_retriever_factory(
        database=None,
        embedding_manager=None,
        top_k=3,
        distance_threshold=0.98,
    ):

        return ValidationRetriever(
            database=database,
            embedding_manager=(
                embedding_manager
                if embedding_manager is not None
                else globals_embedding_manager
            ),
            top_k=top_k,
            distance_threshold=(
                distance_threshold
            ),
        )

    # ==============================================================
    # TEST 12 - API INTEGRATION
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 12 - API INTEGRATION"
    )

    api_integration_valid = False

    try:

        with patch(
            "backend.api.endpoints.ChromaDatabase",
            side_effect=api_database_factory,
        ), patch(
            "backend.api.endpoints.Retriever",
            side_effect=api_retriever_factory,
        ):

            response = client.post(
                "/analyze",
                json={
                    "query": (
                        "failed SSH authentication "
                        "brute force attack"
                    ),
                    "source": "server-a",
                },
            )

        data = response.json()

        print(
            "HTTP status:",
            response.status_code,
        )

        print(
            "Returned source:",
            data.get("source"),
        )

        print(
            "Metadata:",
            data.get("metadata"),
        )

        api_integration_valid = (
            response.status_code == 200
            and data.get(
                "source"
            )
            == "server-a"
            and isinstance(
                data.get(
                    "answer"
                ),
                str,
            )
            and bool(
                data.get(
                    "answer",
                    "",
                ).strip()
            )
            and "server-a"
            in data.get(
                "metadata",
                {},
            ).get(
                "sources",
                [],
            )
            and data.get(
                "metadata",
                {},
            ).get(
                "log_results",
                0,
            ) > 0
        )

    except Exception as exc:

        print(
            "API integration error:",
            exc,
        )

    check(
        "API integration regression",
        api_integration_valid,
    )

    # ==============================================================
    # TEST 13 - QUERY-ONLY API
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 13 - QUERY-ONLY API COMPATIBILITY"
    )

    query_only_valid = False

    try:

        with patch(
            "backend.api.endpoints.ChromaDatabase",
            side_effect=api_database_factory,
        ), patch(
            "backend.api.endpoints.Retriever",
            side_effect=api_retriever_factory,
        ):

            response = client.post(
                "/analyze",
                json={
                    "query": (
                        "suspicious sudo "
                        "privilege escalation"
                    )
                },
            )

        data = response.json()

        print(
            "HTTP status:",
            response.status_code,
        )

        print(
            "Source:",
            data.get("source"),
        )

        query_only_valid = (
            response.status_code == 200
            and data.get(
                "source"
            ) is None
            and isinstance(
                data.get(
                    "answer"
                ),
                str,
            )
            and bool(
                data.get(
                    "answer",
                    "",
                ).strip()
            )
        )

    except Exception as exc:

        print(
            "Query-only API error:",
            exc,
        )

    check(
        "Query-only API regression",
        query_only_valid,
    )

    # ==============================================================
    # TEST 14 - API INPUT VALIDATION
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 14 - API INPUT VALIDATION"
    )

    empty_query_response = (
        client.post(
            "/analyze",
            json={
                "query": "   "
            },
        )
    )

    empty_source_response = (
        client.post(
            "/analyze",
            json={
                "query": "test",
                "source": "   ",
            },
        )
    )

    missing_query_response = (
        client.post(
            "/analyze",
            json={},
        )
    )

    print(
        "Empty query status:",
        empty_query_response.status_code,
    )

    print(
        "Empty source status:",
        empty_source_response.status_code,
    )

    print(
        "Missing query status:",
        missing_query_response.status_code,
    )

    api_validation_valid = (
        empty_query_response.status_code == 400
        and empty_source_response.status_code == 400
        and missing_query_response.status_code == 422
    )

    check(
        "API input validation regression",
        api_validation_valid,
    )

    # ==============================================================
    # TEST 15 - HEALTH ENDPOINTS
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 15 - HEALTH ENDPOINTS"
    )

    root_response = (
        client.get("/")
    )

    health_response = (
        client.get("/health")
    )

    status_response = (
        client.get("/status")
    )

    print(
        "Root status:",
        root_response.status_code,
    )

    print(
        "Health status:",
        health_response.status_code,
    )

    print(
        "Status endpoint status:",
        status_response.status_code,
    )

    health_valid = (
        root_response.status_code == 200
        and health_response.status_code == 200
        and status_response.status_code == 200
        and health_response.json().get(
            "status"
        )
        == "healthy"
        and status_response.json().get(
            "status"
        )
        == "operational"
    )

    check(
        "Health endpoint regression",
        health_valid,
    )

    # ==============================================================
    # TEST 16 - SOURCE LEAK PREVENTION
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 16 - SOURCE LEAK PREVENTION"
    )

    leak_free = True

    # Use queries that are strongly associated with each source.
    source_cases = [
        (
            "server-a",
            "failed SSH authentication brute force attack",
        ),
        (
            "server-b",
            "sudo privilege escalation elevated privileges",
        ),
        (
            "server-c",
            "network scanning suspicious connections ports",
        ),
    ]

    for source, query in source_cases:

        validation_retriever = (
            ValidationRetriever(
                database=database,
                embedding_manager=embedding_manager,
                top_k=3,
                distance_threshold=None,
            )
        )

        metadata = (
            validation_retriever.retrieve_metadata(
                query=query,
                top_k=3,
                source=source,
            )
        )

        sources = [
            item.get("source")
            for item in metadata
        ]

        print(
            f"{source}:",
            sources,
        )

        # A filtered result must never contain another source.
        #
        # Empty results are allowed here because source filtering
        # itself is the behaviour being tested. The test only fails
        # when evidence is returned from the wrong source.
        wrong_source_found = any(
            value != source
            for value in sources
            if value is not None
        )

        if wrong_source_found:

            leak_free = False

    check(
        "Source leak prevention regression",
        leak_free,
    )

    # --------------------------------------------------------------
    # Close database after all checks
    # --------------------------------------------------------------

    try:

        database.close()

    except Exception:

        pass

    # --------------------------------------------------------------
    # Results
    # --------------------------------------------------------------

    print()
    print("=" * 70)
    print(
        "FULL REGRESSION RESULTS"
    )
    print("=" * 70)

    print(
        f"Regression checks passed: "
        f"{passed}/17"
    )

    print(
        f"Regression checks failed: "
        f"{failed}"
    )

    # --------------------------------------------------------------
    # Validation
    # --------------------------------------------------------------

    if failed != 0:

        raise AssertionError(
            "Full regression validation failed."
        )

    if passed != 17:

        raise AssertionError(
            "Expected all 17 regression checks "
            "to pass."
        )

    print()
    print(
        "Database regression: PASS"
    )

    print(
        "Embedding regression: PASS"
    )

    print(
        "Chunking regression: PASS"
    )

    print(
        "Retrieval regression: PASS"
    )

    print(
        "Source filtering regression: PASS"
    )

    print(
        "Security classification regression: PASS"
    )

    print(
        "Severity preservation regression: PASS"
    )

    print(
        "Multi-source regression: PASS"
    )

    print(
        "Distance threshold regression: PASS"
    )

    print(
        "Context regression: PASS"
    )

    print(
        "Security analysis regression: PASS"
    )

    print(
        "Retriever API regression: PASS"
    )

    print(
        "API integration regression: PASS"
    )

    print(
        "Query-only API regression: PASS"
    )

    print(
        "API validation regression: PASS"
    )

    print(
        "Health endpoint regression: PASS"
    )

    print(
        "Source leak prevention: PASS"
    )

    print()
    print("=" * 70)
    print(
        "FULL REGRESSION VALIDATION PASSED"
    )
    print("=" * 70)

    # --------------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------------

    try:

        if DATABASE_PATH.exists():

            shutil.rmtree(
                DATABASE_PATH
            )

            print(
                "Database cleanup: PASS"
            )

    except PermissionError:

        print(
            "Database cleanup: SKIPPED "
            "(files still locked by ChromaDB)"
        )

    except Exception as exc:

        print(
            "Database cleanup: SKIPPED "
            f"({exc})"
        )

    try:

        if KNOWLEDGE_DATABASE_PATH.exists():

            shutil.rmtree(
                KNOWLEDGE_DATABASE_PATH
            )

    except Exception:

        pass

    print("=" * 70)


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    main()