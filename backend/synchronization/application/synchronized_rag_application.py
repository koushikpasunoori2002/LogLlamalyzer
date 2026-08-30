"""
synchronized_rag_application.py

Application-level orchestration for synchronized log processing
and RAG ingestion.

Pipeline:

Synchronization Configuration
        ↓
SynchronizationRunner
        ↓
SynchronizedRAGRunner
        ↓
SynchronizedRAGPipeline
        ↓
Preprocessing
        ↓
Chunking
        ↓
Embeddings
        ↓
ChromaDB
"""

from pathlib import Path

from backend.synchronization.config.synchronization_config import (
    SynchronizationConfig,
)

from backend.synchronization.rsync.rsync_synchronizer import (
    RsyncSynchronizer,
)

from backend.synchronization.runner.synchronization_runner import (
    SynchronizationRunner,
)

from backend.synchronization.pipeline.synchronized_rag_pipeline import (
    SynchronizedRAGPipeline,
)

from backend.synchronization.pipeline.synchronized_rag_runner import (
    SynchronizedRAGRunner,
)


class SynchronizedRAGApplication:
    """
    Top-level application for synchronized log processing.

    The application is responsible only for constructing and
    coordinating the existing synchronization and RAG components.

    It does not implement synchronization, preprocessing,
    chunking, embedding, or database storage itself.
    """

    def __init__(
        self,
        config,
        synchronization_runner=None,
        rag_pipeline=None,
        rag_runner=None,
    ):
        """
        Initialize the application.

        Parameters
        ----------
        config : SynchronizationConfig
            Configuration describing synchronized log sources.

        synchronization_runner : SynchronizationRunner, optional
            Existing synchronization runner.

        rag_pipeline : SynchronizedRAGPipeline, optional
            Existing synchronized RAG pipeline.

        rag_runner : SynchronizedRAGRunner, optional
            Existing combined synchronization/RAG runner.
        """

        if not isinstance(
            config,
            SynchronizationConfig,
        ):
            raise TypeError(
                "config must be a SynchronizationConfig instance."
            )

        self.config = config

        if rag_runner is not None:

            self.rag_runner = rag_runner

            self.synchronization_runner = (
                synchronization_runner
            )

            self.rag_pipeline = rag_pipeline

            return

        self.synchronization_runner = (
            synchronization_runner
            if synchronization_runner is not None
            else SynchronizationRunner(
                config=config,
                synchronizer=RsyncSynchronizer(
                    destination=config.destination
                ),
            )
        )

        self.rag_pipeline = (
            rag_pipeline
            if rag_pipeline is not None
            else SynchronizedRAGPipeline(
                config=config,
            )
        )

        self.rag_runner = (
            SynchronizedRAGRunner(
                synchronization_runner=(
                    self.synchronization_runner
                ),
                rag_pipeline=self.rag_pipeline,
            )
        )

    @classmethod
    def from_file(cls, config_path):
        """
        Create an application from a JSON configuration file.

        Parameters
        ----------
        config_path : str | Path
            Path to synchronization configuration.

        Returns
        -------
        SynchronizedRAGApplication
            Configured application instance.
        """

        config_path = Path(config_path)

        config = SynchronizationConfig.from_file(
            config_path
        )

        return cls(config=config)

    def run_once(self):
        """
        Perform one complete synchronization and RAG cycle.

        Returns
        -------
        dict
            Mapping of source IDs to created chunks.
        """

        return self.rag_runner.run_once()

    def count(self):
        """
        Return the number of vectors stored in ChromaDB.
        """

        return self.rag_runner.count()

    def info(self):
        """
        Return application information.
        """

        return {
            "component": "SynchronizedRAGApplication",
            "configuration": self.config.info(),
            "runner": self.rag_runner.info(),
            "vector_count": self.count(),
        }

    def close(self):
        """
        Close application resources.
        """

        self.rag_runner.close()

    def __repr__(self):
        return (
            "SynchronizedRAGApplication("
            f"vectors={self.count()})"
        )