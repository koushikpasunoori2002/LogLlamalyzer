"""
test_knowledge_pipeline.py

End-to-end integration test for the Phase 14
security knowledge pipeline.

Pipeline:

Knowledge File
    ↓
TextKnowledgeLoader
    ↓
KnowledgeDocument
    ↓
KnowledgeManager
    ↓
Chunking
    ↓
Embeddings
    ↓
ChromaDB
    ↓
KnowledgeRetriever
    ↓
Relevant Security Knowledge
"""

from pathlib import Path
import sys


# --------------------------------------------------------------
# Project Root
# --------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --------------------------------------------------------------
# Imports
# --------------------------------------------------------------

from backend.knowledge import (
    KnowledgeManager,
    KnowledgeIngestor,
    KnowledgeRetriever,
)

from backend.database.chroma import ChromaDatabase

from backend.llm.embeddings import EmbeddingManager


# --------------------------------------------------------------
# Main Test
# --------------------------------------------------------------

def main():

    print("=" * 70)
    print("PHASE 14 KNOWLEDGE PIPELINE INTEGRATION TEST")
    print("=" * 70)

    # ----------------------------------------------------------
    # Step 1 — Knowledge File
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

    print("\nInput Knowledge File")
    print(knowledge_file)

    # ----------------------------------------------------------
    # Step 2 — Knowledge Manager
    # ----------------------------------------------------------

    print("\n" + "=" * 70)
    print("STEP 1 - KNOWLEDGE MANAGEMENT")
    print("=" * 70)

    manager = KnowledgeManager()

    document = manager.load_file(
        file_path=knowledge_file,
        category="authentication",
    )

    print(
        f"Documents Loaded : "
        f"{manager.count()}"
    )

    print(
        f"Document ID      : "
        f"{document.document_id}"
    )

    print(
        f"Category         : "
        f"{document.category}"
    )

    if manager.count() != 1:

        raise AssertionError(
            "Expected exactly one knowledge document."
        )

    print("Knowledge Management: PASS")

    # ----------------------------------------------------------
    # Step 3 — Database
    # ----------------------------------------------------------

    print("\n" + "=" * 70)
    print("STEP 2 - VECTOR DATABASE")
    print("=" * 70)

    database_path = (
        PROJECT_ROOT
        / "data"
        / "test_knowledge_pipeline"
    )

    database = ChromaDatabase(
        persist_directory=database_path,
        collection_name="knowledge_pipeline_test",
    )

    database.clear()

    print(
        f"Collection       : "
        f"knowledge_pipeline_test"
    )

    print(
        "Database cleared."
    )

    # ----------------------------------------------------------
    # Step 4 — Embedding Manager
    # ----------------------------------------------------------

    print("\n" + "=" * 70)
    print("STEP 3 - EMBEDDING MODEL")
    print("=" * 70)

    embedding_manager = EmbeddingManager()

    embedding_info = (
        embedding_manager.model_information()
    )

    print(
        f"Model            : "
        f"{embedding_info['model']}"
    )

    print(
        f"Dimension        : "
        f"{embedding_info['dimension']}"
    )

    if embedding_info["dimension"] != 384:

        raise AssertionError(
            "Unexpected embedding dimension."
        )

    print("Embedding Model: PASS")

    # ----------------------------------------------------------
    # Step 5 — Knowledge Ingestion
    # ----------------------------------------------------------

    print("\n" + "=" * 70)
    print("STEP 4 - KNOWLEDGE INGESTION")
    print("=" * 70)

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
        f"Chunks Created   : "
        f"{len(chunks)}"
    )

    print(
        f"Vectors Stored   : "
        f"{database.count()}"
    )

    if not chunks:

        raise AssertionError(
            "No knowledge chunks were created."
        )

    if database.count() != len(chunks):

        raise AssertionError(
            "Vector count does not match "
            "chunk count."
        )

    print("Knowledge Ingestion: PASS")

    # ----------------------------------------------------------
    # Step 6 — Knowledge Retrieval
    # ----------------------------------------------------------

    print("\n" + "=" * 70)
    print("STEP 5 - KNOWLEDGE RETRIEVAL")
    print("=" * 70)

    retriever = KnowledgeRetriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=2,
    )

    query = (
        "failed SSH authentication "
        "brute force attack"
    )

    print(
        f"Query            : "
        f"{query}"
    )

    results = retriever.retrieve(
        query=query,
        top_k=2,
    )

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
            "Knowledge retrieval returned no results."
        )

    print("\nRetrieved Knowledge")

    for index, text in enumerate(
        documents,
        start=1,
    ):

        print(
            f"\nResult {index}"
        )

        print(
            f"Document : {text}"
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
    # Step 7 — Verify Security Context
    # ----------------------------------------------------------

    print("\n" + "=" * 70)
    print("STEP 6 - SECURITY CONTEXT VERIFICATION")
    print("=" * 70)

    combined_text = " ".join(
        documents
    ).lower()

    security_terms = [
        "ssh",
        "authentication",
        "brute-force",
    ]

    matched_terms = [
        term
        for term in security_terms
        if term in combined_text
    ]

    print(
        f"Security Terms Found : "
        f"{matched_terms}"
    )

    if not matched_terms:

        raise AssertionError(
            "Retrieved knowledge does not "
            "contain expected security context."
        )

    print(
        "Security Context: PASS"
    )

    # ----------------------------------------------------------
    # Step 8 — Final Information
    # ----------------------------------------------------------

    print("\n" + "=" * 70)
    print("PIPELINE SUMMARY")
    print("=" * 70)

    print(
        f"Documents Loaded : "
        f"{manager.count()}"
    )

    print(
        f"Chunks Created   : "
        f"{len(chunks)}"
    )

    print(
        f"Vectors Stored   : "
        f"{database.count()}"
    )

    print(
        f"Results Retrieved: "
        f"{len(documents)}"
    )

    print(
        f"Security Terms   : "
        f"{matched_terms}"
    )

    # ----------------------------------------------------------
    # Step 9 — Cleanup
    # ----------------------------------------------------------

    database.clear()

    if database.count() != 0:

        raise AssertionError(
            "Database cleanup failed."
        )

    print(
        "\nCleanup: PASS"
    )

    retriever.close()

    # ----------------------------------------------------------
    # Final Result
    # ----------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        "PHASE 14 KNOWLEDGE PIPELINE "
        "INTEGRATION TEST PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":

    main()