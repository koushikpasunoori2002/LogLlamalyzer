"""
test_embedding_model.py

Tests the EmbeddingModel.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.llm.embeddings import EmbeddingModel


def main():

    model = EmbeddingModel()

    text = "Failed password for root from 192.168.1.20"

    print("=" * 70)
    print("EMBEDDING MODEL TEST")
    print("=" * 70)

    embedding = model.encode(text)

    print("\nModel Information")

    print(model.model_info())

    print("\nEmbedding Dimension")

    print(model.dimension())

    print("\nEmbedding Shape")

    print(embedding.shape)

    print("\nFirst 10 Values")

    print(embedding[:10])

    print("\nTEST PASSED")


if __name__ == "__main__":
    main()