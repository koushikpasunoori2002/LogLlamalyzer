"""
test_knowledge_ingestor.py

Tests the KnowledgeIngestor.

Pipeline:

KnowledgeDocument
    ↓
Chunking
    ↓
Embedding
    ↓
ChromaDB
"""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.knowledge import (
    KnowledgeManager,
    KnowledgeIngestor,
)

from backend.database.chroma import (
    ChromaDatabase,
)

from backend.llm.embeddings import (
    EmbeddingManager,
)


def main():

    print("=" * 70)
    print("KNOWLEDGE INGESTOR TEST")
    print("=" * 70)

    # ----------------------------------------------------------
    # Test knowledge file
    # ----------------------------------------------------------

    knowledge_file = (
        PROJECT_ROOT
        / "documents"
        / "test_knowledge.txt"
    )

    # The actual test document is located here
    # relative to the project root.
    if not knowledge_file.exists():

        knowledge_file = (
            PROJECT_ROOT
            / "knowledge"
            / "documents"
            / "test_knowledge.txt"
        )

    # Fallback to the backend location.
    if not knowledge_file.exists():

        knowledge_file = (
            PROJECT_ROOT
            / "backend"
            / "knowledge"
            / "documents"
            / "test_knowledge.txt"
        )

    if not knowledge_file.exists():

        raise FileNotFoundError(
            "test_knowledge.txt was not found."
        )

    print("\nKnowledge File")
    print(knowledge_file)

    # ----------------------------------------------------------
    # Knowledge Manager
    # ----------------------------------------------------------

    manager = KnowledgeManager()

    document = manager.load_file(
        file_path=knowledge_file,
        category="authentication",
    )

    print("\nKnowledge Document")
    print(document)

    if manager.count() != 1:

        raise AssertionError(
            "KnowledgeManager should contain "
            "one document."
        )

    print("\nKnowledgeManager: PASS")

    # ----------------------------------------------------------
    # Test ChromaDB
    # ----------------------------------------------------------

    database_path = (
        PROJECT_ROOT
        / "data"
        / "test_knowledge"
    )

    database = ChromaDatabase(
        persist_directory=database_path,
        collection_name="knowledge_test",
    )

    database.clear()

    # ----------------------------------------------------------
    # Embedding Manager
    # ----------------------------------------------------------

    embedding_manager = EmbeddingManager()

    # ----------------------------------------------------------
    # Knowledge Ingestor
    # ----------------------------------------------------------

    ingestor = KnowledgeIngestor(
        database=database,
        embedding_manager=embedding_manager,
        chunk_size=100,
        overlap=20,
    )

    print("\n" + "=" * 70)
    print("INGESTING KNOWLEDGE")
    print("=" * 70)

    chunks = ingestor.ingest_document(
        document
    )

    print(
        f"\nChunks Created : {len(chunks)}"
    )

    print(
        f"Vectors Stored : {ingestor.count()}"
    )

    if not chunks:

        raise AssertionError(
            "Knowledge ingestion created "
            "no chunks."
        )

    if ingestor.count() != len(chunks):

        raise AssertionError(
            "Stored vector count does not "
            "match chunk count."
        )

    print(
        "\nKnowledge Ingestion: PASS"
    )

    # ----------------------------------------------------------
    # Inspect stored data
    # ----------------------------------------------------------

    stored = database.get()

    print("\nStored Knowledge")

    print(
        f"IDs: {stored['ids']}"
    )

    print(
        f"Documents: {stored['documents']}"
    )

    print(
        f"Metadata: {stored['metadatas']}"
    )

    # ----------------------------------------------------------
    # Verify metadata
    # ----------------------------------------------------------

    metadata = stored["metadatas"][0]

    if metadata["document_id"] != (
        document.document_id
    ):

        raise AssertionError(
            "Document ID metadata is incorrect."
        )

    if metadata["category"] != (
        document.category
    ):

        raise AssertionError(
            "Category metadata is incorrect."
        )

    if metadata["source"] != (
        document.source
    ):

        raise AssertionError(
            "Source metadata is incorrect."
        )

    print(
        "\nMetadata Test: PASS"
    )

    # ----------------------------------------------------------
    # Database information
    # ----------------------------------------------------------

    print("\nIngestor Information")

    print(
        ingestor.info()
    )

    # ----------------------------------------------------------
    # Cleanup
    # ----------------------------------------------------------

    ingestor.clear()

    if ingestor.count() != 0:

        raise AssertionError(
            "Knowledge database cleanup failed."
        )

    print(
        "\nCleanup: PASS"
    )

    ingestor.close()

    print("\n" + "=" * 70)
    print(
        "KNOWLEDGE INGESTOR TEST PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()