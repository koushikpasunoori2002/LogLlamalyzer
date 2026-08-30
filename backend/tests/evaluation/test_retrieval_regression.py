"""
test_retrieval_regression.py

Regression tests for the retrieval system.

Verifies that existing retrieval functionality continues to work
after retrieval quality improvements and distance-threshold support.
"""

from pathlib import Path
import shutil
import sys


# ------------------------------------------------------------------
# Project path
# ------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------

from backend.rag.retriever import Retriever
from backend.database.chroma import ChromaDatabase
from backend.llm.embeddings import EmbeddingManager


# ------------------------------------------------------------------
# Test configuration
# ------------------------------------------------------------------

TOP_K = 3
DISTANCE_THRESHOLD = 0.98


# ------------------------------------------------------------------
# Main regression test
# ------------------------------------------------------------------

def main():

    database_path = (
        PROJECT_ROOT
        / "data"
        / "retrieval_regression_test"
    )

    database = ChromaDatabase(
        persist_directory=database_path,
        collection_name="retrieval_regression_test",
    )

    embedding_manager = EmbeddingManager()

    print("=" * 70)
    print("RETRIEVAL REGRESSION TEST")
    print("=" * 70)

    # --------------------------------------------------------------
    # Clear previous test records
    # --------------------------------------------------------------

    database.clear()

    print("\nDatabase cleared.")

    # --------------------------------------------------------------
    # Test documents
    # --------------------------------------------------------------

    documents = [
        (
            "Multiple failed SSH authentication attempts were "
            "detected from a remote IP address. This may indicate "
            "an SSH brute force attack."
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
            "network ports. This may indicate network scanning "
            "or reconnaissance activity."
        ),
        (
            "The system recorded repeated failed login attempts "
            "for the same account. This may indicate a credential "
            "attack."
        ),
        (
            "The Apache web server started successfully and is "
            "operating normally."
        ),
        (
            "The system completed a normal shutdown operation."
        ),
        (
            "A user successfully logged into the system."
        ),
        (
            "The package manager completed a normal software update."
        ),
        (
            "The kernel reported a normal system event."
        ),
    ]

    ids = [
        "regression_001",
        "regression_002",
        "regression_003",
        "regression_004",
        "regression_005",
        "regression_006",
        "regression_007",
        "regression_008",
        "regression_009",
        "regression_010",
    ]

    metadatas = [
        {
            "scenario": "ssh_authentication",
            "log_type": "auth",
            "severity": "HIGH",
        },
        {
            "scenario": "privilege_escalation",
            "log_type": "auth",
            "severity": "HIGH",
        },
        {
            "scenario": "malware",
            "log_type": "syslog",
            "severity": "HIGH",
        },
        {
            "scenario": "network_scanning",
            "log_type": "syslog",
            "severity": "HIGH",
        },
        {
            "scenario": "failed_login",
            "log_type": "auth",
            "severity": "MEDIUM",
        },
        {
            "scenario": "normal_web_server",
            "log_type": "apache",
            "severity": "INFO",
        },
        {
            "scenario": "normal_shutdown",
            "log_type": "syslog",
            "severity": "INFO",
        },
        {
            "scenario": "successful_login",
            "log_type": "auth",
            "severity": "INFO",
        },
        {
            "scenario": "normal_package_update",
            "log_type": "dpkg",
            "severity": "INFO",
        },
        {
            "scenario": "normal_kernel_event",
            "log_type": "kern",
            "severity": "INFO",
        },
    ]

    # --------------------------------------------------------------
    # Generate embeddings
    # --------------------------------------------------------------

    print("\nGenerating embeddings...")

    embeddings = embedding_manager.embed_texts(
        documents
    )

    if len(embeddings) != len(documents):

        raise AssertionError(
            "Embedding count does not match document count."
        )

    print(
        "Embedding generation test: PASS"
    )

    # --------------------------------------------------------------
    # Store documents
    # --------------------------------------------------------------

    database.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    print(
        "Records stored:",
        database.count(),
    )

    if database.count() != len(documents):

        raise AssertionError(
            "Expected all regression test records "
            "to be stored."
        )

    print(
        "Database insertion test: PASS"
    )

    # --------------------------------------------------------------
    # Create baseline retriever
    # --------------------------------------------------------------

    baseline_retriever = Retriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=TOP_K,
    )

    # --------------------------------------------------------------
    # Create threshold retriever
    # --------------------------------------------------------------

    threshold_retriever = Retriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=TOP_K,
        distance_threshold=DISTANCE_THRESHOLD,
    )

    query = (
        "failed SSH authentication brute force attack"
    )

    # --------------------------------------------------------------
    # 1. Basic retrieval regression
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 1 - BASIC RETRIEVAL")

    baseline_results = baseline_retriever.retrieve(
        query=query,
        top_k=TOP_K,
    )

    if not baseline_results:

        raise AssertionError(
            "Basic retrieval returned no result object."
        )

    if not baseline_results.get("documents"):

        raise AssertionError(
            "Basic retrieval returned no documents."
        )

    baseline_documents = (
        baseline_results["documents"][0]
    )

    if len(baseline_documents) == 0:

        raise AssertionError(
            "Basic retrieval returned an empty document list."
        )

    if len(baseline_documents) > TOP_K:

        raise AssertionError(
            "Basic retrieval returned more results than top_k."
        )

    print(
        f"Retrieved documents: {len(baseline_documents)}"
    )

    print(
        "Basic retrieval test: PASS"
    )

    # --------------------------------------------------------------
    # 2. top_k regression
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 2 - TOP-K LIMIT")

    top_k_results = baseline_retriever.retrieve(
        query=query,
        top_k=2,
    )

    top_k_documents = (
        top_k_results["documents"][0]
    )

    if len(top_k_documents) > 2:

        raise AssertionError(
            "Retriever returned more results than requested top_k."
        )

    if len(top_k_documents) == 0:

        raise AssertionError(
            "top_k retrieval returned no results."
        )

    print(
        f"Requested top_k: 2"
    )

    print(
        f"Returned results: {len(top_k_documents)}"
    )

    print(
        "Top-k regression test: PASS"
    )

    # --------------------------------------------------------------
    # 3. retrieve_documents regression
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 3 - RETRIEVE DOCUMENTS")

    retrieved_documents = (
        baseline_retriever.retrieve_documents(
            query=query,
            top_k=TOP_K,
        )
    )

    if not retrieved_documents:

        raise AssertionError(
            "retrieve_documents() returned no documents."
        )

    if not all(
        isinstance(document, str)
        for document in retrieved_documents
    ):

        raise AssertionError(
            "retrieve_documents() returned non-string documents."
        )

    if len(retrieved_documents) > TOP_K:

        raise AssertionError(
            "retrieve_documents() exceeded top_k."
        )

    print(
        f"Documents returned: {len(retrieved_documents)}"
    )

    print(
        "retrieve_documents() regression test: PASS"
    )

    # --------------------------------------------------------------
    # 4. retrieve_metadata regression
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 4 - RETRIEVE METADATA")

    retrieved_metadata = (
        baseline_retriever.retrieve_metadata(
            query=query,
            top_k=TOP_K,
        )
    )

    if not retrieved_metadata:

        raise AssertionError(
            "retrieve_metadata() returned no metadata."
        )

    if not all(
        isinstance(metadata, dict)
        for metadata in retrieved_metadata
    ):

        raise AssertionError(
            "retrieve_metadata() returned invalid metadata."
        )

    if len(retrieved_metadata) > TOP_K:

        raise AssertionError(
            "retrieve_metadata() exceeded top_k."
        )

    print(
        f"Metadata records returned: "
        f"{len(retrieved_metadata)}"
    )

    print(
        "retrieve_metadata() regression test: PASS"
    )

    # --------------------------------------------------------------
    # 5. retrieve_with_scores regression
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 5 - RETRIEVE WITH SCORES")

    scored_results = (
        baseline_retriever.retrieve_with_scores(
            query=query,
            top_k=TOP_K,
        )
    )

    if not scored_results:

        raise AssertionError(
            "retrieve_with_scores() returned no results."
        )

    if len(scored_results) > TOP_K:

        raise AssertionError(
            "retrieve_with_scores() exceeded top_k."
        )

    for result in scored_results:

        if "document" not in result:

            raise AssertionError(
                "Scored result is missing document."
            )

        if "distance" not in result:

            raise AssertionError(
                "Scored result is missing distance."
            )

        if not isinstance(
            result["distance"],
            (int, float),
        ):

            raise AssertionError(
                "Distance is not numeric."
            )

    print(
        f"Scored results returned: {len(scored_results)}"
    )

    print(
        "retrieve_with_scores() regression test: PASS"
    )

    # --------------------------------------------------------------
    # 6. Retrieval without threshold
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 6 - RETRIEVAL WITHOUT THRESHOLD")

    if baseline_retriever.distance_threshold is not None:

        raise AssertionError(
            "Baseline retriever should not have "
            "a distance threshold."
        )

    unrestricted_results = (
        baseline_retriever.retrieve(
            query=query,
            top_k=TOP_K,
        )
    )

    if not unrestricted_results.get("documents"):

        raise AssertionError(
            "Retrieval without threshold returned no documents."
        )

    print(
        "Distance threshold: None"
    )

    print(
        "Retrieval without threshold test: PASS"
    )

    # --------------------------------------------------------------
    # 7. Retrieval with threshold
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 7 - RETRIEVAL WITH DISTANCE THRESHOLD")

    if (
        threshold_retriever.distance_threshold
        != DISTANCE_THRESHOLD
    ):

        raise AssertionError(
            "Distance threshold was not configured correctly."
        )

    threshold_results = (
        threshold_retriever.retrieve(
            query=query,
            top_k=TOP_K,
        )
    )

    threshold_documents = (
        threshold_results.get("documents")
    )

    if not threshold_documents:

        raise AssertionError(
            "Threshold retrieval returned no documents."
        )

    filtered_documents = threshold_documents[0]

    if len(filtered_documents) > TOP_K:

        raise AssertionError(
            "Threshold retrieval exceeded top_k."
        )

    print(
        f"Distance threshold: "
        f"{DISTANCE_THRESHOLD}"
    )

    print(
        f"Results returned: "
        f"{len(filtered_documents)}"
    )

    print(
        "Distance threshold retrieval test: PASS"
    )

    # --------------------------------------------------------------
    # 8. Verify threshold filtering
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 8 - THRESHOLD FILTERING")

    threshold_scored_results = (
        threshold_retriever.retrieve_with_scores(
            query=query,
            top_k=TOP_K,
        )
    )

    if not threshold_scored_results:

        raise AssertionError(
            "Threshold scored retrieval returned no results."
        )

    for result in threshold_scored_results:

        distance = result["distance"]

        if distance > DISTANCE_THRESHOLD:

            raise AssertionError(
                "A result exceeded the configured "
                "distance threshold."
            )

    print(
        f"All returned distances <= "
        f"{DISTANCE_THRESHOLD}"
    )

    print(
        "Threshold filtering regression test: PASS"
    )

    # --------------------------------------------------------------
    # 9. Retriever information
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 9 - RETRIEVER INFORMATION")

    retriever_info = (
        threshold_retriever.info()
    )

    if retriever_info.get("component") != "Retriever":

        raise AssertionError(
            "Retriever information has an unexpected component name."
        )

    if retriever_info.get("top_k") != TOP_K:

        raise AssertionError(
            "Retriever information reports incorrect top_k."
        )

    if (
        retriever_info.get("distance_threshold")
        != DISTANCE_THRESHOLD
    ):

        raise AssertionError(
            "Retriever information reports incorrect "
            "distance threshold."
        )

    if "database" not in retriever_info:

        raise AssertionError(
            "Retriever information is missing database details."
        )

    if "embedding_model" not in retriever_info:

        raise AssertionError(
            "Retriever information is missing embedding model details."
        )

    print(
        retriever_info
    )

    print(
        "Retriever information regression test: PASS"
    )

    # --------------------------------------------------------------
    # 10. Ranking order regression
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 10 - RANKING ORDER")

    ranking_results = (
        threshold_retriever.retrieve_with_scores(
            query=query,
            top_k=TOP_K,
        )
    )

    distances = [
        result["distance"]
        for result in ranking_results
    ]

    if distances != sorted(distances):

        raise AssertionError(
            "Retrieved results are not ordered "
            "by ascending distance."
        )

    print(
        "Distances are ordered from lowest to highest."
    )

    print(
        "Ranking order regression test: PASS"
    )

    # --------------------------------------------------------------
    # Close retrievers
    # --------------------------------------------------------------

    baseline_retriever.close()
    threshold_retriever.close()

    # --------------------------------------------------------------
    # Final result
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("RETRIEVAL REGRESSION TESTS PASSED")
    print("=" * 70)

    # --------------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------------

    try:

        database.clear()

        if database.count() == 0:

            print(
                "Database Cleanup Test: PASS"
            )

        else:

            print(
                "Database Cleanup Test: FAILED"
            )

    except Exception as error:

        print(
            "Database Cleanup: SKIPPED "
            f"({error})"
        )

    try:

        if database_path.exists():

            shutil.rmtree(
                database_path
            )

            print(
                "Test directory cleanup: PASS"
            )

    except PermissionError:

        print(
            "Test directory cleanup: SKIPPED "
            "(files still locked by ChromaDB)"
        )

    except OSError as error:

        print(
            "Test directory cleanup: SKIPPED "
            f"({error})"
        )

    print("=" * 70)


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    main()