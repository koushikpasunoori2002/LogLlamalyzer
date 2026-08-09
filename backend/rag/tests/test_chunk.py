"""
test_chunk.py

Tests the Chunk class.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.rag.chunking import Chunk


def main():

    chunk = Chunk(
        chunk_id="chunk_001",
        text="Failed password for root from 192.168.1.20",
        source="auth.log",
        metadata={
            "severity": "HIGH",
            "log_type": "auth",
        },
    )

    print("=" * 70)
    print("CHUNK TEST")
    print("=" * 70)

    print(chunk)

    print("\nDictionary")

    print(chunk.to_dict())

    print("\nLength")

    print(len(chunk))

    print("\nTEST PASSED")


if __name__ == "__main__":
    main()