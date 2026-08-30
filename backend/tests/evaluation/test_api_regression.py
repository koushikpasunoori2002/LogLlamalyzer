"""
API regression evaluation.

Validates that the existing LogLlamalyzer API remains stable
after multi-source API integration and response enhancement.

The regression suite covers:

- root endpoint
- health endpoint
- status endpoint
- query-only analysis
- source-filtered analysis
- response schema
- response metadata
- empty query validation
- empty source validation
- missing query validation
- source isolation
"""

from pathlib import Path
import shutil
import sys
from unittest.mock import patch


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

from fastapi.testclient import TestClient

from backend.api.app import app
from backend.api.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
)

from backend.database.chroma import ChromaDatabase
from backend.llm.embeddings import EmbeddingManager
from backend.rag.retriever import Retriever


# ------------------------------------------------------------------
# Test database paths
# ------------------------------------------------------------------

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "api_regression_test"
)

KNOWLEDGE_DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "api_regression_knowledge_test"
)

COLLECTION_NAME = (
    "api_regression_test"
)

KNOWLEDGE_COLLECTION_NAME = (
    "empty_knowledge"
)


# ------------------------------------------------------------------
# Controlled documents
# ------------------------------------------------------------------

DOCUMENTS = [
    (
        "Server A recorded repeated failed SSH "
        "authentication attempts from a remote IP address."
    ),
    (
        "Server A detected a brute force password "
        "attack against the SSH service."
    ),
    (
        "Server B recorded suspicious sudo activity "
        "used to obtain elevated privileges."
    ),
    (
        "Server B detected a possible privilege "
        "escalation attempt."
    ),
    (
        "Server C recorded repeated connections "
        "against multiple network ports."
    ),
    (
        "Server C detected possible network scanning "
        "and reconnaissance activity."
    ),
]


# ------------------------------------------------------------------
# IDs
# ------------------------------------------------------------------

IDS = [
    "api_regression_001",
    "api_regression_002",
    "api_regression_003",
    "api_regression_004",
    "api_regression_005",
    "api_regression_006",
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
        "source": "server-a",
        "synchronized_source": "server-a",
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
        "scenario": "network_scanning",
        "classification": "network_scanning",
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
]


# ------------------------------------------------------------------
# Controlled database
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
            "API regression database setup failed."
        )

    return (
        database,
        embedding_manager,
    )


# ------------------------------------------------------------------
# Validation Retriever
# ------------------------------------------------------------------

