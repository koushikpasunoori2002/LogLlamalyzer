"""
Multi-source API validation.

Verifies that the source-aware /analyze endpoint actually
retrieves evidence from the requested synchronized source.

The validation covers:

- controlled multi-source database setup
- server-a source-aware API analysis
- server-b source-aware API analysis
- server-c source-aware API analysis
- source isolation
- source leak prevention
- unrestricted multi-source access
- API response source preservation
- API retrieval evidence verification
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
from backend.database.chroma import ChromaDatabase
from backend.llm.embeddings import EmbeddingManager
from backend.rag.retriever import Retriever


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "multi_source_api_validation_test"
)

KNOWLEDGE_DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "multi_source_api_validation_knowledge_test"
)

COLLECTION_NAME = (
    "multi_source_api_validation"
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
    "api_source_001",
    "api_source_002",
    "api_source_003",
    "api_source_004",
    "api_source_005",
    "api_source_006",
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
            "Controlled database setup failed."
        )

    return (
        database,
        embedding_manager,
    )


# ------------------------------------------------------------------
# Test Retriever
# ------------------------------------------------------------------

class ValidationRetriever:
    """
    Retriever wrapper used by the API validation.

    Each API request receives a fresh underlying Retriever,
    but close() is intentionally a no-op so that the shared
    benchmark database remains available for subsequent tests.

    The wrapper also captures the actual retrieval results
    used by the API.
    """

    def __init__(
        self,
        database,
        embedding_manager,
        top_k=3,
        distance_threshold=0.98,
        capture=None,
    ):

        self._retriever = Retriever(
            database=database,
            embedding_manager=embedding_manager,
            top_k=top_k,
            distance_threshold=distance_threshold,
        )

        self.capture = (
            capture
            if capture is not None
            else []
        )

    # --------------------------------------------------------------
    # Retrieve
    # --------------------------------------------------------------

    def retrieve(
        self,
        query,
        top_k=None,
        source=None,
    ):

        result = self._retriever.retrieve(
            query=query,
            top_k=top_k,
            source=source,
        )

        self.capture.append(
            {
                "query": query,
                "source": source,
                "result": result,
            }
        )

        return result

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

    def count(self):

        return self._retriever.count()

    def info(self):

        return self._retriever.info()

    # --------------------------------------------------------------
    # Important:
    # Do NOT close the shared benchmark database.
    # --------------------------------------------------------------

    def close(self):

        return None


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():

    print("=" * 70)
    print("MULTI-SOURCE API VALIDATION")
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
    # Controlled database
    # --------------------------------------------------------------

    print()
    print(
        "Creating multi-source validation database..."
    )

    controlled_database, embedding_manager = (
        create_database()
    )

    print(
        "Records stored:",
        controlled_database.count(),
    )

    print(
        "Multi-source database setup: PASS"
    )

    # --------------------------------------------------------------
    # Capture API retrieval calls
    # --------------------------------------------------------------

    captured_retrievals = []

    # --------------------------------------------------------------
    # API Retriever factory
    #
    # A fresh wrapper is returned for every API request.
    # The wrapper shares the same benchmark database but its
    # close() method does not close that shared database.
    # --------------------------------------------------------------

    def retriever_factory(
        database=None,
        embedding_manager=None,
        top_k=3,
        distance_threshold=0.98,
    ):

        return ValidationRetriever(
            database=(
                controlled_database
                if database is not None
                else controlled_database
            ),
            embedding_manager=(
                embedding_manager
                if embedding_manager is not None
                else globals_embedding_manager
            ),
            top_k=top_k,
            distance_threshold=distance_threshold,
            capture=captured_retrievals,
        )

    globals_embedding_manager = (
        embedding_manager
    )

    # --------------------------------------------------------------
    # API database factory
    # --------------------------------------------------------------

    def database_factory(
        collection_name="log_embeddings",
        persist_directory=None,
    ):
        """
        Redirect log retrieval to the controlled database.

        Knowledge retrieval uses an isolated empty database.
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

    client = TestClient(
        app
    )

    # ==============================================================
    # TEST 1 - SERVER-A SOURCE
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 1 - SERVER-A SOURCE")

    captured_retrievals.clear()

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
                    "brute force password attack"
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

    server_a_api_valid = (
        response.status_code == 200
        and data.get("source")
        == "server-a"
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
    )

    check(
        "Server-A API analysis",
        server_a_api_valid,
    )

    server_a_calls = [
        item
        for item in captured_retrievals
        if item.get("source")
        == "server-a"
    ]

    server_a_sources = []

    for call in server_a_calls:

        result = call.get(
            "result",
            {},
        )

        metadatas = result.get(
            "metadatas",
            [],
        )

        if (
            metadatas
            and isinstance(
                metadatas,
                list,
            )
            and isinstance(
                metadatas[0],
                list,
            )
        ):

            for metadata in metadatas[0]:

                if isinstance(
                    metadata,
                    dict,
                ):

                    server_a_sources.append(
                        metadata.get(
                            "source"
                        )
                    )

    print(
        "API retrieval sources:",
        server_a_sources,
    )

    check(
        "Server-A source evidence",
        len(server_a_sources) > 0
        and all(
            source == "server-a"
            for source in server_a_sources
        ),
    )

    # ==============================================================
    # TEST 2 - SERVER-B SOURCE
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 2 - SERVER-B SOURCE")

    captured_retrievals.clear()

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
        "Returned source:",
        data.get("source"),
    )

    server_b_api_valid = (
        response.status_code == 200
        and data.get("source")
        == "server-b"
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
    )

    check(
        "Server-B API analysis",
        server_b_api_valid,
    )

    server_b_calls = [
        item
        for item in captured_retrievals
        if item.get("source")
        == "server-b"
    ]

    server_b_sources = []

    for call in server_b_calls:

        result = call.get(
            "result",
            {},
        )

        metadatas = result.get(
            "metadatas",
            [],
        )

        if (
            metadatas
            and isinstance(
                metadatas,
                list,
            )
            and isinstance(
                metadatas[0],
                list,
            )
        ):

            for metadata in metadatas[0]:

                if isinstance(
                    metadata,
                    dict,
                ):

                    server_b_sources.append(
                        metadata.get(
                            "source"
                        )
                    )

    print(
        "API retrieval sources:",
        server_b_sources,
    )

    check(
        "Server-B source evidence",
        len(server_b_sources) > 0
        and all(
            source == "server-b"
            for source in server_b_sources
        ),
    )

    # ==============================================================
    # TEST 3 - SERVER-C SOURCE
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 3 - SERVER-C SOURCE")

    captured_retrievals.clear()

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
        "Returned source:",
        data.get("source"),
    )

    server_c_api_valid = (
        response.status_code == 200
        and data.get("source")
        == "server-c"
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
    )

    check(
        "Server-C API analysis",
        server_c_api_valid,
    )

    server_c_calls = [
        item
        for item in captured_retrievals
        if item.get("source")
        == "server-c"
    ]

    server_c_sources = []

    for call in server_c_calls:

        result = call.get(
            "result",
            {},
        )

        metadatas = result.get(
            "metadatas",
            [],
        )

        if (
            metadatas
            and isinstance(
                metadatas,
                list,
            )
            and isinstance(
                metadatas[0],
                list,
            )
        ):

            for metadata in metadatas[0]:

                if isinstance(
                    metadata,
                    dict,
                ):

                    server_c_sources.append(
                        metadata.get(
                            "source"
                        )
                    )

    print(
        "API retrieval sources:",
        server_c_sources,
    )

    check(
        "Server-C source evidence",
        len(server_c_sources) > 0
        and all(
            source == "server-c"
            for source in server_c_sources
        ),
    )

    # ==============================================================
    # TEST 4 - SOURCE ISOLATION
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 4 - SOURCE ISOLATION")

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

        metadata = (
            controlled_database_retriever(
                controlled_database,
                embedding_manager,
                query,
                source,
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
        "Source isolation",
        isolation_valid,
    )

    # ==============================================================
    # TEST 5 - SHARED MULTI-SOURCE ACCESS
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 5 - SHARED MULTI-SOURCE ACCESS")

    unrestricted_queries = [
        "failed SSH authentication brute force",
        "sudo privilege escalation",
        "network scanning connections",
    ]

    unrestricted_sources = set()

    for query in unrestricted_queries:

        metadata = (
            controlled_database_retriever(
                controlled_database,
                embedding_manager,
                query,
                None,
            )
        )

        sources = [
            item.get("source")
            for item in metadata
        ]

        print(
            f"Query: {query}"
        )

        print(
            "Sources:",
            sources,
        )

        unrestricted_sources.update(
            source
            for source in sources
            if source
        )

    print(
        "Sources observed:",
        sorted(
            unrestricted_sources
        ),
    )

    shared_collection_valid = (
        {
            "server-a",
            "server-b",
            "server-c",
        }.issubset(
            unrestricted_sources
        )
    )

    check(
        "Shared multi-source access",
        shared_collection_valid,
    )

    # ==============================================================
    # TEST 6 - SOURCE LEAK PREVENTION
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 6 - SOURCE LEAK PREVENTION")

    leak_free = True

    for source, query in isolation_cases:

        metadata = (
            controlled_database_retriever(
                controlled_database,
                embedding_manager,
                query,
                source,
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

        if any(
            value != source
            for value in sources
        ):

            leak_free = False

    check(
        "Source leak prevention",
        leak_free,
    )

    # ==============================================================
    # TEST 7 - API RESPONSE SOURCE
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 7 - API RESPONSE SOURCE")

    requested_sources = [
        "server-a",
        "server-b",
        "server-c",
    ]

    source_queries = [
        "failed SSH authentication",
        "privilege escalation",
        "network scanning",
    ]

    returned_sources = []

    for source, query in zip(
        requested_sources,
        source_queries,
    ):

        captured_retrievals.clear()

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

        if response.status_code == 200:

            returned_sources.append(
                response.json().get(
                    "source"
                )
            )

        else:

            returned_sources.append(
                None
            )

    print(
        "Requested sources:",
        requested_sources,
    )

    print(
        "Returned sources:",
        returned_sources,
    )

    check(
        "API response source preservation",
        returned_sources
        == requested_sources,
    )

    # ==============================================================
    # TEST 8 - API EVIDENCE METADATA
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 8 - API EVIDENCE METADATA")

    captured_retrievals.clear()

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
        "Metadata:",
        metadata,
    )

    metadata_valid = (
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
        "API evidence metadata",
        metadata_valid,
    )

    # --------------------------------------------------------------
    # Close only the controlled database at the very end.
    # --------------------------------------------------------------

    try:

        controlled_database.close()

    except Exception:

        pass

    # --------------------------------------------------------------
    # Results
    # --------------------------------------------------------------

    print()
    print("=" * 70)
    print(
        "MULTI-SOURCE API VALIDATION RESULTS"
    )
    print("=" * 70)

    print(
        f"Tests passed: "
        f"{passed}/11"
    )

    print(
        f"Tests failed: "
        f"{failed}"
    )

    if failed != 0:

        raise AssertionError(
            "Multi-source API validation failed."
        )

    if passed != 11:

        raise AssertionError(
            "Expected all 11 validation tests "
            "to pass."
        )

    print()
    print(
        "Server-A API validation: PASS"
    )

    print(
        "Server-B API validation: PASS"
    )

    print(
        "Server-C API validation: PASS"
    )

    print(
        "Source isolation: PASS"
    )

    print(
        "Shared multi-source access: PASS"
    )

    print(
        "Source leak prevention: PASS"
    )

    print(
        "API source preservation: PASS"
    )

    print(
        "API evidence metadata: PASS"
    )

    print()
    print("=" * 70)
    print(
        "MULTI-SOURCE API VALIDATION PASSED"
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
# Direct database retrieval helper
# ------------------------------------------------------------------

def controlled_database_retriever(
    database,
    embedding_manager,
    query,
    source,
):
    """
    Perform a direct retrieval against the controlled
    database for validation-only checks.

    The Retriever is explicitly closed immediately afterward,
    but because a fresh Retriever owns the same persistent
    database object, the close operation is avoided by
    overriding close temporarily.
    """

    retriever = Retriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=3,
        distance_threshold=0.98,
    )

    try:

        metadata = retriever.retrieve_metadata(
            query=query,
            top_k=3,
            source=source,
        )

    finally:

        # Do not close the shared database.
        retriever.close = lambda: None

    return metadata


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    main()