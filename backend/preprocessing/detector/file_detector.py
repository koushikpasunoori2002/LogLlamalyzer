"""
file_detector.py

Detects log file metadata such as:
- log type
- compression
- rotation
- reader type
"""

import re
from pathlib import Path

from ..models.file_info import FileInfo


class FileDetector:
    """Detects metadata for log files."""

    LOG_TYPES = {
        "auth": "auth",
        "syslog": "syslog",
        "kern": "kern",
        "dpkg": "dpkg",
        "dmesg": "dmesg",
        "apache": "apache",
        "nginx": "nginx",
        "docker": "docker",
        "apport": "apport",
    }

    def detect(self, file_path):
        """
        Detect metadata about a log file.

        Args:
            file_path (str | Path): Path to the log file.

        Returns:
            FileInfo: Metadata describing the file.
        """

        path = Path(file_path)

        return FileInfo(
            path=path,
            filename=path.name,
            log_type=self._detect_log_type(path.name),
            compressed=self._is_compressed(path.name),
            rotation=self._detect_rotation(path.name),
            extension=self._get_extension(path.name),
            reader=self._select_reader(path.name),
        )

    def _detect_log_type(self, filename):
        """Determine the log type from the filename."""

        for prefix, log_type in self.LOG_TYPES.items():
            if filename.startswith(prefix):
                return log_type

        return "unknown"

    def _is_compressed(self, filename):
        """Check whether the file is gzip compressed."""

        return filename.endswith(".gz")

    def _detect_rotation(self, filename):
        """
        Detect log rotation number.

        Examples:
            auth.log       -> 0
            auth.log.1     -> 1
            auth.log.2.gz  -> 2
        """

        match = re.search(r"\.(\d+)", filename)

        if match:
            return int(match.group(1))

        return 0

    def _get_extension(self, filename):
        """
        Return the effective extension.

        Examples:
            auth.log       -> .log
            auth.log.1     -> .1
            auth.log.1.gz  -> .gz
            syslog         -> ""
        """

        if filename.endswith(".gz"):
            return ".gz"

        return Path(filename).suffix

    def _select_reader(self, filename):
        """
        Select the appropriate reader.
        """

        if self._is_compressed(filename):
            return "gzip"

        return "file"