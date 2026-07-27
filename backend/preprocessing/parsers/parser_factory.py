"""
parser_factory.py

Factory for creating log parser instances.
"""

from .auth_parser import AuthParser
from .syslog_parser import SyslogParser
from .kern_parser import KernParser
from .dpkg_parser import DpkgParser
from .dmesg_parser import DmesgParser


class ParserFactory:
    """Creates the appropriate parser for a detected log type."""

    _PARSERS = {
        "auth": AuthParser,
        "syslog": SyslogParser,
        "kern": KernParser,
        "dpkg": DpkgParser,
        "dmesg": DmesgParser,
    }

    @classmethod
    def create(cls, log_type: str):
        """
        Create a parser for the specified log type.

        Args:
            log_type: Detected log type.

        Returns:
            An instance of the corresponding parser.

        Raises:
            ValueError: If no parser is registered for the given log type.
        """

        parser_class = cls._PARSERS.get(log_type)

        if parser_class is None:
            raise ValueError(f"No parser registered for log type: '{log_type}'.")

        return parser_class()