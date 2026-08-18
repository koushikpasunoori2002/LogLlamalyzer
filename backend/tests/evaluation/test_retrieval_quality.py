"""
Retrieval quality evaluation tests.

Evaluates whether the retriever returns relevant documents
for representative security scenarios.
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
# Main evaluation
# ------------------------------------------------------------------

def main():

    database_path = (
        PROJECT_ROOT
        / "data"
        / "retrieval_quality_test"
    )

    # --------------------------------------------------------------
    # Create database
    # --------------------------------------------------------------

    database = ChromaDatabase(
        persist_directory=database_path,
        collection_name="retrieval_quality_test",
    )

    embedding_manager = EmbeddingManager()

    retriever = Retriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=3,
    )

    print("=" * 60)
    print("RETRIEVAL QUALITY EVALUATION")
    print("=" * 60)

    # --------------------------------------------------------------
    # Clear previous records
    # --------------------------------------------------------------

    database.clear()

    # --------------------------------------------------------------
    # Test documents
    # --------------------------------------------------------------

    documents = [
        (
            "Multiple failed SSH authentication attempts were "
            "detected from a remote IP address. Repeated failed "
            "password attempts may indicate an SSH brute force attack."
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
            "The system recorded repeated failed login attempts "
            "for the same account. This pattern may indicate a "
            "credential attack."
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
        "retrieval_001",
        "retrieval_002",
        "retrieval_003",
        "retrieval_004",
        "retrieval_005",
        "retrieval_006",
        "retrieval_007",
        "retrieval_008",
        "retrieval_009",
        "retrieval_010",
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
            "Expected all test records to be stored."
        )

    # --------------------------------------------------------------
    # Evaluation scenarios
    # --------------------------------------------------------------

    scenarios = [
        {
            "name": "SSH authentication",
            "query": "failed SSH authentication brute force attack",
            "expected": [
                "ssh_authentication",
                "failed_login",
            ],
        },
        {
            "name": "Privilege escalation",
            "query": "suspicious sudo privilege escalation activity",
            "expected": [
                "privilege_escalation",
            ],
        },
        {
            "name": "Malware",
            "query": "possible malware execution detected",
            "expected": [
                "malware",
            ],
        },
        {
            "name": "Network scanning",
            "query": "possible network scanning and suspicious connections",
            "expected": [
                "network_scanning",
            ],
        },
        {
            "name": "Failed login",
            "query": "repeated failed login attempts",
            "expected": [
                "failed_login",
                "ssh_authentication",
            ],
        },
    ]

    # --------------------------------------------------------------
    # Run evaluation
    # --------------------------------------------------------------

    passed_count = 0

    for scenario in scenarios:

        results = retriever.retrieve(
            query=scenario["query"],
            top_k=3,
        )

        retrieved_metadata = results.get(
            "metadatas",
            [],
        )

        if not retrieved_metadata:
            print(
                f"FAIL: {scenario['name']}"
            )
            continue

        metadata_list = retrieved_metadata[0]

        retrieved_scenarios = [
            metadata.get("scenario")
            for metadata in metadata_list
        ]

        relevant = any(
            expected in retrieved_scenarios
            for expected in scenario["expected"]
        )

        if relevant:

            print(
                f"PASS: {scenario['name']}"
            )

            passed_count += 1

        else:

            print(
                f"FAIL: {scenario['name']}"
            )

            print(
                "Retrieved scenarios:",
                retrieved_scenarios,
            )

    # --------------------------------------------------------------
    # Evaluation result
    # --------------------------------------------------------------

    total = len(scenarios)

    relevance_rate = (
        passed_count / total * 100
        if total > 0
        else 0
    )

    print("=" * 60)

    print(
        f"Retrieval Result: "
        f"{passed_count}/{total} scenarios passed"
    )

    print(
        f"Retrieval Relevance Rate: "
        f"{relevance_rate:.1f}%"
    )

    if passed_count == total:

        print(
            "RETRIEVAL QUALITY EVALUATION PASSED"
        )

    else:

        print(
            "RETRIEVAL QUALITY EVALUATION FAILED"
        )

        # Close resources before raising an error.
        retriever.close()

        raise AssertionError(
            "One or more retrieval scenarios failed."
        )

    print("=" * 60)


    # --------------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------------

    try:
        retriever.close()
    except Exception:
        pass

    try:
        if database_path.exists():
            shutil.rmtree(database_path)

        print("Database Cleanup Test: PASS")

    except PermissionError:
        print(
            "Database Cleanup: SKIPPED "
            "(files still locked by ChromaDB)"
        )

    print("=" * 60)

# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    main()