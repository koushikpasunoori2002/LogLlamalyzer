"""
test_chunker.py

Tests the Chunker.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.rag.chunking import Chunker


def main():

    text = (
        "This is a long log message. "
        * 40
    )

    chunker = Chunker(
        chunk_size=100,
        overlap=20,
    )

    chunks = chunker.chunk_text(
        text=text,
        source="auth.log",
        metadata={
            "severity": "HIGH"
        },
    )

    print("=" * 70)
    print("CHUNKER TEST")
    print("=" * 70)

    print(f"Chunks Created : {len(chunks)}")

    for chunk in chunks:

        print("\n" + "-" * 70)

        print(chunk)

    print("\nTEST PASSED")


if __name__ == "__main__":
    main()