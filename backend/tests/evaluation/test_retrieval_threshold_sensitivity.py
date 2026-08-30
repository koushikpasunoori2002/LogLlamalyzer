"""
Retrieval threshold sensitivity evaluation.

Evaluates retrieval behaviour across multiple distance
thresholds and identifies the effect of threshold selection
on precision, recall, and result volume.
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
        / "retrieval_threshold_sensitivity_test"
    )

    database = ChromaDatabase(
        persist_directory=database_path,
        collection_name="retrieval_threshold_sensitivity_test",
    )

    embedding_manager = EmbeddingManager()

    print("=" * 70)
    print("RETRIEVAL THRESHOLD SENSITIVITY EVALUATION")
    print("=" * 70)

    # --------------------------------------------------------------
    # Clear previous records
    # --------------------------------------------------------------

    database.clear()

    print("\nDatabase cleared.")

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
        "sensitivity_001",
        "sensitivity_002",
        "sensitivity_003",
        "sensitivity_004",
        "sensitivity_005",
        "sensitivity_006",
        "sensitivity_007",
        "sensitivity_008",
        "sensitivity_009",
        "sensitivity_010",
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
            "Expected all sensitivity test records "
            "to be stored."
        )

    print("Database Insert Test: PASS")

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
    # Threshold values
    # --------------------------------------------------------------

    thresholds = [
        0.80,
        0.90,
        0.95,
        0.98,
        1.00,
        1.10,
    ]

    print(
        "\nThresholds under evaluation:",
        thresholds,
    )

    # --------------------------------------------------------------
    # Evaluation
    # --------------------------------------------------------------

    threshold_results = []

    # Use ONE Retriever for the complete evaluation.
    #
    # This is important because Retriever.close() releases
    # the database references. Creating and closing a Retriever
    # for every threshold would invalidate the shared ChromaDB
    # collection for the next threshold.
    retriever = Retriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=3,
        distance_threshold=thresholds[0],
    )

    try:

        for threshold in thresholds:

            # Update only the threshold.
            retriever.distance_threshold = threshold

            total_relevant = 0
            total_retrieved = 0
            total_irrelevant = 0
            scenario_hits = 0

            print(
                "\n" + "-" * 70
            )

            print(
                f"Testing threshold: {threshold:.2f}"
            )

            for scenario in scenarios:

                retrieved_metadata = (
                    retriever.retrieve_metadata(
                        query=scenario["query"],
                        top_k=3,
                    )
                )

                retrieved_scenarios = [
                    metadata.get("scenario")
                    for metadata in retrieved_metadata
                ]

                relevant_count = sum(
                    1
                    for value in retrieved_scenarios
                    if value in scenario["expected"]
                )

                irrelevant_count = (
                    len(retrieved_scenarios)
                    - relevant_count
                )

                total_retrieved += len(
                    retrieved_scenarios
                )

                total_relevant += relevant_count

                total_irrelevant += irrelevant_count

                hit = any(
                    expected in retrieved_scenarios
                    for expected in scenario["expected"]
                )

                if hit:
                    scenario_hits += 1

                print(
                    f"{scenario['name']}: "
                    f"{len(retrieved_scenarios)} results | "
                    f"{relevant_count} relevant | "
                    f"{irrelevant_count} irrelevant | "
                    f"{'HIT' if hit else 'MISS'}"
                )

            # ------------------------------------------------------
            # Metrics
            # ------------------------------------------------------

            precision = (
                total_relevant
                / total_retrieved
                if total_retrieved
                else 0
            )

            total_expected = sum(
                len(scenario["expected"])
                for scenario in scenarios
            )

            recall = (
                total_relevant
                / total_expected
                if total_expected
                else 0
            )

            hit_rate = (
                scenario_hits
                / len(scenarios)
                if scenarios
                else 0
            )

            threshold_results.append(
                {
                    "threshold": threshold,
                    "precision": precision,
                    "recall": recall,
                    "hit_rate": hit_rate,
                    "retrieved": total_retrieved,
                    "relevant": total_relevant,
                    "irrelevant": total_irrelevant,
                }
            )

            print(
                f"Threshold {threshold:.2f} summary: "
                f"Precision={precision * 100:.1f}% | "
                f"Recall={recall * 100:.1f}% | "
                f"Hit Rate={hit_rate * 100:.1f}% | "
                f"Results={total_retrieved} | "
                f"Irrelevant={total_irrelevant}"
            )

    finally:

        # Close the retriever only AFTER all thresholds
        # have been evaluated.
        retriever.close()

    # --------------------------------------------------------------
    # Summary table
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("THRESHOLD SENSITIVITY RESULTS")
    print("=" * 70)

    print(
        f"{'Threshold':<12}"
        f"{'Precision':<14}"
        f"{'Recall':<12}"
        f"{'Hit Rate':<12}"
        f"{'Results':<10}"
        f"{'Irrelevant':<12}"
    )

    print("-" * 70)

    for result in threshold_results:

        print(
            f"{result['threshold']:<12.2f}"
            f"{result['precision'] * 100:<14.1f}"
            f"{result['recall'] * 100:<12.1f}"
            f"{result['hit_rate'] * 100:<12.1f}"
            f"{result['retrieved']:<10}"
            f"{result['irrelevant']:<12}"
        )

    # --------------------------------------------------------------
    # Identify best threshold
    # --------------------------------------------------------------

    valid_results = [
        result
        for result in threshold_results
        if result["hit_rate"] == 1.0
    ]

    if not valid_results:

        raise AssertionError(
            "No evaluated threshold preserved "
            "a 100% retrieval hit rate."
        )

    # Selection priority:
    #
    # 1. Hit Rate
    # 2. Recall
    # 3. Precision
    # 4. Fewer irrelevant results
    # 5. Fewer retrieved results
    #
    # This allows 0.98 to beat 0.80 because:
    #
    # 0.80 -> Precision 100%, Recall 85.7%
    # 0.98 -> Precision 100%, Recall 100%
    #
    # Therefore 0.98 provides the better overall balance.

    best_result = max(
        valid_results,
        key=lambda result: (
            result["hit_rate"],
            result["recall"],
            result["precision"],
            -result["irrelevant"],
            -result["retrieved"],
        ),
    )

    print("\n" + "=" * 70)
    print("THRESHOLD SELECTION")
    print("=" * 70)

    print(
        f"Best evaluated threshold: "
        f"{best_result['threshold']:.2f}"
    )

    print(
        f"Precision: "
        f"{best_result['precision'] * 100:.1f}%"
    )

    print(
        f"Recall: "
        f"{best_result['recall'] * 100:.1f}%"
    )

    print(
        f"Hit Rate: "
        f"{best_result['hit_rate'] * 100:.1f}%"
    )

    print(
        f"Irrelevant results: "
        f"{best_result['irrelevant']}"
    )

    print(
        f"Retrieved results: "
        f"{best_result['retrieved']}"
    )

    # --------------------------------------------------------------
    # Verify the selected 0.98 threshold
    # --------------------------------------------------------------

    selected_threshold = next(
        (
            result
            for result in threshold_results
            if result["threshold"] == 0.98
        ),
        None,
    )

    if selected_threshold is None:

        raise AssertionError(
            "The selected 0.98 threshold was not evaluated."
        )

    if selected_threshold["hit_rate"] < 1.0:

        raise AssertionError(
            "The 0.98 threshold does not preserve "
            "100% hit rate."
        )

    if selected_threshold["precision"] < 0.90:

        raise AssertionError(
            "The 0.98 threshold does not achieve "
            "the expected precision improvement."
        )

    if selected_threshold["recall"] < 1.0:

        raise AssertionError(
            "The 0.98 threshold does not achieve "
            "100% recall."
        )

    if selected_threshold["irrelevant"] != 0:

        raise AssertionError(
            "The 0.98 threshold returned "
            "irrelevant results."
        )

    if best_result["threshold"] != 0.98:

        raise AssertionError(
            "The automatic threshold selection did not "
            "identify 0.98 as the best evaluated threshold."
        )

    print("\nSelected threshold validation: PASS")

    # --------------------------------------------------------------
    # Final result
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("RETRIEVAL THRESHOLD SENSITIVITY EVALUATION PASSED")
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

    print("=" * 70)


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    main()