class ValidationRetriever:
    """
    Fresh Retriever wrapper used for every API request.

    The underlying Retriever uses the shared controlled database.

    close() is intentionally a no-op because the endpoint normally
    closes its Retriever at the end of each request, while the
    regression test needs the benchmark database for subsequent
    requests.
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
# Main
# ------------------------------------------------------------------

def main():

    print("=" * 70)
    print(
        "API REGRESSION VALIDATION"
    )
    print("=" * 70)

    passed = 0
    failed = 0

    # --------------------------------------------------------------
    # Assertion helper
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
    # Create controlled database
    # --------------------------------------------------------------

    print()
    print(
        "Creating controlled regression database..."
    )

    database, embedding_manager = (
        create_database()
    )

    print(
        "Records stored:",
        database.count(),
    )

    print(
        "Database setup: PASS"
    )

    # --------------------------------------------------------------
    # API client
    # --------------------------------------------------------------

    client = TestClient(
        app
    )

    # --------------------------------------------------------------
    # API database factory
    # --------------------------------------------------------------

    def database_factory(
        collection_name="log_embeddings",
        persist_directory=None,
    ):
        """
        Route API log access to the controlled database.

        Knowledge access uses a separate empty collection.
        """

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

    # --------------------------------------------------------------
    # API Retriever factory
    # --------------------------------------------------------------

    def retriever_factory(
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
            distance_threshold=distance_threshold,
        )

    globals_embedding_manager = (
        embedding_manager
    )

    # ==============================================================
    # TEST 1 - ROOT ENDPOINT
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 1 - ROOT ENDPOINT")

    response = client.get(
        "/"
    )

    print(
        "HTTP status:",
        response.status_code,
    )

    print(
        "Response:",
        response.json(),
    )

    root_valid = (
        response.status_code == 200
        and response.json().get(
            "application"
        )
        == "LogLlamalyzer"
        and response.json().get(
            "status"
        )
        == "running"
    )

    check(
        "Root endpoint regression",
        root_valid,
    )

    # ==============================================================
    # TEST 2 - HEALTH ENDPOINT
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 2 - HEALTH ENDPOINT")

    response = client.get(
        "/health"
    )

    print(
        "HTTP status:",
        response.status_code,
    )

    print(
        "Response:",
        response.json(),
    )

    health_valid = (
        response.status_code == 200
        and response.json().get(
            "status"
        )
        == "healthy"
    )

    check(
        "Health endpoint regression",
        health_valid,
    )

    # ==============================================================
    # TEST 3 - STATUS ENDPOINT
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 3 - STATUS ENDPOINT")

    response = client.get(
        "/status"
    )

    print(
        "HTTP status:",
        response.status_code,
    )

    print(
        "Response:",
        response.json(),
    )

    status_valid = (
        response.status_code == 200
        and response.json().get(
            "application"
        )
        == "LogLlamalyzer"
        and response.json().get(
            "status"
        )
        == "operational"
    )

    check(
        "Status endpoint regression",
        status_valid,
    )

    # ==============================================================
    # TEST 4 - REQUEST SCHEMA
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 4 - REQUEST SCHEMA")

    request_fields = set(
        AnalyzeRequest.model_fields.keys()
    )

    print(
        "AnalyzeRequest fields:",
        sorted(request_fields),
    )

    request_schema_valid = (
        request_fields
        == {
            "query",
            "source",
        }
    )

    check(
        "Request schema regression",
        request_schema_valid,
    )

    # ==============================================================
    # TEST 5 - RESPONSE SCHEMA
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 5 - RESPONSE SCHEMA")

    response_fields = set(
        AnalyzeResponse.model_fields.keys()
    )

    print(
        "AnalyzeResponse fields:",
        sorted(response_fields),
    )

    response_schema_valid = (
        response_fields
        == {
            "query",
            "answer",
            "source",
            "metadata",
        }
    )

    check(
        "Response schema regression",
        response_schema_valid,
    )

    # ==============================================================
    # TEST 6 - QUERY-ONLY ANALYSIS
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 6 - QUERY-ONLY ANALYSIS")

    with patch(
        "backend.api.endpoints.ChromaDatabase",
        side_effect=database_factory,
    ), patch(
        "backend.api.endpoints.Retriever",
        side_effect=retriever_factory,
    ):

        response = client.post(
            "/analyze",
            json={
                "query": (
                    "failed SSH authentication "
                    "brute force attack"
                )
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

    query_only_valid = (
        response.status_code == 200
        and isinstance(
            data.get("answer"),
            str,
        )
        and bool(
            data.get(
                "answer",
                "",
            ).strip()
        )
        and data.get(
            "source"
        ) is None
        and data.get(
            "metadata",
            {},
        ).get(
            "log_results",
            0,
        ) > 0
    )

    check(
        "Query-only analysis regression",
        query_only_valid,
    )

    # ==============================================================
    # TEST 7 - SOURCE-A ANALYSIS
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 7 - SOURCE-A ANALYSIS")

    with patch(
        "backend.api.endpoints.ChromaDatabase",
        side_effect=database_factory,
    ), patch(
        "backend.api.endpoints.Retriever",
        side_effect=retriever_factory,
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
        "Source:",
        data.get("source"),
    )

    print(
        "Metadata:",
        data.get("metadata"),
    )

    source_a_valid = (
        response.status_code == 200
        and data.get(
            "source"
        )
        == "server-a"
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

    check(
        "Server-A analysis regression",
        source_a_valid,
    )

    # ==============================================================
    # TEST 8 - SOURCE-B ANALYSIS
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 8 - SOURCE-B ANALYSIS")

    with patch(
        "backend.api.endpoints.ChromaDatabase",
        side_effect=database_factory,
    ), patch(
        "backend.api.endpoints.Retriever",
        side_effect=retriever_factory,
    ):

        response = client.post(
            "/analyze",
            json={
                "query": (
                    "suspicious sudo "
                    "privilege escalation"
                ),
                "source": "server-b",
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

    print(
        "Metadata:",
        data.get("metadata"),
    )

    source_b_valid = (
        response.status_code == 200
        and data.get(
            "source"
        )
        == "server-b"
        and "server-b"
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

    check(
        "Server-B analysis regression",
        source_b_valid,
    )

    # ==============================================================
    # TEST 9 - SOURCE-C ANALYSIS
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 9 - SOURCE-C ANALYSIS")

    with patch(
        "backend.api.endpoints.ChromaDatabase",
        side_effect=database_factory,
    ), patch(
        "backend.api.endpoints.Retriever",
        side_effect=retriever_factory,
    ):

        response = client.post(
            "/analyze",
            json={
                "query": (
                    "network scanning "
                    "suspicious connections"
                ),
                "source": "server-c",
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

    print(
        "Metadata:",
        data.get("metadata"),
    )

    source_c_valid = (
        response.status_code == 200
        and data.get(
            "source"
        )
        == "server-c"
        and "server-c"
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

    check(
        "Server-C analysis regression",
        source_c_valid,
    )

    # ==============================================================
    # TEST 10 - EMPTY QUERY
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 10 - EMPTY QUERY VALIDATION")

    response = client.post(
        "/analyze",
        json={
            "query": "   "
        },
    )

    print(
        "HTTP status:",
        response.status_code,
    )

    print(
        "Response:",
        response.json(),
    )

    empty_query_valid = (
        response.status_code == 400
    )

    check(
        "Empty query regression",
        empty_query_valid,
    )

    # ==============================================================
    # TEST 11 - EMPTY SOURCE
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 11 - EMPTY SOURCE VALIDATION")

    response = client.post(
        "/analyze",
        json={
            "query": (
                "failed SSH authentication"
            ),
            "source": "   ",
        },
    )

    print(
        "HTTP status:",
        response.status_code,
    )

    print(
        "Response:",
        response.json(),
    )

    empty_source_valid = (
        response.status_code == 400
    )

    check(
        "Empty source regression",
        empty_source_valid,
    )

    # ==============================================================
    # TEST 12 - MISSING QUERY
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 12 - MISSING QUERY VALIDATION")

    response = client.post(
        "/analyze",
        json={},
    )

    print(
        "HTTP status:",
        response.status_code,
    )

    missing_query_valid = (
        response.status_code == 422
    )

    check(
        "Missing query regression",
        missing_query_valid,
    )

    # ==============================================================
    # TEST 13 - UNKNOWN SOURCE
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 13 - UNKNOWN SOURCE BEHAVIOUR")

    with patch(
        "backend.api.endpoints.ChromaDatabase",
        side_effect=database_factory,
    ), patch(
        "backend.api.endpoints.Retriever",
        side_effect=retriever_factory,
    ):

        response = client.post(
            "/analyze",
            json={
                "query": (
                    "failed SSH authentication"
                ),
                "source": "server-unknown",
            },
        )

    print(
        "HTTP status:",
        response.status_code,
    )

    print(
        "Response source:",
        response.json().get(
            "source"
        ),
    )

    # The current API treats the source as a metadata
    # filter. An unknown source therefore results in a
    # valid request with no matching log evidence.
    unknown_source_data = (
        response.json()
    )

    unknown_source_valid = (
        response.status_code == 200
        and unknown_source_data.get(
            "source"
        )
        == "server-unknown"
        and unknown_source_data.get(
            "metadata",
            {},
        ).get(
            "log_results",
            0,
        )
        == 0
    )

    check(
        "Unknown source regression",
        unknown_source_valid,
    )

    # ==============================================================
    # TEST 14 - SOURCE ISOLATION
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 14 - SOURCE ISOLATION")

    isolation_cases = [
        (
            "server-a",
            "failed SSH authentication",
        ),
        (
            "server-b",
            "privilege escalation",
        ),
        (
            "server-c",
            "network scanning",
        ),
    ]

    isolation_valid = True

    for source, query in isolation_cases:

        validation_retriever = (
            ValidationRetriever(
                database=database,
                embedding_manager=embedding_manager,
                top_k=3,
                distance_threshold=0.98,
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

        if (
            not sources
            or any(
                value != source
                for value in sources
            )
        ):

            isolation_valid = False

    check(
        "Source isolation regression",
        isolation_valid,
    )

    # ==============================================================
    # TEST 15 - RESPONSE METADATA STRUCTURE
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 15 - RESPONSE METADATA STRUCTURE")

    with patch(
        "backend.api.endpoints.ChromaDatabase",
        side_effect=database_factory,
    ), patch(
        "backend.api.endpoints.Retriever",
        side_effect=retriever_factory,
    ):

        response = client.post(
            "/analyze",
            json={
                "query": (
                    "failed SSH authentication"
                ),
                "source": "server-a",
            },
        )

    data = response.json()

    metadata = data.get(
        "metadata",
        {},
    )

    metadata_structure_valid = (
        response.status_code == 200
        and isinstance(
            metadata,
            dict,
        )
        and isinstance(
            metadata.get(
                "sources"
            ),
            list,
        )
        and isinstance(
            metadata.get(
                "log_results"
            ),
            int,
        )
        and isinstance(
            metadata.get(
                "knowledge_results"
            ),
            int,
        )
    )

    print(
        "Metadata structure:",
        metadata,
    )

    check(
        "Response metadata structure regression",
        metadata_structure_valid,
    )

    # ==============================================================
    # Results
    # ==============================================================

    print()
    print("=" * 70)
    print(
        "API REGRESSION RESULTS"
    )
    print("=" * 70)

    print(
        f"Regression checks passed: "
        f"{passed}/15"
    )

    print(
        f"Regression checks failed: "
        f"{failed}"
    )

    # ==============================================================
    # Validation
    # ==============================================================

    if failed != 0:

        raise AssertionError(
            "API regression validation failed."
        )

    if passed != 15:

        raise AssertionError(
            "Expected all 15 API regression checks "
            "to pass."
        )

    print()
    print(
        "Root endpoint regression: PASS"
    )

    print(
        "Health endpoint regression: PASS"
    )

    print(
        "Status endpoint regression: PASS"
    )

    print(
        "Request schema regression: PASS"
    )

    print(
        "Response schema regression: PASS"
    )

    print(
        "Query-only analysis regression: PASS"
    )

    print(
        "Source-aware analysis regression: PASS"
    )

    print(
        "Input validation regression: PASS"
    )

    print(
        "Source isolation regression: PASS"
    )

    print(
        "Response metadata regression: PASS"
    )

    print()
    print("=" * 70)
    print(
        "API REGRESSION VALIDATION PASSED"
    )
    print("=" * 70)

    # --------------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------------

    try:

        database.close()

    except Exception:

        pass

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