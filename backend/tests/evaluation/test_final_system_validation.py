"""
Final system validation.

Validates the key project capabilities together using controlled
test data and the existing project components.

The validation covers:

- embedding generation
- vector database storage
- retrieval
- source-aware retrieval
- security classification metadata
- severity metadata
- RAG context construction
- structured security analysis
- source isolation
- multi-source access
- API response generation
- API response metadata
- query-only compatibility
- input validation
- API health endpoints
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
from backend.rag.chunking import ChunkManager
from backend.rag.retriever import Retriever
from backend.rag.context import ContextBuilder
from backend.llm.generation import RAGAnalyzer


# ------------------------------------------------------------------
# Controlled database
# ------------------------------------------------------------------

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "final_system_validation"
)

KNOWLEDGE_DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "final_system_validation_knowledge"
)

COLLECTION_NAME = (
    "final_system_validation"
)

KNOWLEDGE_COLLECTION_NAME = (
    "empty_knowledge"
)


# ------------------------------------------------------------------
# Controlled security dataset
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
    "final_validation_001",
    "final_validation_002",
    "final_validation_003",
    "final_validation_004",
    "final_validation_005",
    "final_validation_006",
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

    return (
        database,
        embedding_manager,
    )


# ------------------------------------------------------------------
# Validation retriever
# ------------------------------------------------------------------

class ValidationRetriever:
    """
    Retriever wrapper used for API testing.

    The wrapper uses the shared controlled database but deliberately
    does not close it when the API endpoint finishes a request.
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
# Main validation
# ------------------------------------------------------------------

