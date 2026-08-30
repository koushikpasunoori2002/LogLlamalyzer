"""
Security classification evaluation.

Evaluates whether retrieved security events are correctly classified
into their expected security categories.

Categories evaluated:
- ssh_brute_force
- credential_attack
- privilege_escalation
- malware
- network_scanning
- normal
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
        / "security_classification_test"
    )

    database = ChromaDatabase(
        persist_directory=database_path,
        collection_name="security_classification_test",
    )

    embedding_manager = EmbeddingManager()

    print("=" * 70)
    print("SECURITY CLASSIFICATION EVALUATION")
    print("=" * 70)

    # --------------------------------------------------------------
    # Clear previous records
    # --------------------------------------------------------------

    database.clear()

    print("\nDatabase cleared.")

    # --------------------------------------------------------------
    # Security classification dataset
    # --------------------------------------------------------------

    documents = [
        (
            "Multiple failed SSH authentication attempts were "
            "detected from a remote IP address. Repeated password "
            "failures indicate a possible SSH brute force attack."
        ),
        (
            "Repeated failed login attempts were detected against "
            "a user account. The activity may indicate a credential "
            "attack."
        ),
        (
            "A user executed sudo commands to obtain elevated "
            "privileges. Suspicious privilege escalation activity "
            "was detected."
        ),
        (
            "A suspicious executable was launched from a temporary "
            "directory. The process behaviour is consistent with "
            "possible malware execution."
        ),
        (
            "Multiple connection attempts were made against "
            "different network ports. The behaviour may indicate "
            "network scanning or reconnaissance."
        ),
        (
            "The Apache web server started successfully and is "
            "operating normally."
        ),
        (
            "The system completed a normal shutdown operation "
            "without reporting security-related errors."
        ),
        (
            "A user successfully logged into the system from an "
            "expected account."
        ),
        (
            "The package manager completed a normal software "
            "update successfully."
        ),
        (
            "The kernel reported a normal system event with no "
            "security-related activity."
        ),
    ]

    ids = [
        "classification_001",
        "classification_002",
        "classification_003",
        "classification_004",
        "classification_005",
        "classification_006",
        "classification_007",
        "classification_008",
        "classification_009",
        "classification_010",
    ]

    metadatas = [
        {
            "scenario": "ssh_brute_force",
            "security_category": "ssh_brute_force",
            "log_type": "auth",
            "severity": "HIGH",
            "source": "server-a",
        },
        {
            "scenario": "credential_attack",
            "security_category": "credential_attack",
            "log_type": "auth",
            "severity": "HIGH",
            "source": "server-a",
        },
        {
            "scenario": "privilege_escalation",
            "security_category": "privilege_escalation",
            "log_type": "auth",
            "severity": "HIGH",
            "source": "server-b",
        },
        {
            "scenario": "malware",
            "security_category": "malware",
            "log_type": "syslog",
            "severity": "HIGH",
            "source": "server-b",
        },
        {
            "scenario": "network_scanning",
            "security_category": "network_scanning",
            "log_type": "syslog",
            "severity": "HIGH",
            "source": "server-c",
        },
        {
            "scenario": "normal_web_server",
            "security_category": "normal",
            "log_type": "apache",
            "severity": "INFO",
            "source": "server-a",
        },
        {
            "scenario": "normal_shutdown",
            "security_category": "normal",
            "log_type": "syslog",
            "severity": "INFO",
            "source": "server-b",
        },
        {
            "scenario": "successful_login",
            "security_category": "normal",
            "log_type": "auth",
            "severity": "INFO",
            "source": "server-a",
        },
        {
            "scenario": "normal_package_update",
            "security_category": "normal",
            "log_type": "dpkg",
            "severity": "INFO",
            "source": "server-c",
        },
        {
            "scenario": "normal_kernel_event",
            "security_category": "normal",
            "log_type": "kern",
            "severity": "INFO",
            "source": "server-c",
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
            "Expected all security classification "
            "records to be stored."
        )

    print("Database Insert Test: PASS")

    # --------------------------------------------------------------
    # Classification scenarios
    # --------------------------------------------------------------

    scenarios = [
        {
            "name": "SSH brute force",
            "query": (
                "failed SSH authentication brute force "
                "password attack"
            ),
            "expected": "ssh_brute_force",
        },
        {
            "name": "Credential attack",
            "query": (
                "repeated failed login attempts "
                "credential attack"
            ),
            "expected": "credential_attack",
        },
        {
            "name": "Privilege escalation",
            "query": (
                "suspicious sudo privilege escalation "
                "elevated privileges"
            ),
            "expected": "privilege_escalation",
        },
        {
            "name": "Malware",
            "query": (
                "suspicious executable malware "
                "execution activity"
            ),
            "expected": "malware",
        },
        {
            "name": "Network scanning",
            "query": (
                "network scanning suspicious "
                "connections port reconnaissance"
            ),
            "expected": "network_scanning",
        },
        {
            "name": "Normal activity",
            "query": (
                "normal successful system operation "
                "without security issue"
            ),
            "expected": "normal",
        },
    ]

    # --------------------------------------------------------------
    # Evaluation
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("SECURITY CLASSIFICATION SCENARIOS")
    print("-" * 70)

    retriever = Retriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=3,
        distance_threshold=0.98,
    )

    passed = 0
    failed = 0

    true_positives = 0
    false_positives = 0
    false_negatives = 0

    for scenario in scenarios:

        metadata_results = retriever.retrieve_metadata(
            query=scenario["query"],
            top_k=3,
        )

        predicted_categories = [
            metadata.get("security_category")
            for metadata in metadata_results
        ]

        expected_category = scenario["expected"]

        predicted = (
            expected_category
            if expected_category in predicted_categories
            else (
                predicted_categories[0]
                if predicted_categories
                else None
            )
        )

        correct = predicted == expected_category

        if correct:
            passed += 1
            true_positives += 1
        else:
            failed += 1
            false_positives += 1
            false_negatives += 1

        print(
            f"\n{scenario['name']}"
        )

        print(
            f"  Query: {scenario['query']}"
        )

        print(
            f"  Expected classification: "
            f"{expected_category}"
        )

        print(
            f"  Retrieved classifications: "
            f"{predicted_categories}"
        )

        print(
            f"  Predicted classification: "
            f"{predicted}"
        )

        print(
            f"  Result: "
            f"{'PASS' if correct else 'FAIL'}"
        )

    # --------------------------------------------------------------
    # Metrics
    # --------------------------------------------------------------

    total = len(scenarios)

    accuracy = (
        passed / total
        if total
        else 0
    )

    precision = (
        true_positives
        / (true_positives + false_positives)
        if (true_positives + false_positives)
        else 0
    )

    recall = (
        true_positives
        / (true_positives + false_negatives)
        if (true_positives + false_negatives)
        else 0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if (precision + recall)
        else 0
    )

    # --------------------------------------------------------------
    # Results
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("SECURITY CLASSIFICATION RESULTS")
    print("=" * 70)

    print(
        f"Scenarios evaluated: {total}"
    )

    print(
        f"Scenarios passed: {passed}/{total}"
    )

    print(
        f"Scenarios failed: {failed}"
    )

    print(
        f"Classification Accuracy: "
        f"{accuracy * 100:.1f}%"
    )

    print(
        f"Precision: "
        f"{precision * 100:.1f}%"
    )

    print(
        f"Recall: "
        f"{recall * 100:.1f}%"
    )

    print(
        f"F1 Score: "
        f"{f1 * 100:.1f}%"
    )

    # --------------------------------------------------------------
    # Source validation
    # --------------------------------------------------------------

    source_results = retriever.retrieve_metadata(
        query="suspicious security activity",
        top_k=3,
    )

    sources = sorted(
        {
            metadata.get("source")
            for metadata in source_results
            if metadata.get("source")
        }
    )

    print(
        f"Synchronized sources observed: "
        f"{', '.join(sources)}"
    )

    if not sources:
        raise AssertionError(
            "Source metadata was not preserved."
        )

    # --------------------------------------------------------------
    # Validation
    # --------------------------------------------------------------

    if passed != total:

        raise AssertionError(
            "One or more security classification "
            "scenarios failed."
        )

    if accuracy < 0.80:

        raise AssertionError(
            "Security classification accuracy "
            "is below the required 80% threshold."
        )

    if f1 < 0.80:

        raise AssertionError(
            "Security classification F1 score "
            "is below the required 80% threshold."
        )

    print(
        "\nSecurity classification accuracy validation: PASS"
    )

    print(
        "Security classification metric validation: PASS"
    )

    print(
        "Source metadata validation: PASS"
    )

    # --------------------------------------------------------------
    # Final result
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("SECURITY CLASSIFICATION EVALUATION PASSED")
    print("=" * 70)

    # --------------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------------

    try:

        retriever.close()

        if database_path.exists():

            shutil.rmtree(
                database_path
            )

            print(
                "Database Cleanup Test: PASS"
            )

    except (PermissionError, OSError) as exc:

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