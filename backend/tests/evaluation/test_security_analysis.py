"""
Security analysis baseline evaluation.

Establishes a measurable baseline for security-related log
analysis before introducing further Phase 38 improvements.
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
        / "security_analysis_test"
    )

    database = ChromaDatabase(
        persist_directory=database_path,
        collection_name="security_analysis_test",
    )

    embedding_manager = EmbeddingManager()

    print("=" * 70)
    print("SECURITY ANALYSIS BASELINE EVALUATION")
    print("=" * 70)

    # --------------------------------------------------------------
    # Clear previous records
    # --------------------------------------------------------------

    database.clear()

    print("\nDatabase cleared.")

    # --------------------------------------------------------------
    # Security analysis test dataset
    # --------------------------------------------------------------

    documents = [
        (
            "Failed SSH authentication attempts detected from "
            "192.168.1.30. Repeated password failures indicate "
            "possible brute force activity."
        ),
        (
            "Multiple failed login attempts were recorded for "
            "the root account. The activity may indicate a "
            "credential attack."
        ),
        (
            "A user executed sudo commands to obtain elevated "
            "privileges. Suspicious privilege escalation activity "
            "was detected."
        ),
        (
            "A suspicious executable was launched from a temporary "
            "directory. The process may indicate malware execution."
        ),
        (
            "Multiple connections were attempted against different "
            "network ports. The activity may indicate network "
            "scanning or reconnaissance."
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
        "security_001",
        "security_002",
        "security_003",
        "security_004",
        "security_005",
        "security_006",
        "security_007",
        "security_008",
        "security_009",
        "security_010",
    ]

    metadatas = [
        {
            "scenario": "ssh_brute_force",
            "security_relevant": True,
            "log_type": "auth",
            "severity": "HIGH",
            "source": "server-a",
        },
        {
            "scenario": "credential_attack",
            "security_relevant": True,
            "log_type": "auth",
            "severity": "HIGH",
            "source": "server-a",
        },
        {
            "scenario": "privilege_escalation",
            "security_relevant": True,
            "log_type": "auth",
            "severity": "HIGH",
            "source": "server-b",
        },
        {
            "scenario": "malware",
            "security_relevant": True,
            "log_type": "syslog",
            "severity": "HIGH",
            "source": "server-b",
        },
        {
            "scenario": "network_scanning",
            "security_relevant": True,
            "log_type": "syslog",
            "severity": "HIGH",
            "source": "server-c",
        },
        {
            "scenario": "normal_web_server",
            "security_relevant": False,
            "log_type": "apache",
            "severity": "INFO",
            "source": "server-a",
        },
        {
            "scenario": "normal_shutdown",
            "security_relevant": False,
            "log_type": "syslog",
            "severity": "INFO",
            "source": "server-b",
        },
        {
            "scenario": "successful_login",
            "security_relevant": False,
            "log_type": "auth",
            "severity": "INFO",
            "source": "server-c",
        },
        {
            "scenario": "normal_package_update",
            "security_relevant": False,
            "log_type": "dpkg",
            "severity": "INFO",
            "source": "server-a",
        },
        {
            "scenario": "normal_kernel_event",
            "security_relevant": False,
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
    # Store records
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
            "Expected all security analysis records "
            "to be stored."
        )

    print("Database Insert Test: PASS")

    # --------------------------------------------------------------
    # Create retriever
    # --------------------------------------------------------------

    retriever = Retriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=3,
        distance_threshold=0.98,
    )

    # --------------------------------------------------------------
    # Security analysis scenarios
    # --------------------------------------------------------------

    scenarios = [
        {
            "name": "SSH brute force",
            "query": (
                "failed SSH authentication brute force "
                "password attack"
            ),
            "expected": [
                "ssh_brute_force",
                "credential_attack",
            ],
        },
        {
            "name": "Privilege escalation",
            "query": (
                "suspicious sudo privilege escalation "
                "elevated privileges"
            ),
            "expected": [
                "privilege_escalation",
            ],
        },
        {
            "name": "Malware",
            "query": (
                "suspicious executable malware "
                "execution activity"
            ),
            "expected": [
                "malware",
            ],
        },
        {
            "name": "Network scanning",
            "query": (
                "network scanning suspicious connections "
                "port reconnaissance"
            ),
            "expected": [
                "network_scanning",
            ],
        },
        {
            "name": "Credential attack",
            "query": (
                "repeated failed login attempts "
                "credential attack"
            ),
            "expected": [
                "credential_attack",
                "ssh_brute_force",
            ],
        },
    ]

    # --------------------------------------------------------------
    # Baseline evaluation
    # --------------------------------------------------------------

    total_relevant = 0
    total_retrieved = 0
    total_irrelevant = 0
    scenario_hits = 0
    security_results = 0
    normal_results = 0

    print("\n" + "-" * 70)
    print("SECURITY SCENARIO ANALYSIS")
    print("-" * 70)

    for scenario in scenarios:

        results = retriever.retrieve(
            query=scenario["query"],
            top_k=3,
        )

        metadata_results = retriever.retrieve_metadata(
            query=scenario["query"],
            top_k=3,
        )

        retrieved_scenarios = [
            metadata.get("scenario")
            for metadata in metadata_results
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

        security_count = sum(
            1
            for metadata in metadata_results
            if metadata.get("security_relevant") is True
        )

        normal_count = sum(
            1
            for metadata in metadata_results
            if metadata.get("security_relevant") is False
        )

        hit = any(
            expected in retrieved_scenarios
            for expected in scenario["expected"]
        )

        if hit:
            scenario_hits += 1

        total_relevant += relevant_count
        total_retrieved += len(retrieved_scenarios)
        total_irrelevant += irrelevant_count
        security_results += security_count
        normal_results += normal_count

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
            f"  Relevant: {relevant_count}"
        )

        print(
            f"  Irrelevant: {irrelevant_count}"
        )

        print(
            f"  Security-relevant results: "
            f"{security_count}"
        )

        print(
            f"  Result: "
            f"{'PASS' if hit else 'FAIL'}"
        )

    # --------------------------------------------------------------
    # Quantitative baseline metrics
    # --------------------------------------------------------------

    precision = (
        total_relevant / total_retrieved
        if total_retrieved
        else 0.0
    )

    total_expected = sum(
        len(scenario["expected"])
        for scenario in scenarios
    )

    recall = (
        total_relevant / total_expected
        if total_expected
        else 0.0
    )

    hit_rate = (
        scenario_hits / len(scenarios)
        if scenarios
        else 0.0
    )

    security_result_rate = (
        security_results / total_retrieved
        if total_retrieved
        else 0.0
    )

    # --------------------------------------------------------------
    # Source coverage
    # --------------------------------------------------------------

    source_values = set()

    for metadata in metadatas:
        source = metadata.get("source")

        if source:
            source_values.add(source)

    # --------------------------------------------------------------
    # Baseline results
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("SECURITY ANALYSIS BASELINE RESULTS")
    print("=" * 70)

    print(
        f"Security scenarios passed: "
        f"{scenario_hits}/{len(scenarios)}"
    )

    print(
        f"Hit Rate@3: "
        f"{hit_rate * 100:.1f}%"
    )

    print(
        f"Baseline Precision@3: "
        f"{precision * 100:.1f}%"
    )

    print(
        f"Baseline Recall@3: "
        f"{recall * 100:.1f}%"
    )

    print(
        f"Security-relevant retrieved results: "
        f"{security_results}"
    )

    print(
        f"Normal retrieved results: "
        f"{normal_results}"
    )

    print(
        f"Total retrieved results: "
        f"{total_retrieved}"
    )

    print(
        f"Irrelevant results: "
        f"{total_irrelevant}"
    )

    print(
        f"Synchronized sources: "
        f"{', '.join(sorted(source_values))}"
    )

    print(
        f"Security-result rate: "
        f"{security_result_rate * 100:.1f}%"
    )

    # --------------------------------------------------------------
    # Baseline validation
    # --------------------------------------------------------------

    if scenario_hits != len(scenarios):
        raise AssertionError(
            "Security analysis baseline failed: "
            "not all security scenarios were retrieved."
        )

    if not source_values:
        raise AssertionError(
            "Security analysis baseline failed: "
            "source metadata was not preserved."
        )

    if security_results == 0:
        raise AssertionError(
            "Security analysis baseline failed: "
            "no security-relevant results were retrieved."
        )

    print("\nBaseline security scenario validation: PASS")
    print("Source metadata validation: PASS")
    print("Security relevance validation: PASS")

    # --------------------------------------------------------------
    # Final result
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("SECURITY ANALYSIS BASELINE PASSED")
    print("=" * 70)

    # --------------------------------------------------------------
    # Close retriever before cleanup
    # --------------------------------------------------------------

    retriever.close()

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

    except (PermissionError, OSError) as error:

        print(
            "Database Cleanup: SKIPPED "
            f"({error})"
        )

    print("=" * 70)


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    main()