"""
API response metadata evaluation.

Verifies that the /analyze endpoint exposes useful metadata
for frontend multi-source integration.

The test uses a controlled ChromaDB collection and injects
a fresh Retriever wrapper for each API request. The wrapper
prevents the endpoint's normal close() call from closing the
shared benchmark database between tests.
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
    / "api_response_metadata_test"
)

KNOWLEDGE_DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "api_response_metadata_knowledge_test"
)

COLLECTION_NAME = (
    "api_response_metadata"
)

KNOWLEDGE_COLLECTION_NAME = (
    "empty_knowledge"
)


# ------------------------------------------------------------------
# Controlled log documents
# ------------------------------------------------------------------

LOG_DOCUMENTS = [
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

LOG_IDS = [
    "metadata_001",
    "metadata_002",
    "metadata_003",
    "metadata_004",
    "metadata_005",
    "metadata_006",
]


# ------------------------------------------------------------------
# Metadata
# ------------------------------------------------------------------

LOG_METADATAS = [
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
            LOG_DOCUMENTS
        )
    )

    database.add(
        ids=LOG_IDS,
        embeddings=embeddings,
        documents=LOG_DOCUMENTS,
        metadatas=LOG_METADATAS,
    )

    if database.count() != len(
        LOG_DOCUMENTS
    ):

        raise AssertionError(
            "Controlled API metadata database "
            "was not populated correctly."
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

    The wrapper uses the shared controlled database but
    does not close that database when the API calls close().
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
    # Compatibility methods
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

    # --------------------------------------------------------------
    # API compatibility
    # --------------------------------------------------------------

    def count(self):

        return self._retriever.count()

    def info(self):

        return self._retriever.info()

    # --------------------------------------------------------------
    # Important:
    # Do not close the shared benchmark database.
    # --------------------------------------------------------------

    def close(self):

        return None


# ------------------------------------------------------------------
# Response validation
# ------------------------------------------------------------------

def validate_response(
    data,
):
    """
    Validate the enhanced API response structure.
    """

    if not isinstance(
        data,
        dict,
    ):
        return False

    required_fields = {
        "query",
        "answer",
        "source",
        "metadata",
    }

    if not required_fields.issubset(
        data.keys()
    ):
        return False

    if not isinstance(
        data["query"],
        str,
    ):
        return False

    if not isinstance(
        data["answer"],
        str,
    ):
        return False

    if not data["answer"].strip():
        return False

    metadata = data["metadata"]

    if not isinstance(
        metadata,
        dict,
    ):
        return False

    required_metadata = {
        "sources",
        "log_results",
        "knowledge_results",
    }

    if not required_metadata.issubset(
        metadata.keys()
    ):
        return False

    if not isinstance(
        metadata["sources"],
        list,
    ):
        return False

    if not isinstance(
        metadata["log_results"],
        int,
    ):
        return False

    if not isinstance(
        metadata["knowledge_results"],
        int,
    ):
        return False

    return True


# ------------------------------------------------------------------
# Main evaluation
# ------------------------------------------------------------------

def main():

    print("=" * 70)
    print(
        "API RESPONSE METADATA EVALUATION"
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
    # Controlled database
    # --------------------------------------------------------------

    print()
    print(
        "Creating controlled API metadata database..."
    )

    controlled_database, embedding_manager = (
        create_database()
    )

    print(
        "Controlled records:",
        controlled_database.count(),
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
    # Database factory
    # --------------------------------------------------------------

    def database_factory(
        collection_name="log_embeddings",
        persist_directory=None,
    ):
        """
        Redirect log database creation to the controlled
        benchmark database.

        Knowledge retrieval receives a separate empty
        database.
        """

        if collection_name == (
            "knowledge_embeddings"
        ):

            if not KNOWLEDGE_DATABASE_PATH.exists():

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

        return controlled_database

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
        Return a fresh validation wrapper for every
        API request.

        The wrapper shares the controlled database but
        has a no-op close() method.
        """

        return ValidationRetriever(
            database=(
                controlled_database
            ),
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
    # TEST 1 - RESPONSE MODEL
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 1 - RESPONSE MODEL")

    response_fields = set(
        AnalyzeResponse.model_fields.keys()
    )

    print(
        "Response fields:",
        sorted(response_fields),
    )

    response_model_valid = (
        response_fields
        == {
            "query",
            "answer",
            "source",
            "metadata",
        }
    )

    check(
        "Enhanced response schema",
        response_model_valid,
    )

    # ==============================================================
    # TEST 2 - QUERY-ONLY RESPONSE
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 2 - QUERY-ONLY RESPONSE")

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
        "Response metadata:",
        data.get("metadata"),
    )

    query_only_valid = (
        response.status_code == 200
        and validate_response(data)
        and data.get("source") is None
        and data.get(
            "metadata",
            {},
        ).get(
            "log_results",
            0,
        ) > 0
    )

    check(
        "Query-only enhanced response",
        query_only_valid,
    )

    # ==============================================================
    # TEST 3 - SERVER-A METADATA
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 3 - SERVER-A METADATA")

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

    metadata = data.get(
        "metadata",
        {},
    )

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
        metadata,
    )

    server_a_valid = (
        response.status_code == 200
        and validate_response(data)
        and data.get("source")
        == "server-a"
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
        "Server-A metadata",
        server_a_valid,
    )

    # ==============================================================
    # TEST 4 - SERVER-B METADATA
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 4 - SERVER-B METADATA")

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

    metadata = data.get(
        "metadata",
        {},
    )

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
        metadata,
    )

    server_b_valid = (
        response.status_code == 200
        and validate_response(data)
        and data.get("source")
        == "server-b"
        and "server-b"
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
        "Server-B metadata",
        server_b_valid,
    )

    # ==============================================================
    # TEST 5 - SERVER-C METADATA
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 5 - SERVER-C METADATA")

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

    metadata = data.get(
        "metadata",
        {},
    )

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
        metadata,
    )

    server_c_valid = (
        response.status_code == 200
        and validate_response(data)
        and data.get("source")
        == "server-c"
        and "server-c"
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
        "Server-C metadata",
        server_c_valid,
    )

    # ==============================================================
    # TEST 6 - SOURCE METADATA CONSISTENCY
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 6 - SOURCE METADATA CONSISTENCY"
    )

    cases = [
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

    consistency_valid = True

    for source, query in cases:

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
                    "query": query,
                    "source": source,
                },
            )

        data = response.json()

        metadata = data.get(
            "metadata",
            {},
        )

        sources = metadata.get(
            "sources",
            [],
        )

        valid = (
            response.status_code == 200
            and data.get(
                "source"
            ) == source
            and source in sources
            and metadata.get(
                "log_results",
                0,
            ) > 0
        )

        print(
            f"{source}:",
            "PASS"
            if valid
            else "FAIL",
        )

        if not valid:

            consistency_valid = False

    check(
        "Source metadata consistency",
        consistency_valid,
    )

    # ==============================================================
    # TEST 7 - EVIDENCE COUNTS
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 7 - EVIDENCE COUNTS")

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

    log_count = metadata.get(
        "log_results",
        0,
    )

    knowledge_count = metadata.get(
        "knowledge_results",
        0,
    )

    print(
        "Log evidence:",
        log_count,
    )

    print(
        "Knowledge evidence:",
        knowledge_count,
    )

    evidence_counts_valid = (
        response.status_code == 200
        and log_count > 0
        and knowledge_count >= 0
    )

    check(
        "Evidence count metadata",
        evidence_counts_valid,
    )

    # ==============================================================
    # Results
    # ==============================================================

    print()
    print("=" * 70)
    print(
        "API RESPONSE METADATA RESULTS"
    )
    print("=" * 70)

    print(
        f"Tests passed: "
        f"{passed}/7"
    )

    print(
        f"Tests failed: "
        f"{failed}"
    )

    if failed != 0:

        raise AssertionError(
            "API response metadata evaluation failed."
        )

    if passed != 7:

        raise AssertionError(
            "Expected all 7 metadata tests to pass."
        )

    print()
    print(
        "Enhanced response schema: PASS"
    )

    print(
        "Query-only compatibility: PASS"
    )

    print(
        "Server-A metadata: PASS"
    )

    print(
        "Server-B metadata: PASS"
    )

    print(
        "Server-C metadata: PASS"
    )

    print(
        "Source consistency: PASS"
    )

    print(
        "Evidence counts: PASS"
    )

    print()
    print("=" * 70)
    print(
        "API RESPONSE METADATA EVALUATION PASSED"
    )
    print("=" * 70)

    # --------------------------------------------------------------
    # Final cleanup
    # --------------------------------------------------------------

    try:

        controlled_database.close()

    except Exception:

        pass

    try:

        if DATABASE_PATH.exists():

            shutil.rmtree(
                DATABASE_PATH
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