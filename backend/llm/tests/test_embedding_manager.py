"""
test_embedding_manager.py

Tests the EmbeddingManager.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.llm.embeddings import (
    EmbeddingManager,
)
from backend.rag.chunking import Chunk


def main():

    manager = EmbeddingManager()

    chunk = Chunk(
        chunk_id="chunk_001",
        text="Failed password for root from 192.168.1.20",
        source="auth.log",
    )

    print("=" * 70)
    print("EMBEDDING MANAGER TEST")
    print("=" * 70)

    embedding = manager.embed_chunk(chunk)

    print("\nEmbedding Dimension")

    print(manager.embedding_dimension())

    print("\nEmbedding Shape")

    print(embedding.shape)

    similarity = manager.cosine_similarity(
        embedding,
        embedding,
    )

    print("\nSelf Similarity")

    print(similarity)

    print("\nModel Information")

    print(manager.model_information())

    print("\nTEST PASSED")


if __name__ == "__main__":
    main()