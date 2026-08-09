"""
test_rag_pipeline.py

End-to-end integration test for the RAG pipeline.

Pipeline:

Linux Log
    ↓
PreprocessingPipeline
    ↓
LogRecord
    ↓
ChunkManager
    ↓
EmbeddingManager
    ↓
ChromaDB
    ↓
Retriever
    ↓
Relevant Log Chunks
"""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.preprocessing.pipeline import PreprocessingPipeline
from backend.rag.chunking import ChunkManager
from backend.llm.embeddings import EmbeddingManager
from backend.database.chroma import ChromaDatabase
from backend.rag.retriever import Retriever


def main():

    print("=" * 70)
    print("RAG PIPELINE INTEGRATION TEST")
    print("=" * 70)

    # --------------------------------------------------------------
    # Dataset
    # --------------------------------------------------------------

    log_file = (
        PROJECT_ROOT
        / "dataset"
        / "raw"
        / "auth"
        / "auth.log"
    )

    if not log_file.exists():

        raise FileNotFoundError(
            f"Log file not found: {log_file}"
        )

    print("\nInput File")
    print(log_file)

    # --------------------------------------------------------------
    # Step 1 - Preprocessing
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("STEP 1 - PREPROCESSING")
    print("=" * 70)

    preprocessing_pipeline = (
        PreprocessingPipeline()
    )

    info, records = (
        preprocessing_pipeline
        .process_with_metadata(log_file)
    )

    print(f"Log Type       : {info.log_type}")
    print(f"Reader         : {info.reader}")
    print(f"Records Parsed : {len(records)}")

    if not records:

        raise AssertionError(
            "Preprocessing returned no records."
        )

    print("Preprocessing: PASS")

    # --------------------------------------------------------------
    # Step 2 - Chunking
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("STEP 2 - CHUNKING")
    print("=" * 70)

    chunk_manager = ChunkManager(
        chunk_size=500,
        overlap=50,
    )

    for record in records:

        chunk_manager.add_record(
            record=record,
            source=str(log_file.name),
        )

    chunks = chunk_manager.get_chunks()

    print(f"Records       : {len(records)}")
    print(f"Chunks Created: {len(chunks)}")

    if not chunks:

        raise AssertionError(
            "Chunking returned no chunks."
        )

    print("Chunking: PASS")

    # --------------------------------------------------------------
    # Step 3 - Embeddings
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("STEP 3 - EMBEDDINGS")
    print("=" * 70)

    embedding_manager = EmbeddingManager()

    chunk_embeddings = (
        embedding_manager.embed_chunks(
            chunks
        )
    )

    print(
        f"Embedding Shape: "
        f"{chunk_embeddings.shape}"
    )

    if len(chunk_embeddings) != len(chunks):

        raise AssertionError(
            "Number of embeddings does not "
            "match number of chunks."
        )

    print("Embedding Generation: PASS")

    # --------------------------------------------------------------
    # Step 4 - ChromaDB
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("STEP 4 - CHROMADB")
    print("=" * 70)

    database_path = (
        PROJECT_ROOT
        / "data"
        / "test_rag_pipeline"
    )

    database = ChromaDatabase(
        persist_directory=database_path,
        collection_name="rag_pipeline_test",
    )

    database.clear()

    ids = [
        chunk.chunk_id
        for chunk in chunks
    ]

    documents = [
        chunk.text
        for chunk in chunks
    ]

    metadatas = [
        {
            "chunk_id": chunk.chunk_id,
            "source": chunk.source,
        }
        for chunk in chunks
    ]

    database.add(
        ids=ids,
        embeddings=chunk_embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    stored_count = database.count()

    print(
        f"Chunks Stored: {stored_count}"
    )

    if stored_count != len(chunks):

        raise AssertionError(
            "Stored chunk count does not "
            "match generated chunk count."
        )

    print("ChromaDB Storage: PASS")

    # --------------------------------------------------------------
    # Step 5 - Retriever
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("STEP 5 - RETRIEVER")
    print("=" * 70)

    retriever = Retriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=3,
    )

    query = "failed password login attempt"

    print(f"Query: {query}")

    results = retriever.retrieve(
        query=query,
        top_k=3,
    )

    if not results.get("documents"):

        raise AssertionError(
            "Retriever returned no documents."
        )

    print("\nRetrieved Results")

    retrieved_documents = (
        results["documents"][0]
    )

    distances = (
        results.get("distances", [[]])[0]
    )

    for index, document in enumerate(
        retrieved_documents,
        start=1,
    ):

        print(
            f"\nResult {index}"
        )

        print(
            f"Document : {document}"
        )

        if index <= len(distances):

            print(
                f"Distance : "
                f"{distances[index - 1]}"
            )

    print("\nRetriever: PASS")

    # --------------------------------------------------------------
    # Final Verification
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("INTEGRATION SUMMARY")
    print("=" * 70)

    print(
        f"Log Records Parsed : {len(records)}"
    )

    print(
        f"Chunks Created     : {len(chunks)}"
    )

    print(
        f"Embeddings Created : {len(chunk_embeddings)}"
    )

    print(
        f"Vectors Stored     : {database.count()}"
    )

    print(
        f"Results Retrieved  : "
        f"{len(retrieved_documents)}"
    )

    # --------------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------------

    database.clear()

    if database.count() != 0:

        raise AssertionError(
            "Database cleanup failed."
        )

    retriever.close()

    print("\nCleanup: PASS")

    print("\n" + "=" * 70)
    print("RAG PIPELINE INTEGRATION TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()