"""
parser_factory.py

Creates parser objects.

The factory selects the correct parser
based on the detected log type.
"""

from .auth_parser import AuthParser
from .syslog_parser import SyslogParser
from .kern_parser import KernParser
 

class ParserFactory:

    _PARSERS = {

        "auth": AuthParser,

        "syslog": SyslogParser,
        
        "kern": KernParser,

    }

    @classmethod
    def create_parser(cls, log_type: str):

        parser = cls._PARSERS.get(log_type)

        if parser is None:

            raise ValueError(
                f"No parser registered for '{log_type}'."
            )

        return parser()