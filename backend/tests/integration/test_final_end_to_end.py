"""
Final end-to-end system integration test.

Validates the complete LogLlamalyzer pipeline:

    Controlled log records
        ↓
    Embeddings
        ↓
    ChromaDB
        ↓
    Source-aware Retriever
        ↓
    RAG Context
        ↓
    LLM Analysis
        ↓
    FastAPI /analyze
        ↓
    API response with source and metadata

The integration test validates:

- database setup
- direct source-aware retrieval
- query-only API analysis
- server-a API analysis
- server-b API analysis
- server-c API analysis
- response schema
- source isolation
- unrestricted multi-source retrieval
- evidence metadata
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
from backend.api.schemas import AnalyzeResponse

from backend.database.chroma import ChromaDatabase
from backend.llm.embeddings import EmbeddingManager
from backend.rag.retriever import Retriever


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "final_end_to_end_test"
)

KNOWLEDGE_DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "final_end_to_end_knowledge_test"
)

COLLECTION_NAME = (
    "final_end_to_end"
)

KNOWLEDGE_COLLECTION_NAME = (
    "empty_knowledge"
)


# ------------------------------------------------------------------
# Controlled documents
# ------------------------------------------------------------------

DOCUMENTS = [
    (
        "Server A recorded multiple failed SSH "
        "authentication attempts from a remote IP address. "
        "The repeated password failures indicate a possible "
        "SSH brute force attack."
    ),
    (
        "Server A recorded repeated failed login attempts "
        "against the same account. The activity may indicate "
        "a credential attack."
    ),
    (
        "Server B recorded suspicious sudo commands used "
        "to obtain elevated privileges. This may indicate "
        "privilege escalation activity."
    ),
    (
        "Server B recorded elevated privilege activity "
        "that should be investigated for possible abuse."
    ),
    (
        "Server C recorded repeated connections to different "
        "network ports. The pattern may indicate network "
        "scanning or reconnaissance."
    ),
    (
        "Server C recorded suspicious network reconnaissance "
        "activity involving multiple destination ports."
    ),
]


# ------------------------------------------------------------------
# IDs
# ------------------------------------------------------------------

IDS = [
    "final_e2e_001",
    "final_e2e_002",
    "final_e2e_003",
    "final_e2e_004",
    "final_e2e_005",
    "final_e2e_006",
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
# Create controlled database
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
            "Final end-to-end database setup failed."
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
    Fresh Retriever wrapper for each API request.

    The underlying Retriever uses the shared controlled database.

    close() is intentionally a no-op because the API closes its
    Retriever after each request, while this integration test needs
    to keep the shared benchmark database available for all tests.
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

    # --------------------------------------------------------------
    # Main retrieval
    # --------------------------------------------------------------

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

    # --------------------------------------------------------------
    # Document retrieval
    # --------------------------------------------------------------

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

    # --------------------------------------------------------------
    # Metadata retrieval
    # --------------------------------------------------------------

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

    # --------------------------------------------------------------
    # Scored retrieval
    # --------------------------------------------------------------

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

    # --------------------------------------------------------------
    # Information
    # --------------------------------------------------------------

    def count(self):

        return self._retriever.count()

    def info(self):

        return self._retriever.info()

    # --------------------------------------------------------------
    # Lifecycle
    # --------------------------------------------------------------

    def close(self):
        """
        Do not close the shared benchmark database.
        """

        return None


# ------------------------------------------------------------------
# Main integration evaluation
# ------------------------------------------------------------------

def main():

    print("=" * 70)
    print(
        "FINAL END-TO-END SYSTEM INTEGRATION"
    )
    print("=" * 70)

    passed = 0
    failed = 0

    # --------------------------------------------------------------
    # Assertion helper
    # --------------------------------------------------------------

    def check(
        test_name,
        condition,
    ):

        nonlocal passed, failed

        if condition:

            print(
                f"{test_name}: PASS"
            )

            passed += 1

        else:

            print(
                f"{test_name}: FAIL"
            )

            failed += 1

    # --------------------------------------------------------------
    # Create controlled database
    # --------------------------------------------------------------

    print()
    print(
        "Creating controlled end-to-end database..."
    )

    database, embedding_manager = (
        create_database()
    )

    print(
        "Records stored:",
        database.count(),
    )

    database_setup_valid = (
        database.count()
        == len(DOCUMENTS)
    )

    check(
        "Database setup",
        database_setup_valid,
    )

    # --------------------------------------------------------------
    # API client
    # --------------------------------------------------------------

    client = TestClient(
        app
    )

    # --------------------------------------------------------------
    # Database factory
    # --------------------------------------------------------------

    def database_factory(
        collection_name="log_embeddings",
        persist_directory=None,
    ):
        """
        Route the API's log database access to the controlled
        benchmark database.

        Knowledge retrieval receives an isolated empty database.
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
    # Retriever factory
    # --------------------------------------------------------------

    def retriever_factory(
        database=None,
        embedding_manager=None,
        top_k=3,
        distance_threshold=0.98,
    ):
        """
        Return a fresh validation Retriever wrapper for every
        API request.

        The wrapper shares the controlled database but has a
        no-op close() method.
        """

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
    # TEST 1 - DIRECT SOURCE-AWARE RETRIEVAL
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 1 - DIRECT SOURCE-AWARE RETRIEVAL"
    )

    retriever = ValidationRetriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=3,
        distance_threshold=0.98,
    )

    metadata = retriever.retrieve_metadata(
        query=(
            "failed SSH authentication "
            "brute force password attack"
        ),
        top_k=3,
        source="server-a",
    )

    sources = [
        item.get("source")
        for item in metadata
    ]

    print(
        "Retrieved sources:",
        sources,
    )

    direct_retrieval_valid = (
        len(sources) > 0
        and all(
            source == "server-a"
            for source in sources
        )
    )

    check(
        "Direct source-aware retrieval",
        direct_retrieval_valid,
    )

    # ==============================================================
    # TEST 2 - QUERY-ONLY API
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 2 - QUERY-ONLY API"
    )

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
        "Returned query:",
        data.get("query"),
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
        and data.get("query")
        == (
            "failed SSH authentication "
            "brute force attack"
        )
        and data.get(
            "source"
        ) is None
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
            "metadata",
            {},
        ).get(
            "log_results",
            0,
        ) > 0
    )

    check(
        "Query-only end-to-end analysis",
        query_only_valid,
    )

    # ==============================================================
    # TEST 3 - SERVER-A API
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 3 - SERVER-A API"
    )

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

    server_a_valid = (
        response.status_code == 200
        and data.get("source")
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
        and bool(
            data.get(
                "answer",
                "",
            ).strip()
        )
    )

    check(
        "Server-A end-to-end analysis",
        server_a_valid,
    )

    # ==============================================================
    # TEST 4 - SERVER-B API
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 4 - SERVER-B API"
    )

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

    server_b_valid = (
        response.status_code == 200
        and data.get("source")
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
        and bool(
            data.get(
                "answer",
                "",
            ).strip()
        )
    )

    check(
        "Server-B end-to-end analysis",
        server_b_valid,
    )

    # ==============================================================
    # TEST 5 - SERVER-C API
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 5 - SERVER-C API"
    )

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

    server_c_valid = (
        response.status_code == 200
        and data.get("source")
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
        and bool(
            data.get(
                "answer",
                "",
            ).strip()
        )
    )

    check(
        "Server-C end-to-end analysis",
        server_c_valid,
    )

    # ==============================================================
    # TEST 6 - RESPONSE SCHEMA
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 6 - RESPONSE SCHEMA"
    )

    response_fields = set(
        AnalyzeResponse.model_fields.keys()
    )

    print(
        "Response fields:",
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
        "Final API response schema",
        response_schema_valid,
    )

    # ==============================================================
    # TEST 7 - SOURCE ISOLATION
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 7 - SOURCE ISOLATION"
    )

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
        "Final source isolation",
        isolation_valid,
    )

    # ==============================================================
    # TEST 8 - MULTI-SOURCE ACCESS
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 8 - MULTI-SOURCE ACCESS"
    )

    unrestricted_queries = [
        "failed SSH authentication brute force",
        "sudo privilege escalation",
        "network scanning suspicious connections",
    ]

    observed_sources = set()

    for query in unrestricted_queries:

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
            )
        )

        sources = [
            item.get("source")
            for item in metadata
            if item.get("source")
        ]

        print(
            f"Query: {query}"
        )

        print(
            "Sources:",
            sources,
        )

        observed_sources.update(
            sources
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
        "Final multi-source retrieval",
        multi_source_valid,
    )

    # ==============================================================
    # TEST 9 - EVIDENCE METADATA
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 9 - EVIDENCE METADATA"
    )

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

    print(
        "Metadata:",
        metadata,
    )

    evidence_metadata_valid = (
        response.status_code == 200
        and isinstance(
            metadata,
            dict,
        )
        and "sources"
        in metadata
        and "log_results"
        in metadata
        and "knowledge_results"
        in metadata
        and "server-a"
        in metadata.get(
            "sources",
            [],
        )
        and metadata.get(
            "log_results",
            0,
        ) > 0
    )

    check(
        "Evidence metadata integration",
        evidence_metadata_valid,
    )

    # ==============================================================
    # TEST 10 - FINAL END-TO-END CONTRACT
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 10 - FINAL END-TO-END CONTRACT"
    )

    final_query = (
        "failed SSH authentication "
        "brute force attack"
    )

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
                "query": final_query,
                "source": "server-a",
            },
        )

    data = response.json()

    metadata = data.get(
        "metadata",
        {},
    )

    final_contract_valid = (
        response.status_code == 200
        and data.get(
            "query"
        )
        == final_query
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
        and isinstance(
            metadata,
            dict,
        )
        and "server-a"
        in metadata.get(
            "sources",
            [],
        )
        and metadata.get(
            "log_results",
            0,
        ) > 0
    )

    print(
        "HTTP status:",
        response.status_code,
    )

    print(
        "Query preserved:",
        data.get("query")
        == final_query,
    )

    print(
        "Source preserved:",
        data.get("source")
        == "server-a",
    )

    print(
        "Answer generated:",
        bool(
            data.get(
                "answer",
                "",
            ).strip()
        ),
    )

    print(
        "Metadata valid:",
        isinstance(
            metadata,
            dict,
        ),
    )

    check(
        "Final end-to-end API contract",
        final_contract_valid,
    )

    # --------------------------------------------------------------
    # Close shared database only after all tests.
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
        "FINAL END-TO-END SYSTEM INTEGRATION RESULTS"
    )
    print("=" * 70)

    print(
        f"Integration tests passed: "
        f"{passed}/11"
    )

    print(
        f"Integration tests failed: "
        f"{failed}"
    )

    # --------------------------------------------------------------
    # Validation
    # --------------------------------------------------------------

    if failed != 0:

        raise AssertionError(
            "Final end-to-end system integration failed."
        )

    if passed != 11:

        raise AssertionError(
            "Expected all 11 end-to-end integration "
            "tests to pass."
        )

    print()
    print(
        "Database integration: PASS"
    )

    print(
        "Source-aware retrieval: PASS"
    )

    print(
        "Query-only API: PASS"
    )

    print(
        "Server-A integration: PASS"
    )

    print(
        "Server-B integration: PASS"
    )

    print(
        "Server-C integration: PASS"
    )

    print(
        "Response schema integration: PASS"
    )

    print(
        "Source isolation: PASS"
    )

    print(
        "Multi-source retrieval: PASS"
    )

    print(
        "Evidence metadata: PASS"
    )

    print()
    print("=" * 70)
    print(
        "FINAL END-TO-END SYSTEM INTEGRATION PASSED"
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