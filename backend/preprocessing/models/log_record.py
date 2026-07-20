"""
log_record.py

Defines the standard LogRecord model used throughout
the LogLlamalyzer preprocessing pipeline.
"""

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class LogRecord:
    """
    Represents a single parsed log entry.

    Every parser (auth, syslog, kern, dpkg, dmesg, etc.)
    returns LogRecord objects.
    """

    # ------------------------------------------------------------------
    # Source Information
    # ------------------------------------------------------------------

    log_type: str
    source_file: str

    # ------------------------------------------------------------------
    # Timestamp Information
    # ------------------------------------------------------------------

    timestamp: str

    # ------------------------------------------------------------------
    # Host Information
    # ------------------------------------------------------------------

    hostname: str

    # ------------------------------------------------------------------
    # Process Information
    # ------------------------------------------------------------------

    process: str
    pid: Optional[int] = None

    # ------------------------------------------------------------------
    # Security Information
    # ------------------------------------------------------------------

    severity: str = "INFO"

    # Original event text from the log
    event: str = "UNKNOWN"

    # Standardized event category
    event_type: str = "UNKNOWN"

    # ------------------------------------------------------------------
    # User Information
    # ------------------------------------------------------------------

    user: Optional[str] = None

    # ------------------------------------------------------------------
    # Network Information
    # ------------------------------------------------------------------

    ip: Optional[str] = None
    port: Optional[int] = None
    protocol: Optional[str] = None

    # ------------------------------------------------------------------
    # Original Log Message
    # ------------------------------------------------------------------

    message: str = ""

    # ------------------------------------------------------------------
    # Helper Methods
    # ------------------------------------------------------------------

    def to_dict(self):
        """
        Convert LogRecord into a dictionary.
        """
        return asdict(self)

    def __str__(self):
        return (
            f"\nTimestamp   : {self.timestamp}"
            f"\nLog Type    : {self.log_type}"
            f"\nHostname    : {self.hostname}"
            f"\nProcess     : {self.process}"
            f"\nPID         : {self.pid}"
            f"\nSeverity    : {self.severity}"
            f"\nEvent       : {self.event}"
            f"\nEvent Type  : {self.event_type}"
            f"\nUser        : {self.user}"
            f"\nIP Address  : {self.ip}"
            f"\nPort        : {self.port}"
            f"\nProtocol    : {self.protocol}"
            f"\nSource File : {self.source_file}"
            f"\nMessage     : {self.message}"
        )

    def is_security_event(self):
        """
        Returns True if the log represents
        a security-related event.
        """
        return self.event_type != "UNKNOWN"

    def has_network_information(self):
        """
        Returns True if the log contains
        network-related information.
        """
        return self.ip is not None

    def has_user_information(self):
        """
        Returns True if the log contains
        a username.
        """
        return self.user is not None