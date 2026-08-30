"""
synchronized_rag_pipeline.py

Coordinates synchronized log processing and RAG ingestion.

Pipeline:

Synchronized Files
        ↓
SynchronizedLogProcessor
        ↓
LogRecord objects
        ↓
SynchronizedLogIngestor
        ↓
ChunkManager
        ↓
EmbeddingManager
        ↓
ChromaDB
"""

from backend.synchronization.config.synchronization_config import (
    SynchronizationConfig,
)

from backend.synchronization.processor.synchronized_log_processor import (
    SynchronizedLogProcessor,
)

from backend.synchronization.ingestion.synchronized_log_ingestor import (
    SynchronizedLogIngestor,
)


class SynchronizedRAGPipeline:
    """
    End-to-end RAG pipeline for synchronized logs.

    The pipeline coordinates:

        synchronized files
                ↓
        SynchronizedLogProcessor
                ↓
        LogRecord objects
                ↓
        SynchronizedLogIngestor
                ↓
        ChromaDB
    """

    def __init__(
        self,
        config: SynchronizationConfig,
        processor=None,
        ingestor=None,
    ):
        """
        Initialize the synchronized RAG pipeline.

        Parameters
        ----------
        config : SynchronizationConfig
            Configuration describing synchronized log sources.

        processor : SynchronizedLogProcessor, optional
            Processor used to parse synchronized log files.

        ingestor : SynchronizedLogIngestor, optional
            Ingestor used to store processed records in ChromaDB.
        """

        self.config = config

        self.processor = (
            processor
            if processor is not None
            else SynchronizedLogProcessor(
                config=config
            )
        )

        self.ingestor = (
            ingestor
            if ingestor is not None
            else SynchronizedLogIngestor()
        )

    def process_source(self, source):
        """
        Process and ingest synchronized logs for one source.

        Parameters
        ----------
        source : LogSource

        Returns
        -------
        list
            Created Chunk objects.
        """

        records = self.processor.process_source(
            source
        )

        if not records:
            return []

        return self.ingestor.ingest_source_records(
            source_id=source.source_id,
            records=records,
        )

    def process_all(self):
        """
        Process and ingest synchronized logs for all
        configured sources.

        Returns
        -------
        dict
            Mapping of source_id to created chunks.
        """

        processed_records = (
            self.processor.process_all()
        )

        results = {}

        for source_id, records in (
            processed_records.items()
        ):

            if not records:
                results[source_id] = []
                continue

            results[source_id] = (
                self.ingestor.ingest_source_records(
                    source_id=source_id,
                    records=records,
                )
            )

        return results

    def count(self):
        """
        Return the number of vectors stored.
        """

        return self.ingestor.count()

    def info(self):
        """
        Return pipeline information.
        """

        return {
            "component": "SynchronizedRAGPipeline",
            "processor": self.processor.info(),
            "ingestor": self.ingestor.info(),
            "vector_count": self.count(),
        }

    def close(self):
        """
        Close the underlying ingestion database.
        """

        self.ingestor.close()

    def __repr__(self):

        return (
            "SynchronizedRAGPipeline("
            f"vectors={self.count()})"
        )