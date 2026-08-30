"""
Multi-source retrieval evaluation.

Evaluates retrieval across multiple synchronized sources
using the synchronized_source metadata field.

Tests:
1. Cross-source retrieval
2. Source-aware retrieval
3. Source isolation
4. Retrieval quality across multiple sources
5. Source metadata preservation
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
        / "multi_source_retrieval_test"
    )

    database = ChromaDatabase(
        persist_directory=database_path,
        collection_name="multi_source_retrieval_test",
    )

    embedding_manager = EmbeddingManager()

    print("=" * 70)
    print("MULTI-SOURCE RETRIEVAL EVALUATION")
    print("=" * 70)

    # --------------------------------------------------------------
    # Clear previous records
    # --------------------------------------------------------------

    database.clear()

    print("\nDatabase cleared.")

    # --------------------------------------------------------------
    # Multi-source test documents
    # --------------------------------------------------------------

    documents = [

        # ----------------------------------------------------------
        # server-a
        # ----------------------------------------------------------

        (
            "Server A detected multiple failed SSH authentication "
            "attempts from a remote IP address. The repeated "
            "password failures may indicate an SSH brute force attack."
        ),

        (
            "Server A recorded repeated failed login attempts "
            "for the root account. The activity may indicate "
            "a credential attack."
        ),

        (
            "Server A web server started successfully and is "
            "operating normally."
        ),

        # ----------------------------------------------------------
        # server-b
        # ----------------------------------------------------------

        (
            "Server B detected suspicious sudo activity where "
            "a user attempted to obtain elevated privileges. "
            "This may indicate privilege escalation."
        ),

        (
            "Server B recorded a suspicious executable launched "
            "from a temporary directory. The process may indicate "
            "malware execution."
        ),

        (
            "Server B completed a normal software update successfully."
        ),

        # ----------------------------------------------------------
        # server-c
        # ----------------------------------------------------------

        (
            "Server C detected repeated connection attempts "
            "against multiple network ports. The activity may "
            "indicate network scanning or reconnaissance."
        ),

        (
            "Server C detected another series of suspicious "
            "network connections associated with reconnaissance activity."
        ),

        (
            "Server C completed a normal system shutdown operation."
        ),

        (
            "Server C recorded a successful user login."
        ),
    ]

    ids = [
        "multi_source_001",
        "multi_source_002",
        "multi_source_003",
        "multi_source_004",
        "multi_source_005",
        "multi_source_006",
        "multi_source_007",
        "multi_source_008",
        "multi_source_009",
        "multi_source_010",
    ]

    metadatas = [

        # server-a
        {
            "synchronized_source": "server-a",
            "log_type": "auth",
            "severity": "HIGH",
            "scenario": "ssh_authentication",
        },
        {
            "synchronized_source": "server-a",
            "log_type": "auth",
            "severity": "MEDIUM",
            "scenario": "failed_login",
        },
        {
            "synchronized_source": "server-a",
            "log_type": "apache",
            "severity": "INFO",
            "scenario": "normal_web_server",
        },

        # server-b
        {
            "synchronized_source": "server-b",
            "log_type": "auth",
            "severity": "HIGH",
            "scenario": "privilege_escalation",
        },
        {
            "synchronized_source": "server-b",
            "log_type": "syslog",
            "severity": "HIGH",
            "scenario": "malware",
        },
        {
            "synchronized_source": "server-b",
            "log_type": "dpkg",
            "severity": "INFO",
            "scenario": "normal_package_update",
        },

        # server-c
        {
            "synchronized_source": "server-c",
            "log_type": "syslog",
            "severity": "HIGH",
            "scenario": "network_scanning",
        },
        {
            "synchronized_source": "server-c",
            "log_type": "syslog",
            "severity": "HIGH",
            "scenario": "network_connections",
        },
        {
            "synchronized_source": "server-c",
            "log_type": "syslog",
            "severity": "INFO",
            "scenario": "normal_shutdown",
        },
        {
            "synchronized_source": "server-c",
            "log_type": "auth",
            "severity": "INFO",
            "scenario": "successful_login",
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
        embeddings.shape,
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
            "Expected all multi-source records "
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
    )

    # ==============================================================
    # TEST 1 - CROSS-SOURCE RETRIEVAL
    # ==============================================================

    print("\n" + "-" * 70)
    print("TEST 1 - CROSS-SOURCE RETRIEVAL")

    query = (
        "suspicious authentication and failed login activity"
    )

    results = retriever.retrieve(
        query=query,
        top_k=5,
    )

    metadata = retriever.retrieve_metadata(
        query=query,
        top_k=5,
    )

    sources = [
        item.get("synchronized_source")
        for item in metadata
    ]

    print("Query:")
    print(query)

    print("\nRetrieved sources:")
    print(sources)

    unique_sources = set(sources)

    print(
        "Unique synchronized sources:",
        sorted(unique_sources),
    )

    if not results["documents"]:

        raise AssertionError(
            "Cross-source retrieval returned no results."
        )

    if len(unique_sources) < 2:

        raise AssertionError(
            "Cross-source retrieval did not retrieve "
            "results from multiple synchronized sources."
        )

    print("Cross-source retrieval test: PASS")

    # ==============================================================
    # TEST 2 - SERVER-A SOURCE FILTER
    # ==============================================================

    print("\n" + "-" * 70)
    print("TEST 2 - SERVER-A SOURCE FILTER")

    query = "failed SSH authentication login attempts"

    results = retriever.retrieve(
        query=query,
        top_k=3,
        source="server-a",
    )

    metadata = retriever.retrieve_metadata(
        query=query,
        top_k=3,
        source="server-a",
    )

    sources = [
        item.get("synchronized_source")
        for item in metadata
    ]

    print("Query:")
    print(query)

    print("Retrieved sources:")
    print(sources)

    if not sources:

        raise AssertionError(
            "Server-A retrieval returned no results."
        )

    if any(
        source != "server-a"
        for source in sources
    ):

        raise AssertionError(
            "Source filtering returned a result "
            "from another synchronized source."
        )

    print("Server-A source filtering test: PASS")

    # ==============================================================
    # TEST 3 - SERVER-B SOURCE FILTER
    # ==============================================================

    print("\n" + "-" * 70)
    print("TEST 3 - SERVER-B SOURCE FILTER")

    query = (
        "suspicious sudo privilege escalation activity"
    )

    results = retriever.retrieve(
        query=query,
        top_k=3,
        source="server-b",
    )

    metadata = retriever.retrieve_metadata(
        query=query,
        top_k=3,
        source="server-b",
    )

    sources = [
        item.get("synchronized_source")
        for item in metadata
    ]

    print("Query:")
    print(query)

    print("Retrieved sources:")
    print(sources)

    if not sources:

        raise AssertionError(
            "Server-B retrieval returned no results."
        )

    if any(
        source != "server-b"
        for source in sources
    ):

        raise AssertionError(
            "Source filtering returned a result "
            "from another synchronized source."
        )

    print("Server-B source filtering test: PASS")

    # ==============================================================
    # TEST 4 - SERVER-C SOURCE FILTER
    # ==============================================================

    print("\n" + "-" * 70)
    print("TEST 4 - SERVER-C SOURCE FILTER")

    query = (
        "network scanning suspicious connections"
    )

    results = retriever.retrieve(
        query=query,
        top_k=3,
        source="server-c",
    )

    metadata = retriever.retrieve_metadata(
        query=query,
        top_k=3,
        source="server-c",
    )

    sources = [
        item.get("synchronized_source")
        for item in metadata
    ]

    print("Query:")
    print(query)

    print("Retrieved sources:")
    print(sources)

    if not sources:

        raise AssertionError(
            "Server-C retrieval returned no results."
        )

    if any(
        source != "server-c"
        for source in sources
    ):

        raise AssertionError(
            "Source filtering returned a result "
            "from another synchronized source."
        )

    print("Server-C source filtering test: PASS")

    # ==============================================================
    # TEST 5 - SOURCE ISOLATION
    # ==============================================================

    print("\n" + "-" * 70)
    print("TEST 5 - SOURCE ISOLATION")

    source_checks = [
        (
            "server-a",
            "failed login authentication",
        ),
        (
            "server-b",
            "malware execution",
        ),
        (
            "server-c",
            "network scanning",
        ),
    ]

    for source, query in source_checks:

        metadata = retriever.retrieve_metadata(
            query=query,
            top_k=3,
            source=source,
        )

        returned_sources = [
            item.get("synchronized_source")
            for item in metadata
        ]

        print(
            f"{source}: {returned_sources}"
        )

        if any(
            value != source
            for value in returned_sources
        ):

            raise AssertionError(
                f"Source isolation failed for {source}."
            )

    print("Source isolation test: PASS")

    # ==============================================================
    # TEST 6 - SOURCE METADATA PRESERVATION
    # ==============================================================

    print("\n" + "-" * 70)
    print("TEST 6 - SOURCE METADATA PRESERVATION")

    stored = database.get()

    stored_metadata = stored["metadatas"]

    stored_sources = [
        metadata.get("synchronized_source")
        for metadata in stored_metadata
    ]

    print(
        "Stored synchronized sources:"
    )
    print(
        sorted(set(stored_sources))
    )

    expected_sources = {
        "server-a",
        "server-b",
        "server-c",
    }

    if set(stored_sources) != expected_sources:

        raise AssertionError(
            "Expected synchronized source metadata "
            "was not preserved."
        )

    print("Source metadata preservation test: PASS")

    # ==============================================================
    # TEST 7 - MULTI-SOURCE RETRIEVAL QUALITY
    # ==============================================================

    print("\n" + "-" * 70)
    print("TEST 7 - MULTI-SOURCE RETRIEVAL QUALITY")

    scenarios = [
        {
            "name": "SSH authentication",
            "query": "failed SSH authentication brute force",
            "expected_source": "server-a",
        },
        {
            "name": "Privilege escalation",
            "query": "sudo privilege escalation",
            "expected_source": "server-b",
        },
        {
            "name": "Malware",
            "query": "suspicious malware execution",
            "expected_source": "server-b",
        },
        {
            "name": "Network scanning",
            "query": "network scanning suspicious connections",
            "expected_source": "server-c",
        },
    ]

    passed = 0

    for scenario in scenarios:

        metadata = retriever.retrieve_metadata(
            query=scenario["query"],
            top_k=3,
        )

        sources = [
            item.get("synchronized_source")
            for item in metadata
        ]

        hit = (
            scenario["expected_source"]
            in sources
        )

        print(
            f"{scenario['name']}: "
            f"{sources} | "
            f"{'PASS' if hit else 'FAIL'}"
        )

        if hit:
            passed += 1

    print(
        f"\nMulti-source scenarios passed: "
        f"{passed}/{len(scenarios)}"
    )

    if passed != len(scenarios):

        raise AssertionError(
            "Multi-source retrieval quality "
            "evaluation failed."
        )

    print("Multi-source retrieval quality test: PASS")

    # ==============================================================
    # FINAL SUMMARY
    # ==============================================================

    print("\n" + "=" * 70)
    print("MULTI-SOURCE RETRIEVAL RESULTS")
    print("=" * 70)

    print(
        "Synchronized sources evaluated: "
        "server-a, server-b, server-c"
    )

    print(
        "Cross-source retrieval: PASS"
    )

    print(
        "Source filtering: PASS"
    )

    print(
        "Source isolation: PASS"
    )

    print(
        "Metadata preservation: PASS"
    )

    print(
        "Multi-source retrieval quality: PASS"
    )

    print("\n" + "=" * 70)
    print("MULTI-SOURCE RETRIEVAL EVALUATION PASSED")
    print("=" * 70)

    # --------------------------------------------------------------
    # Close retriever
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

    except Exception as error:

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