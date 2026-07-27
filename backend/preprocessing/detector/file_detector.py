"""
file_detector.py

Detects metadata for Linux log files.

Responsible for determining:

- log type
- compression
- rotation number
- extension
- appropriate reader
"""

import re
from pathlib import Path

from ..models.file_info import FileInfo


class FileDetector:
    """
    Detects metadata about log files before preprocessing.
    """

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

    # --------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------

    def detect(self, file_path):
        """
        Detect metadata about a log file.

        Parameters
        ----------
        file_path : str | Path

        Returns
        -------
        FileInfo
        """

        path = Path(file_path)

        if not path.exists():

            raise FileNotFoundError(
                f"{path} does not exist."
            )

        filename = path.name

        compressed = self._is_compressed(filename)

        return FileInfo(

            path=path,

            filename=filename,

            log_type=self._detect_log_type(filename),

            compressed=compressed,

            rotation=self._detect_rotation(filename),

            extension=self._get_extension(filename),

            reader=self._select_reader(compressed),

        )

    # --------------------------------------------------------------
    # Internal Helpers
    # --------------------------------------------------------------

    def _detect_log_type(self, filename):
        """
        Detect log category.
        """

        filename = filename.lower()

        for prefix, log_type in self.LOG_TYPES.items():

            if filename.startswith(prefix):

                return log_type

        return "unknown"

    def _is_compressed(self, filename):
        """
        Returns True if the file is gzip compressed.
        """

        return filename.lower().endswith(".gz")

    def _detect_rotation(self, filename):
        """
        Detect log rotation.

        Examples
        --------
        auth
            -> 0

        auth.1
            -> 1

        auth.log
            -> 0

        auth.log.2
            -> 2

        auth.log.2.gz
            -> 2
        """

        match = re.search(r"\.(\d+)(?:\.gz)?$", filename)

        if match:

            return int(match.group(1))

        return 0

    def _get_extension(self, filename):
        """
        Return the effective extension.
        """

        if filename.lower().endswith(".gz"):

            return ".gz"

        return Path(filename).suffix

    def _select_reader(self, compressed):
        """
        Select which reader should be used.
        """

        if compressed:

            return "gzip"

        return "file"

    # --------------------------------------------------------------
    # Information
    # --------------------------------------------------------------

    def info(self):
        """
        Returns detector metadata.
        """

        return {

            "component": "FileDetector",

            "version": "1.0",

            "supports": [

                "auth",
                "syslog",
                "kern",
                "dpkg",
                "dmesg",
                "apache",
                "nginx",
                "docker",
                "apport",

            ],

            "compression": [

                "plain",
                "gzip",

            ],

        }