"""
synchronized_log_processor.py

Processes synchronized log files through the existing
LogLlamalyzer preprocessing pipeline.
"""

from pathlib import Path

from ..config.synchronization_config import SynchronizationConfig
from ..models.log_source import LogSource
from backend.preprocessing.pipeline import PreprocessingPipeline


class SynchronizedLogProcessor:
    """
    Processes log files that have been synchronized from
    configured log sources.

    The processor is responsible for:

    1. Discovering synchronized files for a source.
    2. Passing those files to the preprocessing pipeline.
    3. Returning the resulting LogRecord objects.

    It does not perform synchronization itself.
    """

    def __init__(
        self,
        config: SynchronizationConfig,
        pipeline=None,
    ):
        self.config = config

        self.pipeline = (
            pipeline
            if pipeline is not None
            else PreprocessingPipeline()
        )

        self.destination = Path(
            config.destination
        )

    def discover_files(self, source: LogSource):
        """
        Discover files synchronized for one source.

        Parameters
        ----------
        source : LogSource

        Returns
        -------
        list[Path]
            Files found under the source's synchronized
            destination directory.
        """

        if not isinstance(source, LogSource):
            raise TypeError(
                "source must be a LogSource instance."
            )

        source_directory = (
            self.destination
            / source.source_id
        )

        if not source_directory.exists():
            return []

        if not source_directory.is_dir():
            return []

        return [
            path
            for path in source_directory.rglob("*")
            if path.is_file()
        ]

    def process_source(self, source: LogSource):
        """
        Process all synchronized files belonging to one source.

        Returns
        -------
        list
            Parsed LogRecord objects from all successfully
            processed files.
        """

        files = self.discover_files(source)

        records = []

        for file_path in files:

            file_records = self.pipeline.process(
                file_path
            )

            records.extend(file_records)

        return records

    def process_all(self):
        """
        Process synchronized files for every configured source.

        Returns
        -------
        dict
            Mapping of source_id to processed LogRecord objects.
        """

        results = {}

        for source in self.config.sources:

            results[source.source_id] = (
                self.process_source(source)
            )

        return results

    def info(self):
        """
        Return processor metadata.
        """

        return {
            "component": "SynchronizedLogProcessor",
            "source_count": len(
                self.config.sources
            ),
            "destination": str(
                self.destination
            ),
        }