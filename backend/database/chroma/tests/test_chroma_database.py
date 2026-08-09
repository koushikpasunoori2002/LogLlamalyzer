"""
test_chroma_database.py

Tests the ChromaDB vector database.
"""

from pathlib import Path
import sys

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[4]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.database.chroma import ChromaDatabase


def main():

    database_path = (
        PROJECT_ROOT
        / "data"
        / "test_chroma"
    )

    database = ChromaDatabase(
        persist_directory=database_path,
        collection_name="test_logs",
    )

    print("=" * 70)
    print("CHROMADB TEST")
    print("=" * 70)

    # --------------------------------------------------------------
    # Clear previous test data
    # --------------------------------------------------------------

    database.clear()

    print("\nDatabase cleared.")

    # --------------------------------------------------------------
    # Test embeddings
    # --------------------------------------------------------------

    embeddings = [
        np.random.rand(384).astype(float),
        np.random.rand(384).astype(float),
        np.random.rand(384).astype(float),
    ]

    ids = [
        "test_001",
        "test_002",
        "test_003",
    ]

    documents = [
        "Failed password for root from 192.168.1.20",
        "SSH connection established from 192.168.1.30",
        "User successfully logged into the system",
    ]

    metadatas = [
        {
            "log_type": "auth",
            "severity": "HIGH",
            "source": "auth.log",
        },
        {
            "log_type": "auth",
            "severity": "MEDIUM",
            "source": "auth.log",
        },
        {
            "log_type": "auth",
            "severity": "LOW",
            "source": "auth.log",
        },
    ]

    # --------------------------------------------------------------
    # Add records
    # --------------------------------------------------------------

    database.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    print("\nRecords Added")
    print("Count:", database.count())

    # --------------------------------------------------------------
    # Verify count
    # --------------------------------------------------------------

    if database.count() != 3:

        raise AssertionError(
            "Expected 3 records in the database."
        )

    print("Count Test: PASS")

    # --------------------------------------------------------------
    # Retrieve records
    # --------------------------------------------------------------

    records = database.get()

    print("\nStored Records")

    print(records)

    # --------------------------------------------------------------
    # Search
    # --------------------------------------------------------------

    query_embedding = embeddings[0]

    results = database.search(
        query_embedding=query_embedding,
        n_results=2,
    )

    print("\nSimilarity Search")

    print(results)

    if not results["ids"]:

        raise AssertionError(
            "Search returned no results."
        )

    print("Search Test: PASS")

    # --------------------------------------------------------------
    # Delete
    # --------------------------------------------------------------

    database.delete(
        ["test_003"]
    )

    print("\nAfter Delete")

    print("Count:", database.count())

    if database.count() != 2:

        raise AssertionError(
            "Delete operation failed."
        )

    print("Delete Test: PASS")

    # --------------------------------------------------------------
    # Database information
    # --------------------------------------------------------------

    print("\nDatabase Information")

    print(database.info())

    # --------------------------------------------------------------
    # Clear
    # --------------------------------------------------------------

    database.clear()

    print("\nAfter Clear")

    print("Count:", database.count())

    if database.count() != 0:

        raise AssertionError(
            "Clear operation failed."
        )

    print("Clear Test: PASS")

    # --------------------------------------------------------------
    # Finish
    # --------------------------------------------------------------

    database.close()

    print("\n" + "=" * 70)
    print("CHROMADB TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()