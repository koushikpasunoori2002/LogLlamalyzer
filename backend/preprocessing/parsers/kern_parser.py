"""
kern_parser.py

Parser for Linux kernel logs.

Converts kern.log entries into LogRecord objects.
"""

import re

from ..models.log_record import LogRecord


class KernParser:
    """
    Parser for Linux kernel logs.
    """

    # ------------------------------------------------------------------
    # Main log pattern
    # ------------------------------------------------------------------

    BASIC_PATTERN = re.compile(
        r"^(?P<timestamp>\S+)\s+"
        r"(?P<hostname>\S+)\s+"
        r"(?P<process>[^\[:]+)"
        r"(?:\[(?P<pid>\d+)\])?:\s*"
        r"(?P<message>.*)$"
    )

    # ------------------------------------------------------------------
    # Event classification map
    # ------------------------------------------------------------------

    EVENT_MAP = {

        "usb": (
            "USB Device",
            "USB",
            "LOW"
        ),

        "pci": (
            "PCI Device",
            "PCI",
            "LOW"
        ),

        "cpu": (
            "CPU Event",
            "CPU",
            "INFO"
        ),

        "memory": (
            "Memory Event",
            "MEMORY",
            "MEDIUM"
        ),

        "filesystem": (
            "Filesystem Event",
            "FILESYSTEM",
            "MEDIUM"
        ),

        "ext4": (
            "Filesystem Event",
            "FILESYSTEM",
            "MEDIUM"
        ),

        "ata": (
            "Storage Event",
            "STORAGE",
            "MEDIUM"
        ),

        "nvme": (
            "Storage Event",
            "STORAGE",
            "MEDIUM"
        ),

        "audit": (
            "Audit Event",
            "AUDIT",
            "MEDIUM"
        ),

        "error": (
            "Kernel Error",
            "KERNEL_ERROR",
            "HIGH"
        ),

        "warning": (
            "Kernel Warning",
            "KERNEL_WARNING",
            "MEDIUM"
        ),

    }

    # ------------------------------------------------------------------
    # Parse complete log
    # ------------------------------------------------------------------

    def parse(self, text, source_file="kern.log"):

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
            data["message"]
        )

        return LogRecord(

            log_type="kern",

            source_file=source_file,

            timestamp=data["timestamp"],

            hostname=data["hostname"],

            process=data["process"],

            pid=int(data["pid"])
            if data["pid"]
            else None,

            severity=severity,

            event=event,

            event_type=event_type,

            user=None,

            ip=None,

            port=None,

            protocol=None,

            message=data["message"]

        )

    # ------------------------------------------------------------------
    # Event Classification
    # ------------------------------------------------------------------

    def _classify_event(self, message):
        """
        Classify kernel events using message keywords.
        """

        message_lower = message.lower()

        for keyword, (event, event_type, severity) in self.EVENT_MAP.items():

            if keyword in message_lower:

                return (
                    event,
                    event_type,
                    severity
                )

        return (
            "Kernel Event",
            "KERNEL",
            "INFO"
        )

    # ------------------------------------------------------------------
    # Supported Log Type
    # ------------------------------------------------------------------

    def supports(self):
        """
        Returns the supported log type.
        """

        return "kern"

    # ------------------------------------------------------------------
    # Parser Metadata
    # ------------------------------------------------------------------

    def info(self):
        """
        Returns parser metadata.
        """

        return {

            "parser": "KernParser",

            "version": "1.0",

            "supported_log": "kern",

            "supported_events": [

                "USB",

                "PCI",

                "CPU",

                "MEMORY",

                "FILESYSTEM",

                "STORAGE",

                "AUDIT",

                "KERNEL_ERROR",

                "KERNEL_WARNING",

                "KERNEL",

            ]

        }