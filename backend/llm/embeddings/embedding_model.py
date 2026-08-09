"""
embedding_model.py

Loads and manages the sentence embedding model.
"""

from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    """
    Wrapper around a SentenceTransformer model.
    """

    def __init__(
        self,
        model_name="all-MiniLM-L6-v2",
    ):
        """
        Load the embedding model.
        """

        self.model_name = model_name

        self.model = SentenceTransformer(
            model_name
        )

    def encode(
        self,
        text,
        normalize_embeddings=True,
    ):
        """
        Generate an embedding for a single text.
        """

        return self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=normalize_embeddings,
        )

    def encode_batch(
        self,
        texts,
        normalize_embeddings=True,
    ):
        """
        Generate embeddings for multiple texts.
        """

        return self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=normalize_embeddings,
        )

    def dimension(self):
        """
        Return embedding vector size.
        """

        return self.model.get_embedding_dimension()
    def model_info(self):
        """
        Return model information.
        """

        return {
            "model": self.model_name,
            "dimension": self.dimension(),
        }

    def __repr__(self):

        return (
            f"EmbeddingModel("
            f"model='{self.model_name}')"
        )