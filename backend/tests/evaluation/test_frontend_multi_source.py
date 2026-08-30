"""
Frontend multi-source integration validation.

Validates the contract between the LogLlamalyzer frontend and
the source-aware API.

The test verifies:

- frontend files exist
- source selector is present
- all synchronized sources are exposed
- JavaScript sends the selected source
- query-only requests remain supported
- API responses contain source metadata
- returned metadata can be consumed by the frontend
- source-specific API requests work for server-a/server-b/server-c
"""

from pathlib import Path
import json
import re
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
# Paths
# ------------------------------------------------------------------

FRONTEND_PATH = (
    PROJECT_ROOT
    / "frontend"
)

INDEX_PATH = (
    FRONTEND_PATH
    / "index.html"
)

SCRIPT_PATH = (
    FRONTEND_PATH
    / "script.js"
)

STYLE_PATH = (
    FRONTEND_PATH
    / "style.css"
)


# ------------------------------------------------------------------
# Controlled database
# ------------------------------------------------------------------

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "frontend_multi_source_test"
)

KNOWLEDGE_DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "frontend_multi_source_knowledge_test"
)

COLLECTION_NAME = (
    "frontend_multi_source_test"
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
    "frontend_source_001",
    "frontend_source_002",
    "frontend_source_003",
    "frontend_source_004",
    "frontend_source_005",
    "frontend_source_006",
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
            import shutil

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
            "Frontend integration database setup failed."
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
    Fresh Retriever wrapper for each API request.

    The wrapped Retriever uses the shared controlled database,
    while close() does not close that shared database.
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
# Frontend source extraction
# ------------------------------------------------------------------

def frontend_contains_source_options(
    html,
):
    """
    Check that server-a, server-b and server-c
    are represented as source options.
    """

    return all(
        source in html
        for source in [
            "server-a",
            "server-b",
            "server-c",
        ]
    )


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():

    print("=" * 70)
    print(
        "FRONTEND MULTI-SOURCE INTEGRATION VALIDATION"
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
    # Read frontend files
    # --------------------------------------------------------------

    print()
    print(
        "Loading frontend files..."
    )

    if not INDEX_PATH.exists():

        raise AssertionError(
            "frontend/index.html does not exist."
        )

    if not SCRIPT_PATH.exists():

        raise AssertionError(
            "frontend/script.js does not exist."
        )

    if not STYLE_PATH.exists():

        raise AssertionError(
            "frontend/style.css does not exist."
        )

    index_html = INDEX_PATH.read_text(
        encoding="utf-8"
    )

    script_js = SCRIPT_PATH.read_text(
        encoding="utf-8"
    )

    style_css = STYLE_PATH.read_text(
        encoding="utf-8"
    )

    print(
        "Frontend files loaded: PASS"
    )

    # ==============================================================
    # TEST 1 - SOURCE SELECTOR
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 1 - SOURCE SELECTOR")

    source_selector_present = (
        'id="source"'
        in index_html
        and "<select"
        in index_html
    )

    print(
        "Source selector present:",
        source_selector_present,
    )

    check(
        "Frontend source selector",
        source_selector_present,
    )

    # ==============================================================
    # TEST 2 - SOURCE OPTIONS
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 2 - SOURCE OPTIONS")

    sources_present = (
        frontend_contains_source_options(
            index_html
        )
    )

    print(
        "server-a:",
        "server-a" in index_html,
    )

    print(
        "server-b:",
        "server-b" in index_html,
    )

    print(
        "server-c:",
        "server-c" in index_html,
    )

    check(
        "All synchronized source options",
        sources_present,
    )

    # ==============================================================
    # TEST 3 - ALL SOURCES OPTION
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 3 - ALL SOURCES OPTION")

    all_sources_present = (
        "All synchronized sources"
        in index_html
    )

    print(
        "All-source option present:",
        all_sources_present,
    )

    check(
        "All synchronized sources option",
        all_sources_present,
    )

    # ==============================================================
    # TEST 4 - JAVASCRIPT SOURCE INPUT
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 4 - JAVASCRIPT SOURCE INPUT")

    js_source_input = (
        "sourceInput"
        in script_js
        and
        "document.getElementById"
        in script_js
        and
        '"source"'
        in script_js
    )

    print(
        "JavaScript source input handling:",
        js_source_input,
    )

    check(
        "Frontend source input handling",
        js_source_input,
    )

    # ==============================================================
    # TEST 5 - JAVASCRIPT REQUEST SOURCE
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 5 - JAVASCRIPT REQUEST SOURCE")

    js_sends_source = (
        "requestBody.source"
        in script_js
        and
        "JSON.stringify"
        in script_js
        and
        "requestBody"
        in script_js
    )

    print(
        "Selected source added to request:",
        js_sends_source,
    )

    check(
        "Frontend sends selected source",
        js_sends_source,
    )

    # ==============================================================
    # TEST 6 - JAVASCRIPT RESPONSE METADATA
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 6 - JAVASCRIPT RESPONSE METADATA"
    )

    js_reads_metadata = (
        "data.metadata"
        in script_js
        and
        "metadata.sources"
        in script_js
        and
        "metadata.log_results"
        in script_js
        and
        "metadata.knowledge_results"
        in script_js
    )

    print(
        "Metadata consumption:",
        js_reads_metadata,
    )

    check(
        "Frontend response metadata handling",
        js_reads_metadata,
    )

    # ==============================================================
    # TEST 7 - SOURCE API CONTRACT
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 7 - SOURCE API CONTRACT")

    response_fields = set(
        AnalyzeResponse.model_fields.keys()
    )

    print(
        "AnalyzeResponse fields:",
        sorted(response_fields),
    )

    api_contract_valid = (
        response_fields
        == {
            "query",
            "answer",
            "source",
            "metadata",
        }
    )

    check(
        "Frontend/API response contract",
        api_contract_valid,
    )

    # ==============================================================
    # Controlled API setup
    # ==============================================================

    print()
    print(
        "Creating controlled API environment..."
    )

    database, embedding_manager = (
        create_database()
    )

    print(
        "Controlled records:",
        database.count(),
    )

    client = TestClient(
        app
    )

    def database_factory(
        collection_name="log_embeddings",
        persist_directory=None,
    ):
        """
        Route API log access to the controlled database.

        Knowledge retrieval gets an empty collection.
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

    def retriever_factory(
        database=None,
        embedding_manager=None,
        top_k=3,
        distance_threshold=0.98,
    ):

        return ValidationRetriever(
            database=database,
            embedding_manager=embedding_manager,
            top_k=top_k,
            distance_threshold=distance_threshold,
        )

    # ==============================================================
    # TEST 8 - SERVER-A FRONTEND/API CONTRACT
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 8 - SERVER-A FRONTEND/API CONTRACT")

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
        and data.get(
            "source"
        )
        == "server-a"
        and data.get(
            "metadata",
            {},
        ).get(
            "sources",
            [],
        )
        == ["server-a"]
        and data.get(
            "metadata",
            {},
        ).get(
            "log_results",
            0,
        ) > 0
    )

    check(
        "Server-A frontend/API contract",
        server_a_valid,
    )

    # ==============================================================
    # TEST 9 - SERVER-B FRONTEND/API CONTRACT
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 9 - SERVER-B FRONTEND/API CONTRACT")

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
        and data.get(
            "source"
        )
        == "server-b"
        and data.get(
            "metadata",
            {},
        ).get(
            "sources",
            [],
        )
        == ["server-b"]
        and data.get(
            "metadata",
            {},
        ).get(
            "log_results",
            0,
        ) > 0
    )

    check(
        "Server-B frontend/API contract",
        server_b_valid,
    )

    # ==============================================================
    # TEST 10 - SERVER-C FRONTEND/API CONTRACT
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 10 - SERVER-C FRONTEND/API CONTRACT")

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
        and data.get(
            "source"
        )
        == "server-c"
        and data.get(
            "metadata",
            {},
        ).get(
            "sources",
            [],
        )
        == ["server-c"]
        and data.get(
            "metadata",
            {},
        ).get(
            "log_results",
            0,
        ) > 0
    )

    check(
        "Server-C frontend/API contract",
        server_c_valid,
    )

    # ==============================================================
    # TEST 11 - QUERY-ONLY COMPATIBILITY
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 11 - QUERY-ONLY COMPATIBILITY")

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
        and isinstance(
            data.get(
                "metadata"
            ),
            dict,
        )
    )

    check(
        "Query-only frontend/API compatibility",
        query_only_valid,
    )

    # ==============================================================
    # TEST 12 - FRONTEND METADATA DISPLAY CONTRACT
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 12 - FRONTEND METADATA DISPLAY CONTRACT"
    )

    metadata_display_contract = (
        "displayMetadata"
        in script_js
        and
        "metadata-source"
        in index_html
        and
        "metadata-logs"
        in index_html
        and
        "metadata-knowledge"
        in index_html
    )

    print(
        "Frontend metadata display elements:",
        metadata_display_contract,
    )

    check(
        "Frontend metadata display contract",
        metadata_display_contract,
    )

    # --------------------------------------------------------------
    # Close controlled database.
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
        "FRONTEND MULTI-SOURCE INTEGRATION RESULTS"
    )
    print("=" * 70)

    print(
        f"Tests passed: "
        f"{passed}/12"
    )

    print(
        f"Tests failed: "
        f"{failed}"
    )

    if failed != 0:

        raise AssertionError(
            "Frontend multi-source integration "
            "validation failed."
        )

    if passed != 12:

        raise AssertionError(
            "Expected all 12 frontend/API "
            "integration tests to pass."
        )

    print()
    print(
        "Source selector: PASS"
    )

    print(
        "Synchronized source options: PASS"
    )

    print(
        "JavaScript source handling: PASS"
    )

    print(
        "JavaScript request integration: PASS"
    )

    print(
        "JavaScript metadata handling: PASS"
    )

    print(
        "Server-A contract: PASS"
    )

    print(
        "Server-B contract: PASS"
    )

    print(
        "Server-C contract: PASS"
    )

    print(
        "Query-only compatibility: PASS"
    )

    print(
        "Frontend metadata display: PASS"
    )

    print()
    print("=" * 70)
    print(
        "FRONTEND MULTI-SOURCE INTEGRATION PASSED"
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