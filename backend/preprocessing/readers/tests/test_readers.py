"""
Test all reader modules.

Run:
python backend/preprocessing/tests/test_readers.py
"""

from pathlib import Path
import sys

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))

from backend.preprocessing.readers import (
    FileReader,
    GzipReader,
    PersistentReader,
)

# -----------------------------
# Dataset paths
# -----------------------------

DATASET = PROJECT_ROOT / "dataset" / "raw"

AUTH_LOG = DATASET / "auth" / "auth.log"
AUTH_GZ = DATASET / "auth" / "auth.log.1.gz"

print("=" * 60)
print("PHASE 1 READER TESTS")
print("=" * 60)

# ----------------------------------------------------
# Test 1
# ----------------------------------------------------

print("\n[TEST 1] FileReader")

reader = FileReader()

try:

    text = reader.read(AUTH_LOG)

    print("PASS")

    print(f"Characters read : {len(text)}")

    print("Preview:")

    print(text[:300])

except Exception as e:

    print("FAIL")

    print(e)

# ----------------------------------------------------
# Test 2
# ----------------------------------------------------

print("\n[TEST 2] GzipReader")

if AUTH_GZ.exists():

    gz = GzipReader()

    try:

        text = gz.read(AUTH_GZ)

        print("PASS")

        print(f"Characters read : {len(text)}")

        print("Preview:")

        print(text[:300])

    except Exception as e:

        print("FAIL")

        print(e)

else:

    print("SKIPPED")

    print("auth.log.1.gz not found")

# ----------------------------------------------------
# Test 3
# ----------------------------------------------------

print("\n[TEST 3] PersistentReader")

persistent = PersistentReader()

try:

    new_data = persistent.read_increment(str(AUTH_LOG))

    print("PASS")

    print("Returned")

    print(len(new_data), "characters")

except Exception as e:

    print("FAIL")

    print(e)

print("\nFinished.")