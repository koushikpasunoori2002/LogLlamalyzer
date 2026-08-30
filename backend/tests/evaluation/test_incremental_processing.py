"""
Incremental processing evaluation.

Verifies that synchronized log ingestion:

- indexes new records
- skips identical records
- avoids unnecessary embedding generation
- indexes genuinely new records
- handles mixed batches incrementally
- preserves source metadata
"""

from pathlib import Path
import shutil
import sys


# ------------------------------------------------------------------
# Project path
# ------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# ------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------

from backend.database.chroma import ChromaDatabase
from backend.llm.embeddings import EmbeddingManager
from backend.rag.chunking import ChunkManager
from backend.synchronization.ingestion.synchronized_log_ingestor import (
    SynchronizedLogIngestor,
)


# ------------------------------------------------------------------
# Test record
# ------------------------------------------------------------------

class TestRecord:
    """
    Minimal LogRecord-compatible object.
    """

    def __init__(
        self,
        message,
        source_file,
        event_id,
    ):

        self.message = message
        self.source_file = source_file
        self.event_id = event_id

    def to_dict(self):

        return {
            "message": self.message,
            "source_file": self.source_file,
            "event_id": self.event_id,
        }


# ------------------------------------------------------------------
# Counting embedding manager
# ------------------------------------------------------------------

