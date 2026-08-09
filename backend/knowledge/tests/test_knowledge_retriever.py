"""
test_knowledge_retriever.py

Tests semantic retrieval from the security knowledge base.
"""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.knowledge import (
    KnowledgeManager,
    KnowledgeIngestor,
    KnowledgeRetriever,
)

from backend.database.chroma import ChromaDatabase

from backend.llm.embeddings import EmbeddingManager


def main():

    print("=" * 70)
    print("KNOWLEDGE RETRIEVER TEST")
    print("=" * 70)

    # ----------------------------------------------------------
    # Knowledge file
    # ----------------------------------------------------------

    knowledge_file = (
        PROJECT_ROOT
        / "backend"
        / "knowledge"
        / "documents"
        / "test_knowledge.txt"
    )

    if not knowledge_file.exists():

        raise FileNotFoundError(
            f"Knowledge file not found: "
            f"{knowledge_file}"
        )

    # ----------------------------------------------------------
    # Load knowledge
    # ----------------------------------------------------------

    manager = KnowledgeManager()

    document = manager.load_file(
        knowledge_file,
        category="authentication",
    )

    print("\nKnowledge Loaded")
    print(
        f"Documents: {manager.count()}"
    )

    # ----------------------------------------------------------
    # Database
    # ----------------------------------------------------------

    database_path = (
        PROJECT_ROOT
        / "data"
        / "test_knowledge_retriever"
    )

    database = ChromaDatabase(
        persist_directory=database_path,
        collection_name="knowledge_retriever_test",
    )

    database.clear()

    # ----------------------------------------------------------
    # Embeddings
    # ----------------------------------------------------------

    embedding_manager = EmbeddingManager()

    # ----------------------------------------------------------
    # Ingest
    # ----------------------------------------------------------

    ingestor = KnowledgeIngestor(
        database=database,
        embedding_manager=embedding_manager,
        chunk_size=100,
        overlap=20,
    )

    chunks = ingestor.ingest_document(
        document
    )

    print(
        f"Chunks Stored: {len(chunks)}"
    )

    if not chunks:

        raise AssertionError(
            "No knowledge chunks were created."
        )

    print(
        "Knowledge Ingestion: PASS"
    )

    # ----------------------------------------------------------
    # Retriever
    # ----------------------------------------------------------

    retriever = KnowledgeRetriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=2,
    )

    query = (
        "repeated failed SSH login attempts "
        "brute force attack"
    )

    print("\nQuery")
    print(query)

    results = retriever.retrieve(
        query=query,
        top_k=2,
    )

    # ----------------------------------------------------------
    # Verify results
    # ----------------------------------------------------------

    documents = results.get(
        "documents",
        [[]],
    )[0]

    metadatas = results.get(
        "metadatas",
        [[]],
    )[0]

    distances = results.get(
        "distances",
        [[]],
    )[0]

    if not documents:

        raise AssertionError(
            "Knowledge retriever returned "
            "no documents."
        )

    print("\n" + "=" * 70)
    print("RETRIEVED KNOWLEDGE")
    print("=" * 70)

    for index, document_text in enumerate(
        documents,
        start=1,
    ):

        print(
            f"\nResult {index}"
        )

        print(
            f"Document : {document_text}"
        )

        if index <= len(metadatas):

            print(
                f"Metadata : "
                f"{metadatas[index - 1]}"
            )

        if index <= len(distances):

            print(
                f"Distance : "
                f"{distances[index - 1]}"
            )

    print(
        "\nKnowledge Retrieval: PASS"
    )

    # ----------------------------------------------------------
    # Information
    # ----------------------------------------------------------

    print("\nRetriever Information")

    print(
        retriever.info()
    )

    # ----------------------------------------------------------
    # Cleanup
    # ----------------------------------------------------------

    database.clear()

    if database.count() != 0:

        raise AssertionError(
            "Knowledge database cleanup failed."
        )

    print(
        "\nCleanup: PASS"
    )

    retriever.close()

    print("\n" + "=" * 70)
    print(
        "KNOWLEDGE RETRIEVER TEST PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
    