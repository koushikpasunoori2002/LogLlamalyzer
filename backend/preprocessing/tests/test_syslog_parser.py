"""
test_syslog_parser.py

Tests the SyslogParser using a real syslog file.

Run:

python backend/preprocessing/tests/test_syslog_parser.py
"""

from pathlib import Path
import sys
from collections import Counter

# ------------------------------------------------------------------
# Project Root
# ------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))

# ------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------

from backend.preprocessing.readers.file_reader import FileReader
from backend.preprocessing.parsers.syslog_parser import SyslogParser

# ------------------------------------------------------------------
# Dataset
# ------------------------------------------------------------------

SYSLOG = (
    PROJECT_ROOT
    / "dataset"
    / "raw"
    / "syslog"
    / "syslog"
)


def main():

    print("=" * 70)
    print("SYSLOG PARSER TEST")
    print("=" * 70)

    # --------------------------------------------------------------
    # Read log file
    # --------------------------------------------------------------

    reader = FileReader()

    text = reader.read(SYSLOG)

    print(f"\nCharacters Read : {len(text)}")

    # --------------------------------------------------------------
    # Parse records
    # --------------------------------------------------------------

    parser = SyslogParser()

    records = parser.parse(text)

    print(f"Records Parsed  : {len(records)}")

    # --------------------------------------------------------------
    # Statistics
    # --------------------------------------------------------------

    event_counter = Counter()
    severity_counter = Counter()
    process_counter = Counter()

    for record in records:

        event_counter[record.event_type] += 1

        severity_counter[record.severity] += 1

        process_counter[record.process] += 1

    print("\n" + "=" * 70)
    print("EVENT SUMMARY")
    print("=" * 70)

    for event, count in sorted(event_counter.items()):

        print(f"{event:<30}{count}")

    print("\n" + "=" * 70)
    print("SEVERITY SUMMARY")
    print("=" * 70)

    for severity, count in sorted(severity_counter.items()):

        print(f"{severity:<30}{count}")

    print("\n" + "=" * 70)
    print("PROCESS SUMMARY")
    print("=" * 70)

    for process, count in sorted(process_counter.items()):

        print(f"{process:<30}{count}")

    # --------------------------------------------------------------
    # Preview Records
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("FIRST FIVE PARSED RECORDS")
    print("=" * 70)

    for i, record in enumerate(records[:5], start=1):

        print(f"\nRecord {i}")

        print(record)

        print("-" * 70)

    print("\nPASS")


if __name__ == "__main__":
    main()