"""
Retrieval distance analysis.

Evaluates the distance distribution of retrieved documents
for representative security scenarios.

This evaluation is used to determine whether retrieved
documents show a meaningful separation between relevant
and irrelevant results before introducing retrieval
filtering.
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
        / "retrieval_distance_test"
    )

    # --------------------------------------------------------------
    # Create database
    # --------------------------------------------------------------

    database = ChromaDatabase(
        persist_directory=database_path,
        collection_name="retrieval_distance_test",
    )

    embedding_manager = EmbeddingManager()

    retriever = Retriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=3,
    )

    print("=" * 70)
    print("RETRIEVAL DISTANCE ANALYSIS")
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
        "distance_001",
        "distance_002",
        "distance_003",
        "distance_004",
        "distance_005",
        "distance_006",
        "distance_007",
        "distance_008",
        "distance_009",
        "distance_010",
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
    # Run distance analysis
    # --------------------------------------------------------------

    all_distances = []
    relevant_distances = []
    irrelevant_distances = []

    scenario_results = []

    print("\nRunning distance analysis...")

    for scenario in scenarios:

        results = retriever.retrieve_with_scores(
            query=scenario["query"],
            top_k=3,
        )

        if not results:

            print(
                f"\nFAIL: {scenario['name']}"
            )

            scenario_results.append(
                {
                    "name": scenario["name"],
                    "passed": False,
                    "relevant_distances": [],
                    "irrelevant_distances": [],
                }
            )

            continue

        retrieved_metadata = (
            retriever.retrieve_metadata(
                query=scenario["query"],
                top_k=3,
            )
        )

        scenario_relevant_distances = []
        scenario_irrelevant_distances = []

        for index, result in enumerate(results):

            distance = result["distance"]

            if distance is None:
                continue

            all_distances.append(distance)

            metadata = (
                retrieved_metadata[index]
                if index < len(retrieved_metadata)
                else {}
            )

            retrieved_scenario = metadata.get(
                "scenario"
            )

            is_relevant = (
                retrieved_scenario
                in scenario["expected"]
            )

            if is_relevant:

                relevant_distances.append(
                    distance
                )

                scenario_relevant_distances.append(
                    distance
                )

            else:

                irrelevant_distances.append(
                    distance
                )

                scenario_irrelevant_distances.append(
                    distance
                )

        retrieved_scenarios = [
            metadata.get("scenario")
            for metadata in retrieved_metadata
        ]

        relevant_found = any(
            expected in retrieved_scenarios
            for expected in scenario["expected"]
        )

        scenario_results.append(
            {
                "name": scenario["name"],
                "passed": relevant_found,
                "relevant_distances": (
                    scenario_relevant_distances
                ),
                "irrelevant_distances": (
                    scenario_irrelevant_distances
                ),
            }
        )

        print(
            f"\n{scenario['name']}"
        )

        print(
            f"  Query: {scenario['query']}"
        )

        print(
            f"  Retrieved: {retrieved_scenarios}"
        )

        print(
            f"  Expected: {scenario['expected']}"
        )

        print(
            "  Results:"
        )

        for index, result in enumerate(
            results,
            start=1,
        ):

            metadata_index = index - 1

            metadata = (
                retrieved_metadata[
                    metadata_index
                ]
                if metadata_index
                < len(retrieved_metadata)
                else {}
            )

            retrieved_scenario = metadata.get(
                "scenario",
                "unknown",
            )

            distance = result["distance"]

            if (
                retrieved_scenario
                in scenario["expected"]
            ):

                relevance_label = "RELEVANT"

            else:

                relevance_label = "IRRELEVANT"

            print(
                f"    {index}. "
                f"{retrieved_scenario} | "
                f"distance={distance:.6f} | "
                f"{relevance_label}"
            )

        if relevant_found:

            print(
                "  Retrieval Hit: PASS"
            )

        else:

            print(
                "  Retrieval Hit: FAIL"
            )

    # --------------------------------------------------------------
    # Calculate summary statistics
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("DISTANCE ANALYSIS SUMMARY")
    print("=" * 70)

    if all_distances:

        minimum_distance = min(
            all_distances
        )

        maximum_distance = max(
            all_distances
        )

        mean_distance = (
            sum(all_distances)
            / len(all_distances)
        )

        print(
            f"All retrieved distances: "
            f"{len(all_distances)}"
        )

        print(
            f"Minimum distance: "
            f"{minimum_distance:.6f}"
        )

        print(
            f"Maximum distance: "
            f"{maximum_distance:.6f}"
        )

        print(
            f"Mean distance: "
            f"{mean_distance:.6f}"
        )

    else:

        print(
            "No distances were returned."
        )

    # --------------------------------------------------------------
    # Relevant distance statistics
    # --------------------------------------------------------------

    print("\nRelevant result distances")

    if relevant_distances:

        relevant_min = min(
            relevant_distances
        )

        relevant_max = max(
            relevant_distances
        )

        relevant_mean = (
            sum(relevant_distances)
            / len(relevant_distances)
        )

        print(
            f"Count: "
            f"{len(relevant_distances)}"
        )

        print(
            f"Minimum: "
            f"{relevant_min:.6f}"
        )

        print(
            f"Maximum: "
            f"{relevant_max:.6f}"
        )

        print(
            f"Mean: "
            f"{relevant_mean:.6f}"
        )

    else:

        relevant_min = None
        relevant_max = None
        relevant_mean = None

        print(
            "No relevant distances recorded."
        )

    # --------------------------------------------------------------
    # Irrelevant distance statistics
    # --------------------------------------------------------------

    print("\nIrrelevant result distances")

    if irrelevant_distances:

        irrelevant_min = min(
            irrelevant_distances
        )

        irrelevant_max = max(
            irrelevant_distances
        )

        irrelevant_mean = (
            sum(irrelevant_distances)
            / len(irrelevant_distances)
        )

        print(
            f"Count: "
            f"{len(irrelevant_distances)}"
        )

        print(
            f"Minimum: "
            f"{irrelevant_min:.6f}"
        )

        print(
            f"Maximum: "
            f"{irrelevant_max:.6f}"
        )

        print(
            f"Mean: "
            f"{irrelevant_mean:.6f}"
        )

    else:

        irrelevant_min = None
        irrelevant_max = None
        irrelevant_mean = None

        print(
            "No irrelevant distances recorded."
        )

    # --------------------------------------------------------------
    # Distance overlap analysis
    # --------------------------------------------------------------

    print("\nDistance separation analysis")

    if (
        relevant_distances
        and irrelevant_distances
    ):

        closest_irrelevant = min(
            irrelevant_distances
        )

        furthest_relevant = max(
            relevant_distances
        )

        print(
            f"Furthest relevant distance: "
            f"{furthest_relevant:.6f}"
        )

        print(
            f"Closest irrelevant distance: "
            f"{closest_irrelevant:.6f}"
        )

        separation_margin = (
            closest_irrelevant
            - furthest_relevant
        )

        print(
            f"Distance separation margin: "
            f"{separation_margin:.6f}"
        )

        if separation_margin > 0:

            print(
                "Clear distance separation detected."
            )

        else:

            print(
                "Distance overlap detected."
            )

    else:

        separation_margin = None

        print(
            "Insufficient data for separation analysis."
        )

    # --------------------------------------------------------------
    # Retrieval success summary
    # --------------------------------------------------------------

    passed_count = sum(
        1
        for result in scenario_results
        if result["passed"]
    )

    total = len(scenarios)

    print("\n" + "=" * 70)

    print(
        f"Retrieval scenarios passed: "
        f"{passed_count}/{total}"
    )

    if total > 0:

        hit_rate = (
            passed_count
            / total
            * 100
        )

    else:

        hit_rate = 0.0

    print(
        f"Hit Rate@3: "
        f"{hit_rate:.1f}%"
    )

    print("=" * 70)

    # --------------------------------------------------------------
    # Evaluation validation
    # --------------------------------------------------------------

    if passed_count != total:

        retriever.close()

        raise AssertionError(
            "One or more retrieval scenarios failed."
        )

    if not all_distances:

        retriever.close()

        raise AssertionError(
            "No retrieval distances were returned."
        )

    print(
        "\nRETRIEVAL DISTANCE ANALYSIS PASSED"
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

    print(
        "=" * 70
    )


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    main()