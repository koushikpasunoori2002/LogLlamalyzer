"""
test_parsers.py

Tests the ParserFactory using supported log files.
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

from backend.preprocessing.detector.file_detector import FileDetector
from backend.preprocessing.parsers import ParserFactory

# ------------------------------------------------------------------
# Dataset
# ------------------------------------------------------------------

FILES = [
    PROJECT_ROOT / "dataset" / "raw" / "auth" / "auth.log",
    PROJECT_ROOT / "dataset" / "raw" / "syslog" / "syslog",
    PROJECT_ROOT / "dataset" / "raw" / "kern" / "kern.log",
    PROJECT_ROOT / "dataset" / "raw" / "dpkg" / "dpkg.log",
    PROJECT_ROOT / "dataset" / "raw" / "dmesg" / "dmesg.1.gz",
]


# ------------------------------------------------------------------
# Main Test
# ------------------------------------------------------------------

def main():

    detector = FileDetector()

    print("=" * 70)
    print("PARSER FACTORY TEST")
    print("=" * 70)

    for file in FILES:

        if not file.exists():

            print(f"\nSKIPPED : {file.name}")

            continue

        info = detector.detect(file)

        parser = ParserFactory.create(info.log_type)

        print("\n" + "=" * 70)
        print(f"File      : {file.name}")
        print(f"Log Type  : {info.log_type}")
        print(f"Parser    : {type(parser).__name__}")
        print("=" * 70)

        sample_records = parser.parse("Hello World")

        print(f"Sample Parse Result : {sample_records}")

    print("\n" + "=" * 70)
    print("PARSER FACTORY TEST PASSED")
    print("=" * 70)


# ------------------------------------------------------------------

if __name__ == "__main__":

    main()