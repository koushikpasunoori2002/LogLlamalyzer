"""
chroma_database.py

ChromaDB implementation for storing and searching
log embeddings.
"""

from pathlib import Path

import chromadb

from .base_database import BaseVectorDatabase


class ChromaDatabase(BaseVectorDatabase):
    """
    Vector database implementation using ChromaDB.
    """

    def __init__(
        self,
        persist_directory=None,
        collection_name="log_embeddings",
    ):
        """
        Initialize the ChromaDB client and collection.

        Parameters
        ----------
        persist_directory : str | Path, optional
            Directory where ChromaDB data is stored.

        collection_name : str
            Name of the ChromaDB collection.
        """

        if persist_directory is None:

            persist_directory = (
                Path(__file__).resolve().parents[3]
                / "data"
                / "chroma"
            )

        self.persist_directory = Path(
            persist_directory
        )

        self.persist_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.collection_name = collection_name

        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory)
        )

        self.collection = (
            self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "description": "LogLlamalyzer log embeddings"
                },
            )
        )

    def add(
        self,
        ids,
        embeddings,
        documents=None,
        metadatas=None,
    ):
        """
        Add embeddings to the collection.
        """

        if not ids:
            return

        self.collection.add(
            ids=list(ids),
            embeddings=[
                embedding.tolist()
                if hasattr(embedding, "tolist")
                else list(embedding)
                for embedding in embeddings
            ],
            documents=documents,
            metadatas=metadatas,
        )

    def search(
        self,
        query_embedding,
        n_results=5,
    ):
        """
        Search for vectors similar to a query embedding.
        """

        if hasattr(query_embedding, "tolist"):

            query_embedding = (
                query_embedding.tolist()
            )

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )

        return results

    def delete(self, ids):
        """
        Delete vectors by ID.
        """

        if not ids:
            return

        self.collection.delete(
            ids=list(ids)
        )

    def count(self):
        """
        Return the number of stored vectors.
        """

        return self.collection.count()

    def clear(self):
        """
        Remove all vectors from the collection.
        """

        if self.count() == 0:
            return

        ids = self.collection.get(
            include=[]
        )["ids"]

        if ids:
            self.collection.delete(
                ids=ids
            )

    def get(
        self,
        ids=None,
    ):
        """
        Retrieve stored records.

        Parameters
        ----------
        ids : list, optional
            Specific IDs to retrieve.
        """

        if ids is None:

            return self.collection.get()

        return self.collection.get(
            ids=list(ids)
        )

    def close(self):
        """
        Close the database.

        ChromaDB's PersistentClient manages
        persistence automatically, so there is
        no explicit connection close required.
        """

        self.client = None
        self.collection = None

    def info(self):
        """
        Return database information.
        """

        return {
            "database": "ChromaDB",
            "collection": self.collection_name,
            "persist_directory": str(
                self.persist_directory
            ),
            "count": self.count(),
        }

    def __len__(self):

        return self.count()

    def __repr__(self):

        return (
            f"ChromaDatabase("
            f"collection='{self.collection_name}', "
            f"count={self.count()})"
        )