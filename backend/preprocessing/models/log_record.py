"""
log_schema.py

Common schema used by every parser in LogLlamalyzer.
"""

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class LogSchema:
    """
    Standard log record for every parsed log entry.
    """

    # Source Information
    log_type: str
    source_file: str

    # Time Information
    timestamp: str

    # Machine Information
    hostname: str

    # Process Information
    process: str
    pid: Optional[int] = None

    # Security Information
    severity: str = "INFO"
    event: str = "UNKNOWN"

    # User Information
    user: Optional[str] = None

    # Network Information
    ip: Optional[str] = None
    port: Optional[int] = None
    protocol: Optional[str] = None

    # Original Message
    message: str = ""

    def to_dict(self):
        """Convert LogSchema to dictionary."""
        return asdict(self)

    def __str__(self):
        return (
            f"\nTimestamp : {self.timestamp}"
            f"\nLog Type  : {self.log_type}"
            f"\nHostname  : {self.hostname}"
            f"\nProcess   : {self.process}"
            f"\nPID       : {self.pid}"
            f"\nSeverity  : {self.severity}"
            f"\nEvent     : {self.event}"
            f"\nUser      : {self.user}"
            f"\nIP        : {self.ip}"
            f"\nPort      : {self.port}"
            f"\nProtocol  : {self.protocol}"
            f"\nSource    : {self.source_file}"
            f"\nMessage   : {self.message}"
        )