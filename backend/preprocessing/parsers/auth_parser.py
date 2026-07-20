"""
auth_parser.py

Parser for Linux authentication logs.

Converts auth.log entries into LogRecord objects.
"""

import re

from ..models.log_record import LogRecord


class AuthParser:
    """
    Parser for Linux authentication logs.
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
    # Field extraction patterns
    # ------------------------------------------------------------------

    USER_PATTERN = re.compile(
        r"for\s+(?:invalid\s+user\s+|user\s+)?(?P<user>[^\s(]+)"
    )

    IP_PATTERN = re.compile(
        r"from\s+(?P<ip>\d{1,3}(?:\.\d{1,3}){3})"
    )

    PORT_PATTERN = re.compile(
        r"port\s+(?P<port>\d+)"
    )

    PROTOCOL_PATTERN = re.compile(
        r"\b(ssh2|ssh)\b"
    )

    # ------------------------------------------------------------------
    # Event classification map
    # ------------------------------------------------------------------

    EVENT_MAP = {

        "Failed password": (
            "AUTH_FAILURE",
            "HIGH"
        ),

        "Accepted password": (
            "AUTH_SUCCESS",
            "LOW"
        ),

        "invalid user": (
            "INVALID_USER",
            "HIGH"
        ),

        "session opened": (
            "SESSION_OPEN",
            "INFO"
        ),

        "session closed": (
            "SESSION_CLOSE",
            "INFO"
        ),

        "password updated successfully": (
            "PASSWORD_CHANGE",
            "MEDIUM"
        ),
    }

    # ------------------------------------------------------------------
    # Public parser
    # ------------------------------------------------------------------

    def parse(self, text, source_file="auth.log"):
        """
        Parse an entire authentication log.

        Args:
            text (str): Raw auth.log contents.
            source_file (str): Source filename.

        Returns:
            list[LogRecord]
        """

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
    # Parse a single log line
    # ------------------------------------------------------------------

    def _parse_line(self, line, source_file):

        match = self.BASIC_PATTERN.match(line)

        if not match:
            return None

        data = match.groupdict()

        event, event_type, severity = self._classify_event(
            data["process"],
            data["message"]
        )

        return LogRecord(

            log_type="auth",

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

            user=self._extract_user(
                data["message"]
            ),

            ip=self._extract_ip(
                data["message"]
            ),

            port=self._extract_port(
                data["message"]
            ),

            protocol=self._extract_protocol(
                data["message"]
            ),

            message=data["message"]

        )

    # ------------------------------------------------------------------
    # Event Classification
    # ------------------------------------------------------------------

    def _classify_event(self, process, message):
        """
        Determine the event, event type and severity.
        """

        # --------------------------------------------------------------
        # Check message first
        # --------------------------------------------------------------

        for text, (event_type, severity) in self.EVENT_MAP.items():

            if text.lower() in message.lower():

                return (
                    text,
                    event_type,
                    severity
                )

        # --------------------------------------------------------------
        # Fallback to process
        # --------------------------------------------------------------

        if process.lower() == "sudo":

            return (
                "sudo command",
                "SUDO_COMMAND",
                "MEDIUM"
            )

        return (
            "UNKNOWN",
            "UNKNOWN",
            "INFO"
        )

    # ------------------------------------------------------------------
    # Username Extraction
    # ------------------------------------------------------------------

    def _extract_user(self, message):
        """
        Extract username from an authentication message.
        """

        match = self.USER_PATTERN.search(message)

        if match:
            return match.group("user")

        return None

    # ------------------------------------------------------------------
    # IP Address Extraction
    # ------------------------------------------------------------------

    def _extract_ip(self, message):
        """
        Extract IPv4 address.
        """

        match = self.IP_PATTERN.search(message)

        if match:
            return match.group("ip")

        return None

    # ------------------------------------------------------------------
    # Port Extraction
    # ------------------------------------------------------------------

    def _extract_port(self, message):
        """
        Extract network port.
        """

        match = self.PORT_PATTERN.search(message)

        if match:
            return int(match.group("port"))

        return None

    # ------------------------------------------------------------------
    # Protocol Extraction
    # ------------------------------------------------------------------

    def _extract_protocol(self, message):
        """
        Extract network protocol.
        """

        match = self.PROTOCOL_PATTERN.search(message)

        if match:
            return match.group(1)

        return None

    # ------------------------------------------------------------------
    # Supported Log Type
    # ------------------------------------------------------------------

    def supports(self):
        """
        Returns the log type handled by this parser.
        """

        return "auth"