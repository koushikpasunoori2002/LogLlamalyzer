"""
base_database.py

Defines the base interface for vector databases.
"""


from abc import ABC, abstractmethod


class BaseVectorDatabase(ABC):
    """
    Abstract interface for vector database implementations.
    """

    @abstractmethod
    def add(
        self,
        ids,
        embeddings,
        documents=None,
        metadatas=None,
    ):
        """
        Add vectors and associated data.
        """
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        query_embedding,
        n_results=5,
    ):
        """
        Search for vectors similar to a query embedding.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, ids):
        """
        Delete vectors by ID.
        """
        raise NotImplementedError

    @abstractmethod
    def count(self):
        """
        Return the number of stored vectors.
        """
        raise NotImplementedError

    @abstractmethod
    def clear(self):
        """
        Remove all vectors.
        """
        raise NotImplementedError

    @abstractmethod
    def close(self):
        """
        Close the database connection.
        """
        raise NotImplementedError