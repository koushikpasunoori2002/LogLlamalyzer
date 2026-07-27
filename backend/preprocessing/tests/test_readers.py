"""
test_readers.py

Tests all reader modules.
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

from backend.preprocessing.readers import (
    FileReader,
    GzipReader,
    PersistentReader,
)

# ------------------------------------------------------------------
# Dataset
# ------------------------------------------------------------------

DATASET = PROJECT_ROOT / "dataset" / "raw"

AUTH_LOG = DATASET / "auth" / "auth.log"
AUTH_GZ = DATASET / "auth" / "auth.log.1.gz"


# ------------------------------------------------------------------
# Main Test
# ------------------------------------------------------------------

def main():

    print("=" * 70)
    print("READER MODULE TEST")
    print("=" * 70)

    # --------------------------------------------------------------
    # FileReader
    # --------------------------------------------------------------

    print("\n[1] FileReader")

    reader = FileReader()

    try:

        text = reader.read(AUTH_LOG)

        print("PASS")
        print(f"Characters Read : {len(text)}")

        print("\nPreview")
        print("-" * 70)
        print(text[:300])

    except Exception as error:

        print(f"FAIL : {error}")

    # --------------------------------------------------------------
    # GzipReader
    # --------------------------------------------------------------

    print("\n[2] GzipReader")

    if AUTH_GZ.exists():

        gzip_reader = GzipReader()

        try:

            text = gzip_reader.read(AUTH_GZ)

            print("PASS")
            print(f"Characters Read : {len(text)}")

            print("\nPreview")
            print("-" * 70)
            print(text[:300])

        except Exception as error:

            print(f"FAIL : {error}")

    else:

        print("SKIPPED : auth.log.1.gz not found")

    # --------------------------------------------------------------
    # PersistentReader
    # --------------------------------------------------------------

    print("\n[3] PersistentReader")

    persistent_reader = PersistentReader()

    try:

        new_data = persistent_reader.read_increment(str(AUTH_LOG))

        print("PASS")
        print(f"Characters Returned : {len(new_data)}")

    except Exception as error:

        print(f"FAIL : {error}")

    print("\n" + "=" * 70)
    print("READER MODULE TEST PASSED")
    print("=" * 70)


# ------------------------------------------------------------------

if __name__ == "__main__":

    main()