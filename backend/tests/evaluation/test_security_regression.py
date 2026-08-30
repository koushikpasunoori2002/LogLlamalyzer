"""
Security regression evaluation.

Verifies that security-analysis functionality remains stable
after the security analysis improvements.

The regression suite covers:
- basic security retrieval
- security classification
- severity prediction
- evidence grounding
- security relevance
- false-positive prevention
- distance-threshold filtering
- source filtering
- multi-source retrieval
- Retriever API compatibility
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
# Main regression evaluation
# ------------------------------------------------------------------

def main():

    database_path = (
        PROJECT_ROOT
        / "data"
        / "security_regression_test"
    )

    database = ChromaDatabase(
        persist_directory=database_path,
        collection_name="security_regression_test",
    )

    embedding_manager = EmbeddingManager()

    print("=" * 70)
    print("SECURITY REGRESSION TEST")
    print("=" * 70)

    # --------------------------------------------------------------
    # Clear previous records
    # --------------------------------------------------------------

    database.clear()

    print("\nDatabase cleared.")

    # --------------------------------------------------------------
    # Regression dataset
    # --------------------------------------------------------------

    documents = [
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
        (
            "The Apache web server started successfully and is "
            "operating normally."
        ),
        (
            "A user successfully logged into the system."
        ),
        (
            "The package manager completed a normal software update."
        ),
        (
            "The system completed a normal shutdown operation."
        ),
        (
            "The kernel reported a normal system event."
        ),
    ]

    ids = [
        "security_regression_001",
        "security_regression_002",
        "security_regression_003",
        "security_regression_004",
        "security_regression_005",
        "security_regression_006",
        "security_regression_007",
        "security_regression_008",
        "security_regression_009",
        "security_regression_010",
    ]

    metadatas = [
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
        {
            "scenario": "normal_web_server",
            "classification": "normal",
            "severity": "INFO",
            "source": "server-a",
            "log_type": "apache",
        },
        {
            "scenario": "successful_login",
            "classification": "normal",
            "severity": "INFO",
            "source": "server-a",
            "log_type": "auth",
        },
        {
            "scenario": "normal_package_update",
            "classification": "normal",
            "severity": "INFO",
            "source": "server-b",
            "log_type": "dpkg",
        },
        {
            "scenario": "normal_shutdown",
            "classification": "normal",
            "severity": "INFO",
            "source": "server-c",
            "log_type": "syslog",
        },
        {
            "scenario": "normal_kernel_event",
            "classification": "normal",
            "severity": "INFO",
            "source": "server-c",
            "log_type": "kern",
        },
    ]

    # --------------------------------------------------------------
    # Generate embeddings
    # --------------------------------------------------------------

    print("\nGenerating embeddings...")

    embeddings = embedding_manager.embed_texts(
        documents
    )

    print(
        "Embedding shape:",
        getattr(embeddings, "shape", None),
    )

    if len(embeddings) != len(documents):
        raise AssertionError(
            "Embedding count does not match document count."
        )

    print(
        "Embedding generation regression test: PASS"
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
        "\nRecords stored:",
        database.count(),
    )

    if database.count() != len(documents):
        raise AssertionError(
            "Expected all regression records to be stored."
        )

    print(
        "Database insertion regression test: PASS"
    )

    # --------------------------------------------------------------
    # Production-style retriever
    # --------------------------------------------------------------

    retriever = Retriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=3,
        distance_threshold=0.98,
    )

    # --------------------------------------------------------------
    # Unfiltered retriever
    #
    # Used for semantic regression checks. This prevents a distance
    # threshold from masking whether the underlying retrieval API
    # still returns the correct semantic evidence.
    # --------------------------------------------------------------

    unfiltered_retriever = Retriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=3,
        distance_threshold=None,
    )

    passed = 0
    failed = 0

    def check(test_name, condition):

        nonlocal passed, failed

        if condition:
            print(f"{test_name}: PASS")
            passed += 1
        else:
            print(f"{test_name}: FAIL")
            failed += 1

    # --------------------------------------------------------------
    # TEST 1 - BASIC SECURITY RETRIEVAL
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 1 - BASIC SECURITY RETRIEVAL")

    results = retriever.retrieve(
        query=(
            "Multiple failed SSH authentication attempts "
            "remote IP repeated failed password attempts "
            "SSH brute force attack"
        ),
        top_k=3,
    )

    retrieved_documents = results.get(
        "documents",
        [],
    )

    if retrieved_documents:
        retrieved_documents = retrieved_documents[0]

    print(
        "Retrieved documents:",
        len(retrieved_documents),
    )

    check(
        "Basic security retrieval regression test",
        len(retrieved_documents) > 0,
    )

    # --------------------------------------------------------------
    # TEST 2 - SECURITY CLASSIFICATION
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 2 - SECURITY CLASSIFICATION")

    metadata = unfiltered_retriever.retrieve_metadata(
        query=(
            "user executed sudo commands "
            "obtain elevated privileges "
            "suspicious privilege escalation activity"
        ),
        top_k=3,
    )

    classifications = [
        item.get("classification")
        for item in metadata
    ]

    print(
        "Retrieved classifications:",
        classifications,
    )

    check(
        "Security classification regression test",
        "privilege_escalation" in classifications,
    )

    # --------------------------------------------------------------
    # TEST 3 - SEVERITY PRESERVATION
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 3 - SEVERITY PRESERVATION")

    metadata = unfiltered_retriever.retrieve_metadata(
        query=(
            "suspicious executable launched "
            "temporary directory "
            "unexpected process execution "
            "malware activity"
        ),
        top_k=3,
    )

    severities = [
        item.get("severity")
        for item in metadata
    ]

    print(
        "Retrieved severities:",
        severities,
    )

    check(
        "Severity metadata regression test",
        "HIGH" in severities,
    )

    # --------------------------------------------------------------
    # TEST 4 - EVIDENCE RETRIEVAL
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 4 - EVIDENCE RETRIEVAL")

    evidence = unfiltered_retriever.retrieve_documents(
        query=(
            "multiple connections attempted "
            "different network ports "
            "network scanning reconnaissance activity"
        ),
        top_k=3,
    )

    print(
        "Evidence documents returned:",
        len(evidence),
    )

    evidence_valid = (
        len(evidence) > 0
        and any(
            (
                "network" in document.lower()
                or "port" in document.lower()
                or "scanning" in document.lower()
                or "reconnaissance" in document.lower()
            )
            for document in evidence
        )
    )

    check(
        "Evidence retrieval regression test",
        evidence_valid,
    )

    # --------------------------------------------------------------
    # TEST 5 - SECURITY RELEVANCE
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 5 - SECURITY RELEVANCE")

    security_queries = [
        (
            "Multiple failed SSH authentication attempts "
            "remote IP repeated failed password attempts "
            "SSH brute force attack"
        ),
        (
            "repeated failed login attempts "
            "same account credential attack"
        ),
        (
            "user executed sudo commands "
            "obtain elevated privileges "
            "suspicious privilege escalation activity"
        ),
        (
            "suspicious executable launched "
            "temporary directory unexpected process execution "
            "malware activity"
        ),
        (
            "multiple connections attempted "
            "different network ports "
            "network scanning reconnaissance activity"
        ),
    ]

    security_hits = 0

    for query in security_queries:

        metadata = unfiltered_retriever.retrieve_metadata(
            query=query,
            top_k=3,
        )

        classifications = [
            item.get("classification")
            for item in metadata
        ]

        is_security_relevant = any(
            value is not None
            and value != "normal"
            for value in classifications
        )

        print(
            f"  Query: {query}"
        )

        print(
            f"  Classifications: {classifications}"
        )

        print(
            "  Security relevance:",
            "PASS" if is_security_relevant else "FAIL",
        )

        if is_security_relevant:
            security_hits += 1

    print(
        "Security queries with security-relevant results:",
        f"{security_hits}/{len(security_queries)}",
    )

    check(
        "Security relevance regression test",
        security_hits == len(security_queries),
    )

    # --------------------------------------------------------------
    # TEST 6 - FALSE POSITIVE PREVENTION
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 6 - FALSE POSITIVE PREVENTION")

    normal_metadata = unfiltered_retriever.retrieve_metadata(
        query=(
            "Apache web server started successfully "
            "operating normally"
        ),
        top_k=1,
    )

    normal_classifications = [
        item.get("classification")
        for item in normal_metadata
    ]

    print(
        "Normal query classifications:",
        normal_classifications,
    )

    normal_prediction = (
        normal_classifications[0]
        if normal_classifications
        else None
    )

    print(
        "Predicted classification:",
        normal_prediction,
    )

    check(
        "False-positive prevention regression test",
        normal_prediction == "normal",
    )

    # --------------------------------------------------------------
    # TEST 7 - DISTANCE THRESHOLD
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 7 - DISTANCE THRESHOLD")

    scored_results = retriever.retrieve_with_scores(
        query=(
            "Multiple failed SSH authentication attempts "
            "remote IP repeated failed password attempts "
            "SSH brute force attack"
        ),
        top_k=3,
    )

    distances = []

    for item in scored_results:

        if not isinstance(item, dict):
            continue

        distance = item.get("distance")

        if distance is not None:
            distances.append(
                float(distance)
            )

    print(
        "Distances:",
        distances,
    )

    threshold_valid = all(
        distance <= 0.98 + 1e-6
        for distance in distances
    )

    check(
        "Distance threshold regression test",
        len(distances) > 0
        and threshold_valid,
    )

    # --------------------------------------------------------------
    # TEST 8 - SOURCE FILTERING
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 8 - SOURCE FILTERING")

    source_metadata = retriever.retrieve_metadata(
        query=(
            "Multiple failed SSH authentication attempts "
            "remote IP repeated failed password attempts "
            "SSH brute force attack"
        ),
        top_k=3,
        source="server-a",
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
        "Source filtering regression test",
        source_filter_valid,
    )

    # --------------------------------------------------------------
    # TEST 9 - MULTI-SOURCE RETRIEVAL
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 9 - MULTI-SOURCE RETRIEVAL")

    multi_source_metadata = unfiltered_retriever.retrieve_metadata(
        query=(
            "suspicious authentication "
            "failed login activity"
        ),
        top_k=3,
    )

    multi_sources = [
        item.get("source")
        for item in multi_source_metadata
        if item.get("source") is not None
    ]

    unique_sources = sorted(
        set(multi_sources)
    )

    print(
        "Retrieved sources:",
        multi_sources,
    )

    print(
        "Unique sources:",
        unique_sources,
    )

    check(
        "Multi-source retrieval regression test",
        len(unique_sources) >= 2,
    )

    # --------------------------------------------------------------
    # TEST 10 - RETRIEVER API COMPATIBILITY
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 10 - RETRIEVER API COMPATIBILITY")

    api_query = (
        "repeated failed login attempts "
        "same account credential attack"
    )

    api_results = unfiltered_retriever.retrieve(
        query=api_query,
        top_k=3,
    )

    api_documents = unfiltered_retriever.retrieve_documents(
        query=api_query,
        top_k=3,
    )

    api_metadata = unfiltered_retriever.retrieve_metadata(
        query=api_query,
        top_k=3,
    )

    api_scores = unfiltered_retriever.retrieve_with_scores(
        query=api_query,
        top_k=3,
    )

    api_result_documents = api_results.get(
        "documents",
        [],
    )

    if api_result_documents:
        api_result_documents = api_result_documents[0]

    api_compatible = (
        len(api_result_documents) > 0
        and len(api_documents) > 0
        and len(api_metadata) > 0
        and len(api_scores) > 0
    )

    print(
        "retrieve():",
        len(api_result_documents),
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
        "Retriever API compatibility regression test",
        api_compatible,
    )

    # --------------------------------------------------------------
    # Close retrievers
    # --------------------------------------------------------------

    try:
        retriever.close()
    except Exception:
        pass

    try:
        unfiltered_retriever.close()
    except Exception:
        pass

    # --------------------------------------------------------------
    # Results
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("SECURITY REGRESSION RESULTS")
    print("=" * 70)

    print(
        f"Regression tests passed: {passed}/10"
    )

    print(
        f"Regression tests failed: {failed}"
    )

    # --------------------------------------------------------------
    # Validation
    # --------------------------------------------------------------

    if failed != 0:
        raise AssertionError(
            "Security regression testing failed."
        )

    if passed != 10:
        raise AssertionError(
            "Expected all 10 security regression tests to pass."
        )

    print(
        "\nSecurity retrieval regression: PASS"
    )

    print(
        "Security classification regression: PASS"
    )

    print(
        "Severity regression: PASS"
    )

    print(
        "Evidence retrieval regression: PASS"
    )

    print(
        "Security relevance regression: PASS"
    )

    print(
        "False-positive regression: PASS"
    )

    print(
        "Distance threshold regression: PASS"
    )

    print(
        "Source filtering regression: PASS"
    )

    print(
        "Multi-source regression: PASS"
    )

    print(
        "Retriever API regression: PASS"
    )

    # --------------------------------------------------------------
    # Final result
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("SECURITY REGRESSION TESTS PASSED")
    print("=" * 70)

    # --------------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------------

    try:

        if database_path.exists():

            shutil.rmtree(
                database_path
            )

            print(
                "Database Cleanup Test: PASS"
            )

    except PermissionError:

        print(
            "Database Cleanup: SKIPPED "
            "(files still locked by ChromaDB)"
        )

    except Exception as exc:

        print(
            "Database Cleanup: SKIPPED "
            f"({exc})"
        )

    print("=" * 70)


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    main()