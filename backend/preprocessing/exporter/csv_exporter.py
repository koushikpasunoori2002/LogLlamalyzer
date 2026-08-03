"""
csv_exporter.py

Exports log records to CSV format.
"""

import csv

from .base_exporter import BaseExporter


class CSVExporter(BaseExporter):
    """
    Export records to CSV format.
    """

    def __init__(self, output_path):

        super().__init__(output_path)

    def _convert_record(self, record):
        """
        Convert a record into a dictionary.
        """

        if isinstance(record, dict):
            return record

        if hasattr(record, "__dict__"):
            return vars(record)

        return {"value": str(record)}

    def export(self, records):
        """
        Export records to a CSV file.
        """

        if not records:

            with open(
                self.output_path,
                "w",
                newline="",
                encoding="utf-8",
            ):
                pass

            return str(self.output_path)

        data = [
            self._convert_record(record)
            for record in records
        ]

        fieldnames = sorted(data[0].keys())

        with open(
            self.output_path,
            "w",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
            )

            writer.writeheader()

            for row in data:
                writer.writerow(row)

        return str(self.output_path)

    def read(self):
        """
        Read the exported CSV file.
        """

        if not self.exists():
            return []

        rows = []

        with open(
            self.output_path,
            "r",
            newline="",
            encoding="utf-8",
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:
                rows.append(row)

        return rows

    def clear(self):
        """
        Remove all records.
        """

        with open(
            self.output_path,
            "w",
            newline="",
            encoding="utf-8",
        ):
            pass

    def count(self):
        """
        Return the number of records.
        """

        return len(self.read())

    def __repr__(self):

        return (
            f"CSVExporter("
            f"path='{self.output_path}')"
        )