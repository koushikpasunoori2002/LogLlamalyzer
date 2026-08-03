"""
base_exporter.py

Base class for all exporters.
"""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseExporter(ABC):
    """
    Base class for all exporters.
    """

    def __init__(self, output_path):
        """
        Initialize the exporter.

        Parameters
        ----------
        output_path : str or Path
            Destination file path.
        """

        self.output_path = Path(output_path)

        self.output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    @abstractmethod
    def export(self, records):
        """
        Export records.

        Parameters
        ----------
        records : list
            List of LogRecord objects.
        """

        raise NotImplementedError

    def exists(self):
        """
        Determine whether the output file exists.
        """

        return self.output_path.exists()

    def size(self):
        """
        Return the file size in bytes.
        """

        if not self.exists():
            return 0

        return self.output_path.stat().st_size

    def path(self):
        """
        Return the export path.
        """

        return str(self.output_path)

    def __repr__(self):

        return (
            f"{self.__class__.__name__}("
            f"path='{self.output_path}')"
        )