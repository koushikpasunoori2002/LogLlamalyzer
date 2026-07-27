"""
test_auth_parser.py

Integration test for the Auth log preprocessing pipeline.

"""

from pathlib import Path
import sys
from collections import Counter

# ------------------------------------------------------------------
# Project Root
# ------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------

from backend.preprocessing.pipeline import PreprocessingPipeline

# ------------------------------------------------------------------
# Dataset
# ------------------------------------------------------------------

AUTH_LOG = PROJECT_ROOT / "dataset" / "raw" / "auth" / "auth.log"


# ------------------------------------------------------------------
# Main Test
# ------------------------------------------------------------------

def main():

    print("=" * 70)
    print("AUTH PREPROCESSING PIPELINE TEST")
    print("=" * 70)

    pipeline = PreprocessingPipeline()

    # --------------------------------------------------------------
    # Process File
    # --------------------------------------------------------------

    info, records = pipeline.process_with_metadata(AUTH_LOG)

    print(f"\nFilename        : {info.filename}")
    print(f"Log Type        : {info.log_type}")
    print(f"Reader          : {info.reader}")
    print(f"Compressed      : {info.compressed}")
    print(f"Rotation        : {info.rotation}")
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

        print(f"{event:<25} {count}")

    print("\n" + "=" * 70)
    print("SEVERITY SUMMARY")
    print("=" * 70)

    for severity, count in sorted(severity_counter.items()):

        print(f"{severity:<25} {count}")

    print("\n" + "=" * 70)
    print("PROCESS SUMMARY")
    print("=" * 70)

    for process, count in sorted(process_counter.items()):

        print(f"{process:<25} {count}")

    # --------------------------------------------------------------
    # Preview Records
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("FIRST FIVE PARSED RECORDS")
    print("=" * 70)

    for index, record in enumerate(records[:5], start=1):

        print(f"\nRecord {index}")

        print(record)

        print("-" * 70)

    print("\n" + "=" * 70)
    print("AUTH PIPELINE TEST PASSED")
    print("=" * 70)


# ------------------------------------------------------------------

if __name__ == "__main__":

    main()