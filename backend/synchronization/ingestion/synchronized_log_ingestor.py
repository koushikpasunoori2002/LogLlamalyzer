"""
synchronized_log_ingestor.py

Ingests processed synchronized LogRecord objects into
the LogLlamalyzer RAG vector database.

Supports incremental processing by assigning deterministic
identifiers to generated chunks and skipping chunks that
have already been indexed.
"""

import hashlib
import json

from backend.rag.chunking import ChunkManager
from backend.llm.embeddings import EmbeddingManager
from backend.database.chroma import ChromaDatabase


class SynchronizedLogIngestor:
    """
    Ingests synchronized log records into the vector database.

    Incremental processing is supported through deterministic
    chunk identifiers.

    Existing chunks are detected before embedding generation,
    allowing already-processed data to be skipped.
    """

    def __init__(
        self,
        database=None,
        embedding_manager=None,
        chunk_manager=None,
        top_level_source="synchronized",
    ):
        """
        Initialize the synchronized log ingestor.
        """

        self.database = (
            database
            if database is not None
            else ChromaDatabase()
        )

        self.embedding_manager = (
            embedding_manager
            if embedding_manager is not None
            else EmbeddingManager()
        )

        self.chunk_manager = (
            chunk_manager
            if chunk_manager is not None
            else ChunkManager()
        )

        self.top_level_source = (
            top_level_source
        )

        self.last_ingest_stats = {
            "records_received": 0,
            "records_skipped": 0,
            "records_processed": 0,
            "chunks_created": 0,
            "chunks_skipped": 0,
            "chunks_indexed": 0,
            "embeddings_generated": 0,
        }

    # ----------------------------------------------------------
    # Source
    # ----------------------------------------------------------

    def _record_source(
        self,
        record,
        source=None,
    ):
        """
        Determine the source associated with a record.
        """

        if source is not None:
            return str(source)

        if hasattr(
            record,
            "source_file",
        ):
            return str(
                record.source_file
            )

        return self.top_level_source

    # ----------------------------------------------------------
    # Metadata
    # ----------------------------------------------------------

    def _record_metadata(
        self,
        record,
        source,
    ):
        """
        Convert LogRecord information into metadata.
        """

        if hasattr(
            record,
            "to_dict",
        ):
            metadata = record.to_dict()

        elif hasattr(
            record,
            "__dict__",
        ):
            metadata = vars(record).copy()

        else:
            metadata = {}

        metadata["synchronized_source"] = (
            str(source)
        )

        metadata["source"] = str(source)

        return metadata

    # ----------------------------------------------------------
    # Record text
    # ----------------------------------------------------------

    def _record_text(
        self,
        record,
    ):
        """
        Extract text used for chunk creation.
        """

        if hasattr(
            record,
            "message",
        ):
            return str(
                record.message
            )

        return str(record)

    # ----------------------------------------------------------
    # Stable metadata
    # ----------------------------------------------------------

    def _stable_metadata(
        self,
        metadata,
    ):
        """
        Produce deterministic metadata representation.

        Source-specific fields are deliberately excluded from
        the identity because source is metadata about a record,
        not the intrinsic identity of the record itself.
        """

        identity_metadata = dict(
            metadata
        )

        identity_metadata.pop(
            "source",
            None,
        )

        identity_metadata.pop(
            "synchronized_source",
            None,
        )

        try:

            return json.dumps(
                identity_metadata,
                sort_keys=True,
                default=str,
            )

        except Exception:

            return str(
                identity_metadata
            )

    # ----------------------------------------------------------
    # Stable identity
    # ----------------------------------------------------------

    def _stable_chunk_id(
        self,
        record,
        metadata,
        text,
        chunk_index,
    ):
        """
        Generate a deterministic identifier.

        Preference order:

        1. intrinsic event_id if available
        2. stable record metadata
        3. record text

        Source labels are intentionally excluded so that
        reprocessing the same underlying record does not
        create duplicate vectors.
        """

        event_id = getattr(
            record,
            "event_id",
            None,
        )

        if event_id is not None:

            identity = (
                f"event_id={event_id}|"
                f"text={text}|"
                f"chunk_index={chunk_index}"
            )

        else:

            identity = (
                f"metadata="
                f"{self._stable_metadata(metadata)}|"
                f"text={text}|"
                f"chunk_index={chunk_index}"
            )

        digest = hashlib.sha256(
            identity.encode(
                "utf-8"
            )
        ).hexdigest()[:24]

        return (
            f"sync_{digest}"
        )

    # ----------------------------------------------------------
    # Existing IDs
    # ----------------------------------------------------------

    def _existing_ids(
        self,
        ids,
    ):
        """
        Return IDs already present in the database.
        """

        if not ids:
            return set()

        try:

            stored = self.database.get(
                ids=list(ids)
            )

        except Exception:

            return set()

        if not stored:

            return set()

        stored_ids = stored.get(
            "ids",
            [],
        )

        return set(
            stored_ids or []
        )

    # ----------------------------------------------------------
    # Reset statistics
    # ----------------------------------------------------------

    def _reset_stats(
        self,
        records_received,
    ):
        """
        Reset ingestion statistics.
        """

        self.last_ingest_stats = {
            "records_received": records_received,
            "records_skipped": 0,
            "records_processed": 0,
            "chunks_created": 0,
            "chunks_skipped": 0,
            "chunks_indexed": 0,
            "embeddings_generated": 0,
        }

    # ----------------------------------------------------------
    # Ingest
    # ----------------------------------------------------------

    def ingest_records(
        self,
        records,
        source=None,
    ):
        """
        Incrementally ingest LogRecord objects.

        Existing chunks are detected before embedding generation.

        Returns only newly indexed chunks.
        """

        records = list(
            records
        )

        self._reset_stats(
            len(records)
        )

        new_chunks = []

        for record in records:

            record_source = (
                self._record_source(
                    record,
                    source=source,
                )
            )

            metadata = (
                self._record_metadata(
                    record,
                    record_source,
                )
            )

            text = (
                self._record_text(
                    record
                )
            )

            chunks = (
                self.chunk_manager.add_text(
                    text=text,
                    source=record_source,
                    metadata=metadata,
                )
            )

            if not chunks:
                continue

            self.last_ingest_stats[
                "chunks_created"
            ] += len(chunks)

            record_new_chunks = []

            for chunk_index, chunk in enumerate(
                chunks
            ):

                stable_id = (
                    self._stable_chunk_id(
                        record=record,
                        metadata=metadata,
                        text=chunk.text,
                        chunk_index=chunk_index,
                    )
                )

                chunk.chunk_id = stable_id

                existing_ids = (
                    self._existing_ids(
                        [stable_id]
                    )
                )

                if stable_id in existing_ids:

                    self.last_ingest_stats[
                        "chunks_skipped"
                    ] += 1

                    continue

                record_new_chunks.append(
                    chunk
                )

            if not record_new_chunks:

                self.last_ingest_stats[
                    "records_skipped"
                ] += 1

                continue

            self.last_ingest_stats[
                "records_processed"
            ] += 1

            new_chunks.extend(
                record_new_chunks
            )

        # ------------------------------------------------------
        # No new records
        # ------------------------------------------------------

        if not new_chunks:

            return []

        # ------------------------------------------------------
        # Embed only new chunks
        # ------------------------------------------------------

        embeddings = (
            self.embedding_manager.embed_chunks(
                new_chunks
            )
        )

        self.last_ingest_stats[
            "embeddings_generated"
        ] = len(new_chunks)

        ids = [
            chunk.chunk_id
            for chunk in new_chunks
        ]

        documents = [
            chunk.text
            for chunk in new_chunks
        ]

        metadatas = [
            chunk.metadata
            for chunk in new_chunks
        ]

        # ------------------------------------------------------
        # Store only new vectors
        # ------------------------------------------------------

        self.database.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        self.last_ingest_stats[
            "chunks_indexed"
        ] = len(new_chunks)

        return new_chunks

    # ----------------------------------------------------------
    # Source ingestion
    # ----------------------------------------------------------

    def ingest_source_records(
        self,
        source_id,
        records,
    ):
        """
        Ingest records belonging to a synchronized source.
        """

        return self.ingest_records(
            records=records,
            source=source_id,
        )

    # ----------------------------------------------------------
    # Statistics
    # ----------------------------------------------------------

    def ingestion_statistics(self):
        """
        Return the statistics from the latest ingestion.
        """

        return dict(
            self.last_ingest_stats
        )

    # ----------------------------------------------------------
    # Count
    # ----------------------------------------------------------

    def count(self):
        """
        Return current vector count.
        """

        return self.database.count()

    # ----------------------------------------------------------
    # Information
    # ----------------------------------------------------------

    def info(self):
        """
        Return ingestion component information.
        """

        return {
            "component": (
                "SynchronizedLogIngestor"
            ),
            "database": self.database.info(),
            "embedding_model": (
                self.embedding_manager
                .model_information()
            ),
            "chunk_manager": repr(
                self.chunk_manager
            ),
            "default_source": (
                self.top_level_source
            ),
            "incremental_processing": True,
            "last_ingest_stats": (
                self.ingestion_statistics()
            ),
        }

    # ----------------------------------------------------------
    # Close
    # ----------------------------------------------------------

    def close(self):
        """
        Close the underlying database.
        """

        self.database.close()

    # ----------------------------------------------------------
    # Representation
    # ----------------------------------------------------------

    def __repr__(self):

        return (
            "SynchronizedLogIngestor("
            f"vectors={self.count()}, "
            f"incremental=True)"
        )
        