"""
synchronized_rag_runner.py

Coordinates synchronization and RAG processing.

Pipeline:

Configured Sources
        ↓
Rsync Synchronization
        ↓
Synchronized Files
        ↓
Synchronized RAG Pipeline
        ↓
LogRecord objects
        ↓
Chunks
        ↓
Embeddings
        ↓
ChromaDB
"""

from backend.synchronization.runner.synchronization_runner import (
    SynchronizationRunner,
)

from backend.synchronization.pipeline.synchronized_rag_pipeline import (
    SynchronizedRAGPipeline,
)


class SynchronizedRAGRunner:
    """
    Coordinates one synchronization cycle followed by
    synchronized RAG processing.

    This class does not implement synchronization,
    preprocessing, chunking, embedding, or database
    storage itself. It delegates those responsibilities
    to the existing components.
    """

    def __init__(
        self,
        synchronization_runner: SynchronizationRunner,
        rag_pipeline: SynchronizedRAGPipeline,
    ):
        """
        Initialize the combined synchronization/RAG runner.

        Parameters
        ----------
        synchronization_runner : SynchronizationRunner
            Responsible for synchronizing configured sources.

        rag_pipeline : SynchronizedRAGPipeline
            Responsible for processing synchronized files
            and ingesting them into the RAG database.
        """

        self.synchronization_runner = (
            synchronization_runner
        )

        self.rag_pipeline = rag_pipeline

    def run_once(self):
        """
        Perform one complete synchronization and RAG cycle.

        Returns
        -------
        dict
            Mapping of source IDs to created chunks.
        """

        self.synchronization_runner.sync_once()

        return self.rag_pipeline.process_all()

    def count(self):
        """
        Return the number of vectors stored in the RAG database.
        """

        return self.rag_pipeline.count()

    def info(self):
        """
        Return combined runner information.
        """

        return {
            "component": "SynchronizedRAGRunner",
            "synchronization": (
                self.synchronization_runner.info()
            ),
            "rag_pipeline": (
                self.rag_pipeline.info()
            ),
            "vector_count": self.count(),
        }

    def close(self):
        """
        Close the RAG pipeline.
        """

        self.rag_pipeline.close()

    def __repr__(self):
        return (
            "SynchronizedRAGRunner("
            f"vectors={self.count()})"
        )