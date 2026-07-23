"""
dpkg_parser.py

Parser for Linux package manager logs.

Converts dpkg.log entries into LogRecord objects.
"""

import re

from ..models.log_record import LogRecord


class DpkgParser:
    """
    Parser for Linux dpkg logs.
    """

    # ------------------------------------------------------------------
    # Main log pattern
    # ------------------------------------------------------------------

    BASIC_PATTERN = re.compile(
        r"^(?P<timestamp>\S+\s+\S+)\s+"
        r"(?P<action>\w+)\s+"
        r"(?P<package>\S+)"
        r"(?:\s+(?P<details>.*))?$"
    )

    # ------------------------------------------------------------------
    # Event classification map
    # ------------------------------------------------------------------

    EVENT_MAP = {

        "install": (
            "Package Installed",
            "PACKAGE_INSTALL",
            "LOW"
        ),

        "upgrade": (
            "Package Upgraded",
            "PACKAGE_UPGRADE",
            "MEDIUM"
        ),

        "remove": (
            "Package Removed",
            "PACKAGE_REMOVE",
            "HIGH"
        ),

        "configure": (
            "Package Configured",
            "PACKAGE_CONFIGURE",
            "INFO"
        ),

    }

    # ------------------------------------------------------------------
    # Parse complete log
    # ------------------------------------------------------------------

    def parse(self, text, source_file="dpkg.log"):

        records = []

        for line in text.splitlines():

            line = line.strip()

            if not line:
                continue

            record = self._parse_line(
                line,
                source_file
            )

            if record is not None:
                records.append(record)

        return records

    # ------------------------------------------------------------------
    # Parse one line
    # ------------------------------------------------------------------

    def _parse_line(self, line, source_file):

        match = self.BASIC_PATTERN.match(line)

        if not match:
            return None

        data = match.groupdict()

        event, event_type, severity = self._classify_event(
            data["action"]
        )

        return LogRecord(

            log_type="dpkg",

            source_file=source_file,

            timestamp=data["timestamp"],

            hostname=None,

            process="dpkg",

            pid=None,

            severity=severity,

            event=event,

            event_type=event_type,

            user=None,

            ip=None,

            port=None,

            protocol=None,

            message=f'{data["action"]} {data["package"]} {data.get("details") or ""}'.strip()

        )

    # ------------------------------------------------------------------
    # Event Classification
    # ------------------------------------------------------------------

    def _classify_event(self, action):
        """
        Classify package manager events.
        """

        action = action.lower()

        if action in self.EVENT_MAP:

            return self.EVENT_MAP[action]

        return (
            "Package Event",
            "PACKAGE",
            "INFO"
        )

    # ------------------------------------------------------------------
    # Supported Log Type
    # ------------------------------------------------------------------

    def supports(self):
        """
        Returns the supported log type.
        """

        return "dpkg"

    # ------------------------------------------------------------------
    # Parser Metadata
    # ------------------------------------------------------------------

    def info(self):
        """
        Returns parser metadata.
        """

        return {

            "parser": "DpkgParser",

            "version": "1.0",

            "supported_log": "dpkg",

            "supported_events": [

                "PACKAGE_INSTALL",

                "PACKAGE_UPGRADE",

                "PACKAGE_REMOVE",

                "PACKAGE_CONFIGURE",

                "PACKAGE",

            ]

        }