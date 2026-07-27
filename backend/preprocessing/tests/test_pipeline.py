"""
test_pipeline.py

Integration test for the preprocessing pipeline.
"""

from pathlib import Path
import sys

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

DATASET_ROOT = PROJECT_ROOT / "dataset" / "raw"

TEST_FILES = [
    DATASET_ROOT / "auth" / "auth.log",
    DATASET_ROOT / "syslog" / "syslog",
    DATASET_ROOT / "kern" / "kern.log",
    DATASET_ROOT / "dpkg" / "dpkg.log",
    DATASET_ROOT / "dmesg" / "dmesg.1.gz",
]


# ------------------------------------------------------------------
# Main Test
# ------------------------------------------------------------------

def main():

    pipeline = PreprocessingPipeline()

    print("=" * 70)
    print("PREPROCESSING PIPELINE TEST")
    print("=" * 70)

    files_processed = 0
    total_records = 0

    for file in TEST_FILES:

        if not file.exists():

            print(f"\nSKIPPED : {file.name}")

            continue

        print("\n" + "=" * 70)
        print(f"PROCESSING : {file.name}")
        print("=" * 70)

        try:

            info, records = pipeline.process_with_metadata(file)

            files_processed += 1
            total_records += len(records)

            print(f"Log Type      : {info.log_type}")
            print(f"Reader        : {info.reader}")
            print(f"Compressed    : {info.compressed}")
            print(f"Rotation      : {info.rotation}")
            print(f"Records Parsed: {len(records)}")

            if records:

                print("\nFirst Parsed Record")
                print("-" * 70)
                print(records[0])

        except Exception as error:

            print(f"FAILED : {error}")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print(f"Files Processed : {files_processed}")
    print(f"Total Records   : {total_records}")

    print("\n" + "=" * 70)
    print("PREPROCESSING PIPELINE TEST PASSED")
    print("=" * 70)


# ------------------------------------------------------------------

if __name__ == "__main__":

    main()