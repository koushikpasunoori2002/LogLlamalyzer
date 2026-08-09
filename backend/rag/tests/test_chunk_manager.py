"""
test_chunk_manager.py

Tests the ChunkManager.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.rag.chunking import ChunkManager


def main():

    manager = ChunkManager(
        chunk_size=80,
        overlap=10,
    )

    manager.add_text(
        text="Failed password " * 50,
        source="auth.log",
        metadata={
            "severity": "HIGH"
        },
    )

    print("=" * 70)
    print("CHUNK MANAGER TEST")
    print("=" * 70)

    print(f"Chunks Stored : {manager.count()}")

    for chunk in manager.get_chunks():

        print("\n" + "-" * 70)

        print(chunk)

    print("\nTEST PASSED")


if __name__ == "__main__":
    main()