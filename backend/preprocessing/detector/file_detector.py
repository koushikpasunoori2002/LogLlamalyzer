"""
file_detector.py

Detects log type, compression and reader.
"""

import re
from pathlib import Path

from .file_info import FileInfo


class FileDetector:

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

        path = Path(file_path)

        filename = path.name

        compressed = filename.endswith(".gz")

        reader = "gzip" if compressed else "file"

        extension = ".gz" if compressed else path.suffix

        # -------------------------
        # Detect log type
        # -------------------------

        log_type = "unknown"

        for key in self.LOG_TYPES:

            if filename.startswith(key):

                log_type = self.LOG_TYPES[key]

                break

        # -------------------------
        # Detect rotation
        # -------------------------

        rotation = 0

        match = re.search(r"\.(\d+)", filename)

        if match:

            rotation = int(match.group(1))

        return FileInfo(
            path=path,
            filename=filename,
            log_type=log_type,
            compressed=compressed,
            rotation=rotation,
            extension=extension,
            reader=reader,
        )