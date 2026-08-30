"""
Retrieval optimization evaluation.

Evaluates distance-threshold filtering to determine whether
retrieval results can be improved by removing low-relevance
high-distance results.
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
        / "retrieval_optimization_test"
    )

    database = ChromaDatabase(
        persist_directory=database_path,
        collection_name="retrieval_optimization_test",
    )

    embedding_manager = EmbeddingManager()

    print("=" * 70)
    print("RETRIEVAL OPTIMIZATION EVALUATION")
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
        "optimization_001",
        "optimization_002",
        "optimization_003",
        "optimization_004",
        "optimization_005",
        "optimization_006",
        "optimization_007",
        "optimization_008",
        "optimization_009",
        "optimization_010",
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
            "Expected all optimization test records "
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
    # Threshold
    # --------------------------------------------------------------
    #
    # Earlier distance analysis showed:
    #
    # Furthest relevant distance : 0.965643
    # Closest irrelevant distance: 0.998003
    #
    # Therefore 0.98 is used as an experimental threshold.
    #
    # --------------------------------------------------------------

    threshold = 0.98

    print(
        f"\nExperimental distance threshold: "
        f"{threshold:.2f}"
    )

    # --------------------------------------------------------------
    # Create retrievers
    # --------------------------------------------------------------

    baseline_retriever = Retriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=3,
        distance_threshold=None,
    )

    optimized_retriever = Retriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=3,
        distance_threshold=threshold,
    )

    # --------------------------------------------------------------
    # Run optimization evaluation
    # --------------------------------------------------------------

    baseline_hits = 0
    optimized_hits = 0

    baseline_irrelevant = 0
    optimized_irrelevant = 0

    baseline_result_count = 0
    optimized_result_count = 0

    print("\nRunning optimization analysis...")

    for scenario in scenarios:

        # ----------------------------------------------------------
        # Baseline retrieval
        # ----------------------------------------------------------

        baseline_results = (
            baseline_retriever.retrieve_with_scores(
                query=scenario["query"],
                top_k=3,
            )
        )

        # ----------------------------------------------------------
        # Threshold retrieval
        # ----------------------------------------------------------

        optimized_results = (
            optimized_retriever.retrieve_with_scores(
                query=scenario["query"],
                top_k=3,
            )
        )

        # ----------------------------------------------------------
        # Extract scenario names
        # ----------------------------------------------------------

        baseline_scenarios = []

        baseline_metadata = (
            baseline_retriever.retrieve_metadata(
                query=scenario["query"],
                top_k=3,
            )
        )

        for metadata in baseline_metadata:

            baseline_scenarios.append(
                metadata.get("scenario")
            )

        optimized_scenarios = []

        optimized_metadata = (
            optimized_retriever.retrieve_metadata(
                query=scenario["query"],
                top_k=3,
            )
        )

        for metadata in optimized_metadata:

            optimized_scenarios.append(
                metadata.get("scenario")
            )

        # ----------------------------------------------------------
        # Relevant results
        # ----------------------------------------------------------

        baseline_relevant = [
            value
            for value in baseline_scenarios
            if value in scenario["expected"]
        ]

        optimized_relevant = [
            value
            for value in optimized_scenarios
            if value in scenario["expected"]
        ]

        # ----------------------------------------------------------
        # Irrelevant results
        # ----------------------------------------------------------

        baseline_irrelevant_count = (
            len(baseline_scenarios)
            - len(baseline_relevant)
        )

        optimized_irrelevant_count = (
            len(optimized_scenarios)
            - len(optimized_relevant)
        )

        baseline_irrelevant += (
            baseline_irrelevant_count
        )

        optimized_irrelevant += (
            optimized_irrelevant_count
        )

        baseline_result_count += len(
            baseline_results
        )

        optimized_result_count += len(
            optimized_results
        )

        # ----------------------------------------------------------
        # Hit checks
        # ----------------------------------------------------------

        baseline_hit = any(
            expected in baseline_scenarios
            for expected in scenario["expected"]
        )

        optimized_hit = any(
            expected in optimized_scenarios
            for expected in scenario["expected"]
        )

        if baseline_hit:
            baseline_hits += 1

        if optimized_hit:
            optimized_hits += 1

        # ----------------------------------------------------------
        # Display
        # ----------------------------------------------------------

        print(
            f"\n{scenario['name']}"
        )

        print(
            "  Baseline:"
        )

        print(
            f"    Retrieved: "
            f"{baseline_scenarios}"
        )

        print(
            f"    Results: "
            f"{len(baseline_results)}"
        )

        print(
            f"    Relevant: "
            f"{len(baseline_relevant)}"
        )

        print(
            f"    Irrelevant: "
            f"{baseline_irrelevant_count}"
        )

        print(
            "  Optimized:"
        )

        print(
            f"    Retrieved: "
            f"{optimized_scenarios}"
        )

        print(
            f"    Results: "
            f"{len(optimized_results)}"
        )

        print(
            f"    Relevant: "
            f"{len(optimized_relevant)}"
        )

        print(
            f"    Irrelevant: "
            f"{optimized_irrelevant_count}"
        )

        if optimized_hit:

            print(
                "  Threshold Retrieval Hit: PASS"
            )

        else:

            print(
                "  Threshold Retrieval Hit: FAIL"
            )

    # --------------------------------------------------------------
    # Calculate metrics
    # --------------------------------------------------------------

    total = len(scenarios)

    baseline_hit_rate = (
        baseline_hits / total * 100
        if total
        else 0
    )

    optimized_hit_rate = (
        optimized_hits / total * 100
        if total
        else 0
    )

    baseline_precision = (
        (
            baseline_result_count
            - baseline_irrelevant
        )
        / baseline_result_count
        * 100
        if baseline_result_count
        else 0
    )

    optimized_precision = (
        (
            optimized_result_count
            - optimized_irrelevant
        )
        / optimized_result_count
        * 100
        if optimized_result_count
        else 0
    )

    irrelevant_reduction = (
        (
            baseline_irrelevant
            - optimized_irrelevant
        )
        / baseline_irrelevant
        * 100
        if baseline_irrelevant
        else 0
    )

    # --------------------------------------------------------------
    # Results
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("RETRIEVAL OPTIMIZATION RESULTS")
    print("=" * 70)

    print(
        f"Baseline Hit Rate@3:       "
        f"{baseline_hit_rate:.1f}%"
    )

    print(
        f"Optimized Hit Rate:        "
        f"{optimized_hit_rate:.1f}%"
    )

    print(
        f"Baseline Precision:        "
        f"{baseline_precision:.1f}%"
    )

    print(
        f"Optimized Precision:       "
        f"{optimized_precision:.1f}%"
    )

    print(
        f"Baseline Irrelevant:       "
        f"{baseline_irrelevant}"
    )

    print(
        f"Optimized Irrelevant:      "
        f"{optimized_irrelevant}"
    )

    print(
        f"Irrelevant Reduction:      "
        f"{irrelevant_reduction:.1f}%"
    )

    print(
        f"Baseline Results:          "
        f"{baseline_result_count}"
    )

    print(
        f"Optimized Results:         "
        f"{optimized_result_count}"
    )

    print("=" * 70)

    # --------------------------------------------------------------
    # Validation
    # --------------------------------------------------------------

    if optimized_hits != total:

        print(
            "RETRIEVAL OPTIMIZATION EVALUATION FAILED"
        )

        baseline_retriever.close()
        optimized_retriever.close()

        raise AssertionError(
            "Distance threshold removed a relevant "
            "retrieval result."
        )

    if optimized_irrelevant > baseline_irrelevant:

        print(
            "RETRIEVAL OPTIMIZATION EVALUATION FAILED"
        )

        baseline_retriever.close()
        optimized_retriever.close()

        raise AssertionError(
            "Optimization increased the number "
            "of irrelevant results."
        )

    print(
        "RETRIEVAL OPTIMIZATION EVALUATION PASSED"
    )

    # --------------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------------

    try:
        baseline_retriever.close()
    except Exception:
        pass

    try:
        optimized_retriever.close()
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