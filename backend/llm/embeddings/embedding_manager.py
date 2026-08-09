"""
embedding_manager.py

Manages embedding generation for text and Chunk objects.
"""

import numpy as np

from .embedding_model import EmbeddingModel


class EmbeddingManager:
    """
    High-level interface for embedding generation.
    """

    def __init__(
        self,
        model_name="all-MiniLM-L6-v2",
    ):

        self.model = EmbeddingModel(model_name)

    def embed_text(self, text):
        """
        Generate an embedding for a single text.
        """

        return self.model.encode(text)

    def embed_texts(self, texts):
        """
        Generate embeddings for multiple texts.
        """

        return self.model.encode_batch(texts)

    def embed_chunk(self, chunk):
        """
        Generate an embedding for a Chunk object.
        """

        return self.model.encode(chunk.text)

    def embed_chunks(self, chunks):
        """
        Generate embeddings for multiple Chunk objects.
        """

        texts = [
            chunk.text
            for chunk in chunks
        ]

        return self.model.encode_batch(texts)

    def cosine_similarity(
        self,
        embedding1,
        embedding2,
    ):
        """
        Compute cosine similarity between two embeddings.
        """

        embedding1 = np.asarray(embedding1)
        embedding2 = np.asarray(embedding2)

        return float(
            np.dot(embedding1, embedding2)
            /
            (
                np.linalg.norm(embedding1)
                *
                np.linalg.norm(embedding2)
            )
        )

    def embedding_dimension(self):
        """
        Return the embedding vector dimension.
        """

        return self.model.dimension()

    def model_information(self):
        """
        Return information about the loaded model.
        """

        return self.model.model_info()

    def __repr__(self):

        return (
            f"EmbeddingManager("
            f"model={self.model.model_name})"
        )