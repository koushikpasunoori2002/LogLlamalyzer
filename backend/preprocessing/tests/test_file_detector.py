"""
test_file_detector.py

Tests the FileDetector using sample log files.
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

from backend.preprocessing.detector import FileDetector

# ------------------------------------------------------------------
# Dataset
# ------------------------------------------------------------------

DATASET = PROJECT_ROOT / "dataset" / "raw"

FILES = [
    DATASET / "auth" / "auth.log",
    DATASET / "auth" / "auth.log.1",
    DATASET / "auth" / "auth.log.1.gz",
    DATASET / "syslog" / "syslog",
    DATASET / "kern" / "kern.log",
    DATASET / "dpkg" / "dpkg.log",
    DATASET / "dmesg" / "dmesg.1.gz",
]

# ------------------------------------------------------------------
# Main Test
# ------------------------------------------------------------------

def main():

    detector = FileDetector()

    print("=" * 70)
    print("FILE DETECTOR TEST")
    print("=" * 70)

    for file in FILES:

        if not file.exists():

            print(f"\nSKIPPED : {file}")

            continue

        try:

            info = detector.detect(file)

            print("\n" + "=" * 70)
            print(f"FILE : {file.name}")
            print("=" * 70)

            print(info)

        except Exception as error:

            print(f"\nFAILED : {file.name}")
            print(error)

    print("\n" + "=" * 70)
    print("FILE DETECTOR TEST COMPLETED")
    print("=" * 70)


# ------------------------------------------------------------------

if __name__ == "__main__":

    main()