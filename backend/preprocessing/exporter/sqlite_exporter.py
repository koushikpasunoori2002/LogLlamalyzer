"""
sqlite_exporter.py

Exports log records to an SQLite database.
"""

import sqlite3

from .base_exporter import BaseExporter


class SQLiteExporter(BaseExporter):
    """
    Export records to SQLite.
    """

    def __init__(self, output_path):

        super().__init__(output_path)

        self.connection = sqlite3.connect(
            self.output_path
        )

        self.cursor = self.connection.cursor()

        self._create_table()

    def _create_table(self):
        """
        Create the records table.
        """

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL
            )
            """
        )

        self.connection.commit()

    def _convert_record(self, record):
        """
        Convert a record to text.
        """

        if isinstance(record, dict):
            return str(record)

        if hasattr(record, "__dict__"):
            return str(vars(record))

        return str(record)

    def export(self, records):
        """
        Export records to the database.
        """

        for record in records:

            value = self._convert_record(record)

            self.cursor.execute(
                """
                INSERT INTO logs (data)
                VALUES (?)
                """,
                (value,),
            )

        self.connection.commit()

        return str(self.output_path)

    def read(self):
        """
        Read all records.
        """

        self.cursor.execute(
            """
            SELECT * FROM logs
            """
        )

        return self.cursor.fetchall()

    def clear(self):
        """
        Remove all records.
        """

        self.cursor.execute(
            """
            DELETE FROM logs
            """
        )

        self.connection.commit()

    def count(self):
        """
        Return the number of records.
        """

        self.cursor.execute(
            """
            SELECT COUNT(*)
            FROM logs
            """
        )

        return self.cursor.fetchone()[0]

    def close(self):
        """
        Close the database connection.
        """

        self.connection.close()

    def __del__(self):

        try:
            self.close()

        except Exception:
            pass

    def __repr__(self):

        return (
            f"SQLiteExporter("
            f"path='{self.output_path}')"
        )