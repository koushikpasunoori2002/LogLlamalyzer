"""
syslog_parser.py

Parser for Linux system logs.

Converts syslog entries into LogRecord objects.
"""

import re

from ..models.log_record import LogRecord


class SyslogParser:
    """
    Parser for Linux system logs.
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
    # Process classification map
    # ------------------------------------------------------------------

    EVENT_MAP = {

        "systemd": (
            "SYSTEMD",
            "INFO"
        ),

        "rsyslogd": (
            "RSYSLOG",
            "INFO"
        ),

        "snapd": (
            "SNAP",
            "INFO"
        ),

        "PackageKit": (
            "PACKAGE",
            "INFO"
        ),

        "anacron": (
            "ANACRON",
            "INFO"
        ),

        "CRON": (
            "CRON",
            "INFO"
        ),

        "kernel": (
            "KERNEL",
            "INFO"
        ),

        "NetworkManager": (
            "NETWORK",
            "INFO"
        ),

        "dbus-daemon": (
            "DBUS",
            "INFO"
        ),

    }

    # ------------------------------------------------------------------
    # Parse entire syslog
    # ------------------------------------------------------------------

    def parse(self, text, source_file="syslog"):

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

        event_type, severity = self._classify_event(
            data["process"]
        )

        return LogRecord(

            log_type="syslog",

            source_file=source_file,

            timestamp=data["timestamp"],

            hostname=data["hostname"],

            process=data["process"],

            pid=int(data["pid"])
            if data["pid"]
            else None,

            severity=severity,

            event=event_type,

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

    def _classify_event(self, process):
        """
        Classify the event based on the process name.
        """

        if process in self.EVENT_MAP:

            return self.EVENT_MAP[process]

        return (
            "SYSTEM_EVENT",
            "INFO"
        )

    # ------------------------------------------------------------------
    # Supported Log Type
    # ------------------------------------------------------------------

    def supports(self):
        """
        Returns the log type handled by this parser.
        """

        return "syslog"

    # ------------------------------------------------------------------
    # Parser Information
    # ------------------------------------------------------------------

    def info(self):
        """
        Returns parser metadata.
        """

        return {

            "parser": "SyslogParser",

            "version": "1.0",

            "supported_log": "syslog",

            "supported_events": [

                "SYSTEMD",

                "RSYSLOG",

                "SNAP",

                "PACKAGE",

                "ANACRON",

                "CRON",

                "KERNEL",

                "NETWORK",

                "DBUS",

                "SYSTEM_EVENT",

            ]

        }