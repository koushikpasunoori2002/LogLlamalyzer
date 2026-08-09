"""
test_retriever.py

Tests the Retriever using ChromaDB and real embeddings.
"""

from pathlib import Path
import sys
import shutil


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.rag.retriever import Retriever
from backend.database.chroma import ChromaDatabase
from backend.llm.embeddings import EmbeddingManager


def main():

    database_path = (
        PROJECT_ROOT
        / "data"
        / "test_retriever"
    )

    database = ChromaDatabase(
        persist_directory=database_path,
        collection_name="retriever_test",
    )

    embedding_manager = EmbeddingManager()

    retriever = Retriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=3,
    )

    print("=" * 70)
    print("RETRIEVER TEST")
    print("=" * 70)

    # --------------------------------------------------------------
    # Clear previous test data
    # --------------------------------------------------------------

    database.clear()

    print("\nDatabase cleared.")

    # --------------------------------------------------------------
    # Documents
    # --------------------------------------------------------------

    documents = [
        "Failed password for root from 192.168.1.20 port 22 ssh2",
        "Failed password for admin from 192.168.1.30 port 22 ssh2",
        "Successful login for user osboxes",
        "System shutdown completed successfully",
        "Apache web server started successfully",
    ]

    ids = [
        "retriever_001",
        "retriever_002",
        "retriever_003",
        "retriever_004",
        "retriever_005",
    ]

    metadatas = [
        {
            "log_type": "auth",
            "severity": "HIGH",
            "source": "auth.log",
        },
        {
            "log_type": "auth",
            "severity": "HIGH",
            "source": "auth.log",
        },
        {
            "log_type": "auth",
            "severity": "INFO",
            "source": "auth.log",
        },
        {
            "log_type": "syslog",
            "severity": "INFO",
            "source": "syslog",
        },
        {
            "log_type": "apache",
            "severity": "INFO",
            "source": "apache.log",
        },
    ]

    # --------------------------------------------------------------
    # Generate embeddings
    # --------------------------------------------------------------

    print("\nGenerating embeddings...")

    embeddings = (
        embedding_manager.embed_texts(
            documents
        )
    )

    print(
        "Embedding shape:",
        embeddings.shape
    )

    # --------------------------------------------------------------
    # Store embeddings
    # --------------------------------------------------------------

    database.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    print("\nRecords stored:", database.count())

    if database.count() != 5:

        raise AssertionError(
            "Expected 5 records in ChromaDB."
        )

    print("Database Insert Test: PASS")

    # --------------------------------------------------------------
    # Query
    # --------------------------------------------------------------

    query = "failed password login attempt"

    print("\nQuery:")
    print(query)

    results = retriever.retrieve(
        query=query,
        top_k=3,
    )

    print("\nRetrieved Results")

    print("-" * 70)

    print(results)

    if not results["documents"]:

        raise AssertionError(
            "Retriever returned no documents."
        )

    print("\nRetriever Search Test: PASS")

    # --------------------------------------------------------------
    # Retrieved documents
    # --------------------------------------------------------------

    retrieved_documents = (
        retriever.retrieve_documents(
            query=query,
            top_k=3,
        )
    )

    print("\nRetrieved Documents")

    for index, document in enumerate(
        retrieved_documents,
        start=1,
    ):

        print(
            f"\nResult {index}:"
        )

        print(document)

    if len(retrieved_documents) == 0:

        raise AssertionError(
            "No documents were returned."
        )

    # --------------------------------------------------------------
    # Metadata
    # --------------------------------------------------------------

    retrieved_metadata = (
        retriever.retrieve_metadata(
            query=query,
            top_k=3,
        )
    )

    print("\nRetrieved Metadata")

    for metadata in retrieved_metadata:

        print(metadata)

    # --------------------------------------------------------------
    # Results with scores
    # --------------------------------------------------------------

    scored_results = (
        retriever.retrieve_with_scores(
            query=query,
            top_k=3,
        )
    )

    print("\nResults With Distances")

    for result in scored_results:

        print("\nDocument:")
        print(result["document"])

        print(
            "Distance:",
            result["distance"],
        )

    if not scored_results:

        raise AssertionError(
            "No scored results returned."
        )

    print(
        "\nScored Retrieval Test: PASS"
    )

    # --------------------------------------------------------------
    # Retriever information
    # --------------------------------------------------------------

    print("\nRetriever Information")

    print(retriever.info())

    # --------------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------------

    database.clear()

    if database.count() != 0:

        raise AssertionError(
            "Database cleanup failed."
        )

    retriever.close()

    print("\nDatabase Cleanup Test: PASS")

    print("\n" + "=" * 70)
    print("RETRIEVER TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()