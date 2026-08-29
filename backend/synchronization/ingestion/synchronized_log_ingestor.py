"""
synchronized_log_ingestor.py

Ingests processed synchronized LogRecord objects into
the LogLlamalyzer RAG vector database.

Pipeline:

LogRecord
    ↓
ChunkManager
    ↓
EmbeddingManager
    ↓
ChromaDatabase
"""

from backend.rag.chunking import ChunkManager
from backend.llm.embeddings import EmbeddingManager
from backend.database.chroma import ChromaDatabase


class SynchronizedLogIngestor:
    """
    Ingests synchronized log records into the vector database.

    The ingestor coordinates the existing RAG components:

        LogRecord
            ↓
        ChunkManager
            ↓
        EmbeddingManager
            ↓
        ChromaDatabase
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

        Parameters
        ----------
        database : ChromaDatabase, optional
            Vector database used to store embeddings.

        embedding_manager : EmbeddingManager, optional
            Manager responsible for generating embeddings.

        chunk_manager : ChunkManager, optional
            Manager responsible for creating chunks.

        top_level_source : str
            Default source label for synchronized logs.
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

            return str(
                record.source_file
            )

        return self.top_level_source

    def _record_metadata(
        self,
        record,
        source,
    ):
        """
        Convert LogRecord information into chunk metadata.
        """

        if hasattr(record, "to_dict"):

            metadata = record.to_dict()

        elif hasattr(record, "__dict__"):

            metadata = vars(record).copy()

        else:

            metadata = {}

        metadata["synchronized_source"] = (
            str(source)
        )

        return metadata

    def ingest_records(
        self,
        records,
        source=None,
    ):
        """
        Ingest LogRecord objects into ChromaDB.

        Parameters
        ----------
        records : iterable
            Parsed LogRecord objects.

        source : str, optional
            Source identifier for the records.

        Returns
        -------
        list
            Created Chunk objects.
        """

        all_chunks = []

        for record in records:

            record_source = self._record_source(
                record,
                source=source,
            )

            metadata = self._record_metadata(
                record,
                record_source,
            )

            if hasattr(record, "message"):

                text = record.message

            else:

                text = str(record)

            chunks = self.chunk_manager.add_text(
                text=text,
                source=record_source,
                metadata=metadata,
            )

            all_chunks.extend(
                chunks
            )

        if not all_chunks:
            return []

        embeddings = (
            self.embedding_manager.embed_chunks(
                all_chunks
            )
        )

        ids = [
            chunk.chunk_id
            for chunk in all_chunks
        ]

        documents = [
            chunk.text
            for chunk in all_chunks
        ]

        metadatas = [
            chunk.metadata
            for chunk in all_chunks
        ]

        self.database.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        return all_chunks

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

    def count(self):
        """
        Return the number of vectors currently stored.
        """

        return self.database.count()

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
        }

    def close(self):
        """
        Close the underlying database.
        """

        self.database.close()

    def __repr__(self):

        return (
            "SynchronizedLogIngestor("
            f"vectors={self.count()})"
        )