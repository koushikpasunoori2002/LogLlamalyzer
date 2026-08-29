"""
rsync_synchronizer.py

Synchronizes log files from a configured remote source
using rsync over SSH.
"""

import subprocess
from pathlib import Path

from ..models.log_source import LogSource


class RsyncSynchronizer:
    """
    Synchronizes logs from a LogSource using rsync.

    The synchronizer does not know how many sources exist.
    Each LogSource is processed independently.
    """

    def __init__(self, destination):
        self.destination = Path(destination)

    def build_command(self, source: LogSource, log_path: Path):
        """
        Build an rsync command for a configured log path.

        The command uses SSH as the transport mechanism.
        """

        destination = (
            self.destination
            / source.source_id
        )

        destination.mkdir(
            parents=True,
            exist_ok=True,
        )

        remote_path = (
            f"{source.hostname}:{log_path.as_posix()}"
        )

        return [
            "rsync",
            "-av",
            "--partial",
            remote_path,
            str(destination),
        ]

    def sync_source(self, source: LogSource):
        """
        Synchronize all configured log paths for one source.

        Returns the results of each rsync operation.
        """

        if not isinstance(source, LogSource):
            raise TypeError(
                "source must be a LogSource instance."
            )

        results = []

        for log_path in source.log_paths:

            command = self.build_command(
                source,
                log_path,
            )

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )

            results.append(result)

        return results
    def sync_all(self, sources):
        """
        Synchronize all configured log sources.
        """

        results = {}

        for source in sources:
            results[source.source_id] = self.sync_source(source)

        return results