def main():

    print("=" * 70)
    print(
        "FINAL SYSTEM VALIDATION"
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
    # Prepare database
    # --------------------------------------------------------------

    print()
    print(
        "Preparing controlled validation database..."
    )

    database, embedding_manager = (
        create_database()
    )

    print(
        "Records stored:",
        database.count(),
    )

    check(
        "Database setup",
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
    # TEST 1 - EMBEDDINGS
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 1 - EMBEDDING GENERATION"
    )

    query_embedding = (
        embedding_manager.embed_text(
            "failed SSH authentication"
        )
    )

    embedding_valid = (
        query_embedding is not None
        and len(query_embedding) > 0
    )

    print(
        "Embedding generated:",
        embedding_valid,
    )

    check(
        "Embedding generation",
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

    chunk_valid = (
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

    print(
        "Chunks created:",
        len(chunks),
    )

    check(
        "Chunk generation",
        chunk_valid,
    )

    # ==============================================================
    # TEST 3 - RETRIEVAL
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

    documents = results.get(
        "documents",
        [],
    )

    if documents:

        documents = documents[0]

    else:

        documents = []

    retrieval_valid = (
        len(documents) > 0
    )

    print(
        "Documents retrieved:",
        len(documents),
    )

    check(
        "Basic retrieval",
        retrieval_valid,
    )

    # ==============================================================
    # TEST 4 - SOURCE RETRIEVAL
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 4 - SOURCE-AWARE RETRIEVAL"
    )

    source_metadata = (
        retriever.retrieve_metadata(
            query=(
                "failed SSH authentication "
                "brute force attack"
            ),
            top_k=3,
            source="server-a",
        )
    )

    source_values = [
        item.get("source")
        for item in source_metadata
    ]

    source_valid = (
        len(source_values) > 0
        and all(
            value == "server-a"
            for value in source_values
        )
    )

    print(
        "Retrieved sources:",
        source_values,
    )

    check(
        "Source-aware retrieval",
        source_valid,
    )

    # ==============================================================
    # TEST 5 - CLASSIFICATION
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 5 - SECURITY CLASSIFICATION"
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

    classification_valid = (
        "privilege_escalation"
        in classifications
    )

    print(
        "Classifications:",
        classifications,
    )

    check(
        "Security classification",
        classification_valid,
    )

    # ==============================================================
    # TEST 6 - SEVERITY
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

    severity_valid = (
        "HIGH"
        in severities
    )

    print(
        "Severities:",
        severities,
    )

    check(
        "Severity preservation",
        severity_valid,
    )

    # ==============================================================
    # TEST 7 - MULTI-SOURCE ACCESS
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 7 - MULTI-SOURCE ACCESS"
    )

    multi_source_queries = [
        "failed authentication brute force",
        "sudo privilege escalation",
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
            "Query:",
            query,
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
        "Multi-source access",
        multi_source_valid,
    )

    # ==============================================================
    # TEST 8 - CONTEXT
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 8 - RAG CONTEXT"
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

    context_log_count = (
        context.log_count()
    )

    context_valid = (
        context_log_count > 0
    )

    print(
        "Log results:",
        context_log_count,
    )

    check(
        "RAG context construction",
        context_valid,
    )

    # ==============================================================
    # TEST 9 - STRUCTURED ANALYSIS
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 9 - STRUCTURED SECURITY ANALYSIS"
    )

    analysis_valid = False
    analysis_response = None

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
        "Structured security analysis",
        analysis_valid,
    )

    # ==============================================================
    # TEST 10 - RETRIEVER API
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 10 - RETRIEVER API"
    )

    api_query = (
        "failed SSH authentication"
    )

    api_result = retriever.retrieve(
        query=api_query,
        top_k=3,
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

    retriever_api_valid = (
        bool(api_result)
        and len(api_documents) > 0
        and len(api_metadata) > 0
        and len(api_scores) > 0
    )

    print(
        "retrieve():",
        bool(api_result),
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
        "Retriever API compatibility",
        retriever_api_valid,
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

    def database_factory(
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
            distance_threshold=(
                distance_threshold
            ),
        )

    # ==============================================================
    # TEST 11 - SOURCE-A API
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 11 - SERVER-A API"
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

    server_a_valid = (
        response.status_code == 200
        and data.get(
            "source"
        ) == "server-a"
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

    check(
        "Server-A API integration",
        server_a_valid,
    )

    # ==============================================================
    # TEST 12 - SOURCE-B API
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 12 - SERVER-B API"
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

    server_b_valid = (
        response.status_code == 200
        and data.get(
            "source"
        ) == "server-b"
        and bool(
            data.get(
                "answer",
                "",
            ).strip()
        )
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

    check(
        "Server-B API integration",
        server_b_valid,
    )

    # ==============================================================
    # TEST 13 - SOURCE-C API
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 13 - SERVER-C API"
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

    server_c_valid = (
        response.status_code == 200
        and data.get(
            "source"
        ) == "server-c"
        and bool(
            data.get(
                "answer",
                "",
            ).strip()
        )
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

    check(
        "Server-C API integration",
        server_c_valid,
    )

    # ==============================================================
    # TEST 14 - QUERY-ONLY API
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 14 - QUERY-ONLY API"
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
                )
            },
        )

    data = response.json()

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

    check(
        "Query-only API compatibility",
        query_only_valid,
    )

    # ==============================================================
    # TEST 15 - RESPONSE SCHEMA
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 15 - RESPONSE SCHEMA"
    )

    response_fields = set(
        AnalyzeResponse.model_fields.keys()
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

    print(
        "Response fields:",
        sorted(response_fields),
    )

    check(
        "API response schema",
        response_schema_valid,
    )

    # ==============================================================
    # TEST 16 - RESPONSE METADATA
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 16 - RESPONSE METADATA"
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

    metadata = data.get(
        "metadata",
        {},
    )

    metadata_valid = (
        isinstance(
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
        "Metadata:",
        metadata,
    )

    check(
        "API response metadata",
        metadata_valid,
    )

    # ==============================================================
    # TEST 17 - API INPUT VALIDATION
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 17 - API INPUT VALIDATION"
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
        "Empty query:",
        empty_query_response.status_code,
    )

    print(
        "Empty source:",
        empty_source_response.status_code,
    )

    print(
        "Missing query:",
        missing_query_response.status_code,
    )

    validation_valid = (
        empty_query_response.status_code
        == 400
        and empty_source_response.status_code
        == 400
        and missing_query_response.status_code
        == 422
    )

    check(
        "API input validation",
        validation_valid,
    )

    # ==============================================================
    # TEST 18 - HEALTH ENDPOINTS
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "TEST 18 - HEALTH ENDPOINTS"
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
        "Root:",
        root_response.status_code,
    )

    print(
        "Health:",
        health_response.status_code,
    )

    print(
        "Status:",
        status_response.status_code,
    )

    health_valid = (
        root_response.status_code == 200
        and health_response.status_code == 200
        and status_response.status_code == 200
        and root_response.json().get(
            "status"
        ) == "running"
        and health_response.json().get(
            "status"
        ) == "healthy"
        and status_response.json().get(
            "status"
        ) == "operational"
    )

    check(
        "API health endpoints",
        health_valid,
    )

    # --------------------------------------------------------------
    # Close shared database after all checks
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
        "FINAL SYSTEM VALIDATION RESULTS"
    )
    print("=" * 70)

    print(
        f"Validation checks passed: "
        f"{passed}/19"
    )

    print(
        f"Validation checks failed: "
        f"{failed}"
    )

    # --------------------------------------------------------------
    # Validation
    # --------------------------------------------------------------

    if failed != 0:

        raise AssertionError(
            "Final system validation failed."
        )

    if passed != 19:

        raise AssertionError(
            "Expected all 19 final validation checks "
            "to pass."
        )

    print()
    print(
        "Database setup: PASS"
    )

    print(
        "Embedding generation: PASS"
    )

    print(
        "Chunk generation: PASS"
    )

    print(
        "Basic retrieval: PASS"
    )

    print(
        "Source-aware retrieval: PASS"
    )

    print(
        "Security classification: PASS"
    )

    print(
        "Severity preservation: PASS"
    )

    print(
        "Multi-source access: PASS"
    )

    print(
        "RAG context construction: PASS"
    )

    print(
        "Structured security analysis: PASS"
    )

    print(
        "Retriever API compatibility: PASS"
    )

    print(
        "Server-A API integration: PASS"
    )

    print(
        "Server-B API integration: PASS"
    )

    print(
        "Server-C API integration: PASS"
    )

    print(
        "Query-only API compatibility: PASS"
    )

    print(
        "API response schema: PASS"
    )

    print(
        "API response metadata: PASS"
    )

    print(
        "API input validation: PASS"
    )

    print(
        "API health endpoints: PASS"
    )

    print()
    print("=" * 70)
    print(
        "FINAL SYSTEM VALIDATION PASSED"
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