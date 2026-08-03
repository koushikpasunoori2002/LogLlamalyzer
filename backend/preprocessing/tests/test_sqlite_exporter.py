"""
test_sqlite_exporter.py

Tests the SQLite exporter.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.preprocessing.exporter import SQLiteExporter


def main():

    exporter = SQLiteExporter(
        PROJECT_ROOT
        / "dataset"
        / "processed"
        / "logs.db"
    )

    records = [
        {
            "timestamp": "2026-08-03 12:00:00",
            "severity": "HIGH",
            "message": "Failed password attempt",
        },
        {
            "timestamp": "2026-08-03 12:01:00",
            "severity": "MEDIUM",
            "message": "Connection established",
        },
        {
            "timestamp": "2026-08-03 12:02:00",
            "severity": "LOW",
            "message": "Service started",
        },
    ]

    print("=" * 70)
    print("SQLITE EXPORTER TEST")
    print("=" * 70)

    exporter.clear()

    exporter.export(records)

    loaded_records = exporter.read()

    print("\nRecords written:", exporter.count())

    print("\n")

    for record in loaded_records:
        print(record)

    print("\n")

    print("=" * 70)
    print("DATABASE LOCATION")
    print("=" * 70)

    print(exporter.path())

    print("\n")

    print("=" * 70)
    print("DATABASE SIZE")
    print("=" * 70)

    print(exporter.size(), "bytes")

    print("\n")

    print("=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)

    exporter.close()


if __name__ == "__main__":
    main()