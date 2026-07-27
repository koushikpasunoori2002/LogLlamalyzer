"""
pipeline.py

Preprocessing pipeline for Linux log files.

Pipeline:

    Input File
        │
        ▼
    FileDetector
        │
        ▼
    Select Reader
        │
        ▼
    Read File
        │
        ▼
    ParserFactory
        │
        ▼
    Parse Records
        │
        ▼
    List[LogRecord]
"""

from pathlib import Path

from .detector.file_detector import FileDetector
from .parsers.parser_factory import ParserFactory
from .readers.file_reader import FileReader
from .readers.gzip_reader import GzipReader


class PreprocessingPipeline:
    """
    End-to-end preprocessing pipeline.

    Automatically:

    1. Detects file metadata.
    2. Selects the correct reader.
    3. Reads the file.
    4. Selects the correct parser.
    5. Parses the log records.
    """

    def __init__(self):

        self.detector = FileDetector()

        self.file_reader = FileReader()

        self.gzip_reader = GzipReader()

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------

    def process(self, file_path):
        """
        Process a single log file.

        Parameters
        ----------
        file_path : str | Path

        Returns
        -------
        list[LogRecord]
        """

        file_path = Path(file_path)

        info = self.detector.detect(file_path)

        reader = self._select_reader(info)

        text = reader.read(file_path)

        parser = ParserFactory.create(info.log_type)

        records = parser.parse(text)

        return records

    def process_with_metadata(self, file_path):
        """
        Process a log file and return both metadata and records.

        Returns
        -------
        tuple(FileInfo, list[LogRecord])
        """

        file_path = Path(file_path)

        info = self.detector.detect(file_path)

        reader = self._select_reader(info)

        text = reader.read(file_path)

        parser = ParserFactory.create(info.log_type)

        records = parser.parse(text)

        return info, records

    # ----------------------------------------------------------
    # Internal Helpers
    # ----------------------------------------------------------

    def _select_reader(self, file_info):
        """
        Select the correct reader based on metadata.
        """

        if file_info.reader == "gzip":

            return self.gzip_reader

        return self.file_reader

    # ----------------------------------------------------------
    # Information
    # ----------------------------------------------------------

    def info(self):
        """
        Returns pipeline metadata.
        """

        return {

            "component": "PreprocessingPipeline",

            "version": "1.0",

            "stages": [

                "FileDetector",

                "Reader Selection",

                "Read File",

                "Parser Selection",

                "Parse Log Records",

            ],

            "supported_readers": [

                "FileReader",

                "GzipReader",

            ],

            "supported_parsers": [

                "AuthParser",

                "SyslogParser",

                "KernParser",

                "DpkgParser",

                "DmesgParser",

            ],

        }


if __name__ == "__main__":

    pipeline = PreprocessingPipeline()

    print(pipeline.info())