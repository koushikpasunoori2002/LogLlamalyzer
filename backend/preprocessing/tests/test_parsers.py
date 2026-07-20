"""
Run:

python backend/tests/preprocessing/test_parsers.py
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]

sys.path.append(str(PROJECT_ROOT))

from backend.preprocessing.detector.file_detector import FileDetector
from backend.preprocessing.parsers import ParserFactory

detector = FileDetector()

FILES = [

    "dataset/raw/auth/auth.log",

    "dataset/raw/syslog/syslog",

    "dataset/raw/kern/kern.log",

    "dataset/raw/dpkg/dpkg.log",

    "dataset/raw/dmesg/dmesg.1.gz",

]

print("=" * 60)
print("PHASE 4 PARSER FACTORY TEST")
print("=" * 60)

for file in FILES:

    info = detector.detect(file)

    parser = ParserFactory.create_parser(info.log_type)

    print()

    print(f"File      : {file}")

    print(f"Parser    : {type(parser).__name__}")

    print(parser.parse("Hello World"))