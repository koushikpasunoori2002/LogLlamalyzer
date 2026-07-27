"""
dmesg_parser.py

Parser for Linux dmesg boot logs.
"""

import re

from .base_parser import BaseParser
from ..models.log_record import LogRecord


class DmesgParser(BaseParser):

    """
    Parser for Linux dmesg logs.
    """

    # --------------------------------------------------------------
    # Example:
    #
    # [    0.000000] Linux version ...
    # [    0.123456] usb 1-1: new device found
    # --------------------------------------------------------------

    BASIC_PATTERN = re.compile(

        r"^\[\s*(?P<timestamp>[0-9.]+)\]\s+(?P<message>.*)$"

    )

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

        "network": (
            "Network Event",
            "NETWORK",
            "LOW"
        ),

        "error": (
            "Boot Error",
            "BOOT_ERROR",
            "HIGH"
        ),

        "warning": (
            "Boot Warning",
            "BOOT_WARNING",
            "MEDIUM"
        )

    }

    # --------------------------------------------------------------
    # Parse Whole File
    # --------------------------------------------------------------

    def parse(self, text):

        records = []

        for line in text.splitlines():

            line = line.strip()

            if not line:

                continue

            record = self._parse_line(line)

            if record:

                records.append(record)

        return records

    # --------------------------------------------------------------
    # Parse Single Line
    # --------------------------------------------------------------

    def _parse_line(self, line):

        match = self.BASIC_PATTERN.match(line)

        if not match:

            return None

        data = match.groupdict()

        message = data["message"]

        event, event_type, severity = self._classify_event(message)

        return LogRecord(

            log_type="dmesg",

            source_file="dmesg",

            timestamp=data["timestamp"],

            hostname=None,

            process="kernel",

            pid=None,

            severity=severity,

            event=event,

            event_type=event_type,

            user=None,

            ip=None,

            port=None,

            protocol=None,

            message=message

        )
    # --------------------------------------------------------------
    # Event Classification
    # --------------------------------------------------------------

    def _classify_event(self, message):
        """
        Classify dmesg boot events based on message keywords.
        """

        message = message.lower()

        for keyword, classification in self.EVENT_MAP.items():

            if keyword in message:

                return classification

        return (

            "Boot Event",

            "BOOT",

            "INFO"

        )

    # --------------------------------------------------------------
    # Supported Log Type
    # --------------------------------------------------------------

    def supports(self):
        """
        Returns the supported log type.
        """

        return "dmesg"

    # --------------------------------------------------------------
    # Parser Metadata
    # --------------------------------------------------------------

    def info(self):
        """
        Returns parser metadata.
        """

        return {

            "parser": "DmesgParser",

            "version": "1.0",

            "supported_log": "dmesg",

            "supported_events": [

                "BOOT",

                "USB",

                "PCI",

                "CPU",

                "MEMORY",

                "FILESYSTEM",

                "STORAGE",

                "NETWORK",

                "BOOT_ERROR",

                "BOOT_WARNING"

            ]

        }
