"""
Retrieval ranking quality evaluation.

Evaluates the ranking position of relevant documents
returned by the retriever for representative security scenarios.
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
        / "retrieval_ranking_test"
    )

    # --------------------------------------------------------------
    # Create database
    # --------------------------------------------------------------

    database = ChromaDatabase(
        persist_directory=database_path,
        collection_name="retrieval_ranking_test",
    )

    embedding_manager = EmbeddingManager()

    retriever = Retriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=3,
    )

    print("=" * 70)
    print("RETRIEVAL RANKING QUALITY EVALUATION")
    print("=" * 70)

    print("\nEvaluation cutoff: K=3")

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
        "ranking_001",
        "ranking_002",
        "ranking_003",
        "ranking_004",
        "ranking_005",
        "ranking_006",
        "ranking_007",
        "ranking_008",
        "ranking_009",
        "ranking_010",
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
    # Metric accumulators
    # --------------------------------------------------------------

    passed_count = 0

    precision_at_1_values = []
    precision_at_3_values = []
    recall_at_3_values = []
    reciprocal_rank_values = []
    relevant_rank_values = []

    # --------------------------------------------------------------
    # Run evaluation
    # --------------------------------------------------------------

    print("\nRunning ranking analysis...\n")

    for scenario in scenarios:

        results = retriever.retrieve(
            query=scenario["query"],
            top_k=3,
        )

        metadata_groups = results.get(
            "metadatas",
            [],
        )

        distance_groups = results.get(
            "distances",
            [],
        )

        if not metadata_groups:

            print(
                f"FAIL: {scenario['name']}"
            )

            precision_at_1_values.append(0.0)
            precision_at_3_values.append(0.0)
            recall_at_3_values.append(0.0)
            reciprocal_rank_values.append(0.0)

            continue

        metadata_list = metadata_groups[0]

        distances = (
            distance_groups[0]
            if distance_groups
            else []
        )

        retrieved_scenarios = [
            metadata.get("scenario")
            for metadata in metadata_list
        ]

        expected = scenario["expected"]

        # ----------------------------------------------------------
        # Identify relevant results
        # ----------------------------------------------------------

        relevant_positions = []

        for index, retrieved_scenario in enumerate(
            retrieved_scenarios,
            start=1,
        ):

            if retrieved_scenario in expected:
                relevant_positions.append(index)

        # ----------------------------------------------------------
        # Precision@1
        # ----------------------------------------------------------

        if retrieved_scenarios:

            precision_at_1 = (
                1.0
                if retrieved_scenarios[0] in expected
                else 0.0
            )

        else:

            precision_at_1 = 0.0

        # ----------------------------------------------------------
        # Precision@3
        # ----------------------------------------------------------

        relevant_count = len(relevant_positions)

        precision_at_3 = (
            relevant_count / len(retrieved_scenarios)
            if retrieved_scenarios
            else 0.0
        )

        # ----------------------------------------------------------
        # Recall@3
        # ----------------------------------------------------------

        recall_at_3 = (
            relevant_count / len(expected)
            if expected
            else 0.0
        )

        # Cap recall at 1.0 because multiple retrieved
        # results can correspond to the same expected scenario.
        recall_at_3 = min(
            recall_at_3,
            1.0,
        )

        # ----------------------------------------------------------
        # Reciprocal Rank
        # ----------------------------------------------------------

        if relevant_positions:

            first_relevant_rank = (
                relevant_positions[0]
            )

            reciprocal_rank = (
                1.0 / first_relevant_rank
            )

            relevant_rank_values.append(
                first_relevant_rank
            )

        else:

            reciprocal_rank = 0.0

        # ----------------------------------------------------------
        # Store metrics
        # ----------------------------------------------------------

        precision_at_1_values.append(
            precision_at_1
        )

        precision_at_3_values.append(
            precision_at_3
        )

        recall_at_3_values.append(
            recall_at_3
        )

        reciprocal_rank_values.append(
            reciprocal_rank
        )

        # ----------------------------------------------------------
        # Scenario result
        # ----------------------------------------------------------

        if relevant_positions:

            passed_count += 1

            print(
                f"PASS: {scenario['name']}"
            )

        else:

            print(
                f"FAIL: {scenario['name']}"
            )

        print(
            f"  Query: {scenario['query']}"
        )

        print(
            f"  Retrieved: {retrieved_scenarios}"
        )

        print(
            f"  Expected:   {expected}"
        )

        print(
            f"  Relevant ranks: "
            f"{relevant_positions}"
        )

        if distances:

            formatted_distances = [
                f"{distance:.6f}"
                for distance in distances
            ]

            print(
                f"  Distances: {formatted_distances}"
            )

        print(
            f"  Precision@1: {precision_at_1:.3f}"
        )

        print(
            f"  Precision@3: {precision_at_3:.3f}"
        )

        print(
            f"  Recall@3:    {recall_at_3:.3f}"
        )

        print(
            f"  Reciprocal Rank: "
            f"{reciprocal_rank:.3f}"
        )

        print()

    # --------------------------------------------------------------
    # Aggregate metrics
    # --------------------------------------------------------------

    total = len(scenarios)

    mean_precision_at_1 = (
        sum(precision_at_1_values) / total
        if total > 0
        else 0.0
    )

    mean_precision_at_3 = (
        sum(precision_at_3_values) / total
        if total > 0
        else 0.0
    )

    mean_recall_at_3 = (
        sum(recall_at_3_values) / total
        if total > 0
        else 0.0
    )

    mean_reciprocal_rank = (
        sum(reciprocal_rank_values) / total
        if total > 0
        else 0.0
    )

    mean_relevant_rank = (
        sum(relevant_rank_values)
        / len(relevant_rank_values)
        if relevant_rank_values
        else 0.0
    )

    # --------------------------------------------------------------
    # Print summary
    # --------------------------------------------------------------

    print("=" * 70)
    print("RETRIEVAL RANKING RESULTS")
    print("=" * 70)

    print(
        f"Scenarios Passed: "
        f"{passed_count}/{total}"
    )

    print(
        f"Precision@1: "
        f"{mean_precision_at_1 * 100:.1f}%"
    )

    print(
        f"Mean Precision@3: "
        f"{mean_precision_at_3 * 100:.1f}%"
    )

    print(
        f"Mean Recall@3: "
        f"{mean_recall_at_3 * 100:.1f}%"
    )

    print(
        f"Mean Reciprocal Rank (MRR): "
        f"{mean_reciprocal_rank:.3f}"
    )

    print(
        f"Mean First Relevant Rank: "
        f"{mean_relevant_rank:.2f}"
    )

    print("=" * 70)

    # --------------------------------------------------------------
    # Evaluation status
    # --------------------------------------------------------------

    if passed_count == total:

        print(
            "RETRIEVAL RANKING EVALUATION PASSED"
        )

    else:

        print(
            "RETRIEVAL RANKING EVALUATION FAILED"
        )

        try:
            retriever.close()
        except Exception:
            pass

        raise AssertionError(
            "One or more retrieval scenarios "
            "failed ranking evaluation."
        )

    # --------------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------------

    try:

        retriever.close()

    except Exception:

        pass

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