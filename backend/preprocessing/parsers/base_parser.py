"""
base_parser.py

Abstract base class for all log parsers.
"""

from abc import ABC, abstractmethod


class BaseParser(ABC):

    @abstractmethod
    def parse(self, text):
        """
        Parse log text into LogRecord objects.
        """
        pass

    @abstractmethod
    def supports(self):
        """
        Return the supported log type.
        """
        pass

    @abstractmethod
    def info(self):
        """
        Return parser metadata.
        """
        pass