class CountingEmbeddingManager(
    EmbeddingManager
):
    """
    Records how many chunks are actually embedded.
    """

    def __init__(self):

        super().__init__()

        self.total_chunks_embedded = 0
        self.embedding_calls = 0

    def embed_chunks(
        self,
        chunks,
    ):

        self.embedding_calls += 1

        self.total_chunks_embedded += len(
            chunks
        )

        return super().embed_chunks(
            chunks
        )


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():

    database_path = (
        PROJECT_ROOT
        / "data"
        / "incremental_processing_test"
    )

    if database_path.exists():

        try:

            shutil.rmtree(
                database_path
            )

        except PermissionError:

            pass

    database = ChromaDatabase(
        persist_directory=database_path,
        collection_name="incremental_processing_test",
    )

    embedding_manager = (
        CountingEmbeddingManager()
    )

    chunk_manager = ChunkManager(
        chunk_size=500,
        overlap=50,
    )

    ingestor = SynchronizedLogIngestor(
        database=database,
        embedding_manager=embedding_manager,
        chunk_manager=chunk_manager,
    )

    print("=" * 70)
    print("INCREMENTAL PROCESSING EVALUATION")
    print("=" * 70)

    database.clear()

    # --------------------------------------------------------------
    # Records
    # --------------------------------------------------------------

    record_one = TestRecord(
        message=(
            "Failed SSH authentication attempt "
            "from 192.168.1.20"
        ),
        source_file="server-a/auth.log",
        event_id="event-001",
    )

    record_two = TestRecord(
        message=(
            "User executed sudo command to obtain "
            "elevated privileges"
        ),
        source_file="server-b/auth.log",
        event_id="event-002",
    )

    record_three = TestRecord(
        message=(
            "Multiple network connections were "
            "attempted against different ports"
        ),
        source_file="server-c/network.log",
        event_id="event-003",
    )

    # --------------------------------------------------------------
    # TEST 1 - FIRST INGESTION
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 1 - FIRST INGESTION")

    first_chunks = (
        ingestor.ingest_source_records(
            source_id="server-a",
            records=[
                record_one,
            ],
        )
    )

    first_count = database.count()

    first_stats = (
        ingestor.ingestion_statistics()
    )

    print(
        "Chunks indexed:",
        len(first_chunks),
    )

    print(
        "Database count:",
        first_count,
    )

    print(
        "Statistics:",
        first_stats,
    )

    first_pass = (
        len(first_chunks) == 1
        and first_count == 1
        and first_stats[
            "embeddings_generated"
        ] == 1
        and first_stats[
            "chunks_indexed"
        ] == 1
    )

    print(
        "First ingestion:",
        "PASS"
        if first_pass
        else "FAIL",
    )

    # --------------------------------------------------------------
    # TEST 2 - IDENTICAL RECORD
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 2 - IDENTICAL RECORD")

    count_before_duplicate = (
        database.count()
    )

    embeddings_before_duplicate = (
        embedding_manager.total_chunks_embedded
    )

    duplicate_chunks = (
        ingestor.ingest_source_records(
            source_id="server-a",
            records=[
                record_one,
            ],
        )
    )

    count_after_duplicate = (
        database.count()
    )

    embeddings_after_duplicate = (
        embedding_manager.total_chunks_embedded
    )

    duplicate_stats = (
        ingestor.ingestion_statistics()
    )

    print(
        "Chunks indexed:",
        len(duplicate_chunks),
    )

    print(
        "Database count before:",
        count_before_duplicate,
    )

    print(
        "Database count after:",
        count_after_duplicate,
    )

    print(
        "New embeddings generated:",
        (
            embeddings_after_duplicate
            - embeddings_before_duplicate
        ),
    )

    print(
        "Statistics:",
        duplicate_stats,
    )

    duplicate_pass = (
        len(duplicate_chunks) == 0
        and (
            count_after_duplicate
            == count_before_duplicate
        )
        and (
            embeddings_after_duplicate
            == embeddings_before_duplicate
        )
        and duplicate_stats[
            "chunks_skipped"
        ] == 1
        and duplicate_stats[
            "chunks_indexed"
        ] == 0
    )

    print(
        "Duplicate processing:",
        "PASS"
        if duplicate_pass
        else "FAIL",
    )

    # --------------------------------------------------------------
    # TEST 3 - NEW RECORD
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 3 - NEW RECORD")

    count_before_new = (
        database.count()
    )

    embeddings_before_new = (
        embedding_manager.total_chunks_embedded
    )

    new_chunks = (
        ingestor.ingest_source_records(
            source_id="server-b",
            records=[
                record_two,
            ],
        )
    )

    count_after_new = (
        database.count()
    )

    embeddings_after_new = (
        embedding_manager.total_chunks_embedded
    )

    new_stats = (
        ingestor.ingestion_statistics()
    )

    print(
        "Chunks indexed:",
        len(new_chunks),
    )

    print(
        "Database count before:",
        count_before_new,
    )

    print(
        "Database count after:",
        count_after_new,
    )

    print(
        "New embeddings generated:",
        (
            embeddings_after_new
            - embeddings_before_new
        ),
    )

    print(
        "Statistics:",
        new_stats,
    )

    new_pass = (
        len(new_chunks) == 1
        and count_after_new
        == count_before_new + 1
        and embeddings_after_new
        == embeddings_before_new + 1
        and new_stats[
            "chunks_indexed"
        ] == 1
    )

    print(
        "New record processing:",
        "PASS"
        if new_pass
        else "FAIL",
    )

    # --------------------------------------------------------------
    # TEST 4 - MIXED BATCH
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 4 - MIXED BATCH")

    count_before_batch = (
        database.count()
    )

    embeddings_before_batch = (
        embedding_manager.total_chunks_embedded
    )

    batch_chunks = (
        ingestor.ingest_source_records(
            source_id="server-b",
            records=[
                record_one,
                record_two,
                record_three,
            ],
        )
    )

    count_after_batch = (
        database.count()
    )

    embeddings_after_batch = (
        embedding_manager.total_chunks_embedded
    )

    batch_stats = (
        ingestor.ingestion_statistics()
    )

    print(
        "Chunks indexed:",
        len(batch_chunks),
    )

    print(
        "Database count before:",
        count_before_batch,
    )

    print(
        "Database count after:",
        count_after_batch,
    )

    print(
        "New embeddings generated:",
        (
            embeddings_after_batch
            - embeddings_before_batch
        ),
    )

    print(
        "Statistics:",
        batch_stats,
    )

    # record_one = duplicate
    # record_two = duplicate
    # record_three = new
    batch_pass = (
        len(batch_chunks) == 1
        and count_after_batch
        == count_before_batch + 1
        and (
            embeddings_after_batch
            == embeddings_before_batch + 1
        )
        and batch_stats[
            "records_skipped"
        ] == 2
        and batch_stats[
            "chunks_skipped"
        ] == 2
        and batch_stats[
            "chunks_indexed"
        ] == 1
    )

    print(
        "Mixed batch processing:",
        "PASS"
        if batch_pass
        else "FAIL",
    )

    # --------------------------------------------------------------
    # TEST 5 - SOURCE METADATA
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 5 - SOURCE METADATA")

    stored = database.get()

    stored_metadata = (
        stored.get(
            "metadatas",
            [],
        )
    )

    sources = sorted(
        set(
            metadata.get(
                "source"
            )
            for metadata in stored_metadata
            if metadata.get("source")
            is not None
        )
    )

    print(
        "Stored sources:",
        sources,
    )

    source_pass = (
        "server-a" in sources
        and "server-b" in sources
    )

    print(
        "Source metadata:",
        "PASS"
        if source_pass
        else "FAIL",
    )

    # --------------------------------------------------------------
    # TEST 6 - REPEATED BATCH
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 6 - REPEATED BATCH")

    count_before_repeat = (
        database.count()
    )

    embeddings_before_repeat = (
        embedding_manager.total_chunks_embedded
    )

    repeat_chunks = (
        ingestor.ingest_records(
            records=[
                record_one,
                record_two,
                record_three,
            ]
        )
    )

    count_after_repeat = (
        database.count()
    )

    embeddings_after_repeat = (
        embedding_manager.total_chunks_embedded
    )

    repeat_stats = (
        ingestor.ingestion_statistics()
    )

    print(
        "Chunks indexed:",
        len(repeat_chunks),
    )

    print(
        "Database count before:",
        count_before_repeat,
    )

    print(
        "Database count after:",
        count_after_repeat,
    )

    print(
        "New embeddings generated:",
        (
            embeddings_after_repeat
            - embeddings_before_repeat
        ),
    )

    print(
        "Statistics:",
        repeat_stats,
    )

    repeat_pass = (
        len(repeat_chunks) == 0
        and count_after_repeat
        == count_before_repeat
        and embeddings_after_repeat
        == embeddings_before_repeat
        and repeat_stats[
            "chunks_skipped"
        ] == 3
        and repeat_stats[
            "chunks_indexed"
        ] == 0
    )

    print(
        "Repeated batch:",
        "PASS"
        if repeat_pass
        else "FAIL",
    )

    # --------------------------------------------------------------
    # TEST 7 - STATISTICS
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEST 7 - INCREMENTAL STATISTICS")

    statistics = (
        ingestor.ingestion_statistics()
    )

    print(
        "Statistics:",
        statistics,
    )

    statistics_pass = all(
        key in statistics
        for key in [
            "records_received",
            "records_skipped",
            "records_processed",
            "chunks_created",
            "chunks_skipped",
            "chunks_indexed",
            "embeddings_generated",
        ]
    )

    print(
        "Statistics API:",
        "PASS"
        if statistics_pass
        else "FAIL",
    )

    # --------------------------------------------------------------
    # Summary
    # --------------------------------------------------------------

    tests = [
        first_pass,
        duplicate_pass,
        new_pass,
        batch_pass,
        source_pass,
        repeat_pass,
        statistics_pass,
    ]

    passed = sum(
        1
        for result in tests
        if result
    )

    failed = (
        len(tests)
        - passed
    )

    print("\n" + "=" * 70)
    print("INCREMENTAL PROCESSING RESULTS")
    print("=" * 70)

    print(
        f"Tests passed: "
        f"{passed}/{len(tests)}"
    )

    print(
        f"Tests failed: "
        f"{failed}"
    )

    print(
        "Final vector count:",
        database.count(),
    )

    print(
        "Total embedding chunks generated:",
        embedding_manager.total_chunks_embedded,
    )

    if failed != 0:

        raise AssertionError(
            "Incremental processing evaluation failed."
        )

    print("\n" + "=" * 70)
    print(
        "INCREMENTAL PROCESSING EVALUATION PASSED"
    )
    print("=" * 70)

    # --------------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------------

    try:

        ingestor.close()

    except Exception:

        pass

    try:

        if database_path.exists():

            shutil.rmtree(
                database_path
            )

            print(
                "Database cleanup: PASS"
            )

    except PermissionError:

        print(
            "Database cleanup: SKIPPED "
            "(files still locked by ChromaDB)"
        )

    except Exception as exc:

        print(
            "Database cleanup: SKIPPED "
            f"({exc})"
        )

    print("=" * 70)


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    main()