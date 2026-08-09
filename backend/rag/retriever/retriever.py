"""
retriever.py

Retrieves relevant log chunks from the vector database.
"""

from backend.llm.embeddings import EmbeddingManager
from backend.database.chroma import ChromaDatabase


class Retriever:
    """
    Retrieves relevant documents using embeddings
    and ChromaDB similarity search.
    """

    def __init__(
        self,
        database=None,
        embedding_manager=None,
        top_k=5,
    ):
        """
        Initialize the retriever.

        Parameters
        ----------
        database : ChromaDatabase, optional
            Vector database instance.

        embedding_manager : EmbeddingManager, optional
            Embedding generation manager.

        top_k : int
            Number of results to retrieve.
        """

        self.database = (
            database
            if database is not None
            else ChromaDatabase()
        )

        self.embedding_manager = (
            embedding_manager
            if embedding_manager is not None
            else EmbeddingManager()
        )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than 0."
            )

        self.top_k = top_k

    def retrieve(
        self,
        query,
        top_k=None,
    ):
        """
        Retrieve documents relevant to a query.

        Parameters
        ----------
        query : str
            User search query.

        top_k : int, optional
            Number of results to return.

        Returns
        -------
        dict
            ChromaDB search results.
        """

        if not query or not str(query).strip():

            raise ValueError(
                "Query cannot be empty."
            )

        number_of_results = (
            top_k
            if top_k is not None
            else self.top_k
        )

        if number_of_results <= 0:

            raise ValueError(
                "top_k must be greater than 0."
            )

        query_embedding = (
            self.embedding_manager.embed_text(
                str(query)
            )
        )

        return self.database.search(
            query_embedding=query_embedding,
            n_results=number_of_results,
        )

    def retrieve_documents(
        self,
        query,
        top_k=None,
    ):
        """
        Retrieve only the documents from a query.

        Returns
        -------
        list
            Relevant document texts.
        """

        results = self.retrieve(
            query=query,
            top_k=top_k,
        )

        documents = results.get(
            "documents",
            [],
        )

        if not documents:
            return []

        return documents[0]

    def retrieve_metadata(
        self,
        query,
        top_k=None,
    ):
        """
        Retrieve metadata associated with results.
        """

        results = self.retrieve(
            query=query,
            top_k=top_k,
        )

        metadata = results.get(
            "metadatas",
            [],
        )

        if not metadata:
            return []

        return metadata[0]

    def retrieve_with_scores(
        self,
        query,
        top_k=None,
    ):
        """
        Return documents together with similarity distances.
        """

        results = self.retrieve(
            query=query,
            top_k=top_k,
        )

        documents = results.get(
            "documents",
            [],
        )

        distances = results.get(
            "distances",
            [],
        )

        if not documents:
            return []

        documents = documents[0]

        if distances:
            distances = distances[0]
        else:
            distances = []

        output = []

        for index, document in enumerate(
            documents
        ):

            distance = (
                distances[index]
                if index < len(distances)
                else None
            )

            output.append(
                {
                    "document": document,
                    "distance": distance,
                }
            )

        return output

    def count(self):
        """
        Return the number of records
        currently stored in the database.
        """

        return self.database.count()

    def info(self):
        """
        Return retriever information.
        """

        return {
            "component": "Retriever",
            "top_k": self.top_k,
            "database": self.database.info(),
            "embedding_model": (
                self.embedding_manager
                .model_information()
            ),
        }

    def close(self):
        """
        Close the database.
        """

        self.database.close()

    def __repr__(self):

        return (
            f"Retriever("
            f"top_k={self.top_k}, "
            f"records={self.count()})"
        )