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

    Large insertions are written in batches so they remain
    within ChromaDB's supported batch size.
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

        self.top_level_source = top_level_source

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

        if hasattr(record, "source_file"):
            return str(record.source_file)

        return self.top_level_source

    # ----------------------------------------------------------
    # Metadata
    # ----------------------------------------------------------

    def _normalise_metadata(
        self,
        metadata,
    ):
        """
        Convert metadata values into ChromaDB-compatible
        scalar values.

        Supported values are preserved:

            str
            int
            float
            bool

        None values are omitted.

        Any other value is converted to a string.
        """

        normalised = {}

        for key, value in metadata.items():

            if value is None:
                continue

            if isinstance(
                value,
                (str, int, float, bool),
            ):
                normalised[str(key)] = value
                continue

            normalised[str(key)] = str(value)

        return normalised

    def _record_metadata(
        self,
        record,
        source,
    ):
        """
        Convert LogRecord information into metadata.
        """

        if hasattr(record, "to_dict"):

            metadata = record.to_dict()

        elif hasattr(record, "__dict__"):

            metadata = vars(record).copy()

        else:

            metadata = {}

        metadata["synchronized_source"] = str(source)
        metadata["source"] = str(source)

        return self._normalise_metadata(
            metadata
        )

    # ----------------------------------------------------------
    # Record text
    # ----------------------------------------------------------

    def _record_text(
        self,
        record,
    ):
        """
        Build a structured searchable representation of a log record.

        The representation includes important security fields so that
        semantic retrieval can match queries against event type,
        severity, process, user, network information, and the
        original log message.
        """

        fields = []

        field_names = [
            ("Log type", "log_type"),
            ("Timestamp", "timestamp"),
            ("Hostname", "hostname"),
            ("Process", "process"),
            ("Severity", "severity"),
            ("Event", "event"),
            ("Event type", "event_type"),
            ("User", "user"),
            ("IP address", "ip"),
            ("Port", "port"),
            ("Protocol", "protocol"),
            ("Message", "message"),
        ]

        for label, attribute in field_names:

            if not hasattr(record, attribute):
                continue

            value = getattr(
                record,
                attribute,
            )

            if value is None:
                continue

            value = str(value).strip()

            if not value:
                continue

            fields.append(
                f"{label}: {value}"
            )

        if fields:
            return "\n".join(fields)

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
            identity.encode("utf-8")
        ).hexdigest()[:24]

        return f"sync_{digest}"

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
    # Batched storage
    # ----------------------------------------------------------

    def _store_chunks(
        self,
        chunks,
        embeddings,
        batch_size=5000,
    ):
        """
        Store chunks in batches.

        Parameters
        ----------
        chunks : list
            Chunks to store.

        embeddings : list
            Corresponding embeddings.

        batch_size : int
            Maximum number of records written per
            ChromaDB add() operation.

        Returns
        -------
        int
            Number of chunks successfully stored.
        """

        if not chunks:
            return 0

        if len(chunks) != len(embeddings):
            raise ValueError(
                "The number of chunks and embeddings "
                "must be identical."
            )

        if batch_size <= 0:
            raise ValueError(
                "batch_size must be greater than zero."
            )

        total_indexed = 0

        for start in range(
            0,
            len(chunks),
            batch_size,
        ):

            end = min(
                start + batch_size,
                len(chunks),
            )

            batch_chunks = chunks[start:end]
            batch_embeddings = embeddings[start:end]

            ids = [
                chunk.chunk_id
                for chunk in batch_chunks
            ]

            documents = [
                chunk.text
                for chunk in batch_chunks
            ]

            metadatas = [
                self._normalise_metadata(
                    chunk.metadata
                )
                for chunk in batch_chunks
            ]

            self.database.add(
                ids=ids,
                embeddings=batch_embeddings,
                documents=documents,
                metadatas=metadatas,
            )

            total_indexed += len(
                batch_chunks
            )

        return total_indexed

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

        Existing chunks are detected before embedding
        generation.

        Duplicate IDs within the current batch are also
        prevented.

        Returns only newly indexed chunks.
        """

        records = list(records)

        self._reset_stats(
            len(records)
        )

        if not records:
            return []

        new_chunks = []

        # IDs already selected for insertion during this
        # ingestion call.
        pending_ids = set()

        for record in records:

            record_source = self._record_source(
                record,
                source=source,
            )

            metadata = self._record_metadata(
                record,
                record_source,
            )

            text = self._record_text(
                record
            )

            chunks = self.chunk_manager.add_text(
                text=text,
                source=record_source,
                metadata=metadata,
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

                # Prevent duplicate IDs inside this
                # current ingestion batch.
                if stable_id in pending_ids:

                    self.last_ingest_stats[
                        "chunks_skipped"
                    ] += 1

                    continue

                existing_ids = self._existing_ids(
                    [stable_id]
                )

                # Prevent inserting an ID already stored
                # in the database.
                if stable_id in existing_ids:

                    self.last_ingest_stats[
                        "chunks_skipped"
                    ] += 1

                    continue

                pending_ids.add(
                    stable_id
                )

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

        # ------------------------------------------------------
        # Store vectors safely in batches
        # ------------------------------------------------------

        indexed_count = self._store_chunks(
            chunks=new_chunks,
            embeddings=embeddings,
            batch_size=5000,
        )

        self.last_ingest_stats[
            "chunks_indexed"
        ] = indexed_count

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
        Return statistics from the latest ingestion.
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
            "batch_size": 5000,
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