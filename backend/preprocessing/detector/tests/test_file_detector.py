"""
Run:

python backend/preprocessing/detector/tests/test_file_detector.py
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.append(str(PROJECT_ROOT))

from backend.preprocessing.detector import FileDetector

detector = FileDetector()

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

print("=" * 60)
print("PHASE 2 FILE DETECTOR TESTS")
print("=" * 60)

for file in FILES:

    if not file.exists():

        print(f"\nSKIPPED : {file.name}")

        continue

    info = detector.detect(file)

    print("\nPASS")

    print(info)

print("\nFinished.")