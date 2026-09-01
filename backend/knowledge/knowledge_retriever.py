"""
knowledge_retriever.py

Retrieves relevant security knowledge from the
knowledge vector database.
"""

from backend.llm.embeddings import EmbeddingManager


class KnowledgeRetriever:
    """
    Retrieves security knowledge using semantic similarity.
    """

    def __init__(
        self,
        database,
        embedding_manager=None,
        top_k=3,
    ):
        """
        Initialize the knowledge retriever.

        Parameters
        ----------
        database : ChromaDatabase
            Knowledge vector database.

        embedding_manager : EmbeddingManager, optional
            Embedding model used for queries.

        top_k : int
            Number of results to retrieve.
        """

        self.database = database

        self.embedding_manager = (
            embedding_manager
            if embedding_manager is not None
            else EmbeddingManager()
        )

        self.top_k = top_k

    # ----------------------------------------------------------
    # Retrieve
    # ----------------------------------------------------------

    def retrieve(
        self,
        query,
        top_k=None,
    ):
        """
        Retrieve relevant security knowledge.

        Parameters
        ----------
        query : str
            Security question or search query.

        top_k : int, optional
            Number of results.

        Returns
        -------
        dict
            ChromaDB search results.
        """

        if not isinstance(query, str):

            raise TypeError(
                "query must be a string."
            )

        query = query.strip()

        if not query:

            raise ValueError(
                "query cannot be empty."
            )

        if top_k is None:

            top_k = self.top_k

        if top_k <= 0:

            raise ValueError(
                "top_k must be greater than zero."
            )

        query_embedding = (
            self.embedding_manager.embed_text(
                query
            )
        )

        results = self.database.search(
            query_embedding=query_embedding,
            n_results=top_k,
        )

        return results

    # ----------------------------------------------------------
    # Retrieve with scores
    # ----------------------------------------------------------

    def retrieve_with_scores(
        self,
        query,
        top_k=None,
    ):
        """
        Retrieve knowledge together with similarity
        distances.
        """

        return self.retrieve(
            query=query,
            top_k=top_k,
        )

    # ----------------------------------------------------------
    # Filter knowledge by query relevance
    # ----------------------------------------------------------

    def retrieve_relevant(
        self,
        query,
        top_k=None,
    ):
        """
        Retrieve knowledge and keep results that share
        meaningful terms with the query.
        """

        query = str(
            query
        ).strip().lower()

        if not query:
            raise ValueError(
                "query cannot be empty."
            )

        results = self.retrieve(
            query=query,
            top_k=(
                top_k
                if top_k is not None
                else self.top_k
            ),
        )

        documents = results.get(
            "documents",
            [[]],
        )

        if not documents:
            return {
                "ids": [[]],
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
            }

        documents = documents[0]

        metadatas = results.get(
            "metadatas",
            [[]],
        )

        metadatas = (
            metadatas[0]
            if metadatas
            else []
        )

        distances = results.get(
            "distances",
            [[]],
        )

        distances = (
            distances[0]
            if distances
            else []
        )

        # ------------------------------------------------------
        # Security terms
        # ------------------------------------------------------

        stop_words = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "for",
            "from",
            "to",
            "of",
            "and",
            "or",
            "in",
            "on",
            "with",
            "this",
            "that",
            "attack",
            "activity",
            "possible",
            "potential",
        }

        query_terms = {
            term
            for term in query.split()
            if len(term) >= 3
            and term not in stop_words
        }

        selected_indices = []

        for index, document in enumerate(
            documents
        ):

            document_text = str(
                document
            ).lower()

            document_terms = set(
                document_text.split()
            )

            if query_terms.intersection(
                document_terms
            ):
                selected_indices.append(
                    index
                )

        return {
            "ids": [[
                results["ids"][0][index]
                for index in selected_indices
            ]],

            "documents": [[
                documents[index]
                for index in selected_indices
            ]],

            "metadatas": [[
                metadatas[index]
                for index in selected_indices
                if index < len(metadatas)
            ]],

            "distances": [[
                distances[index]
                for index in selected_indices
                if index < len(distances)
            ]],
        }
    # ----------------------------------------------------------
    # Information
    # ----------------------------------------------------------

    def info(self):
        """
        Return retriever information.
        """

        return {
            "component": "KnowledgeRetriever",
            "top_k": self.top_k,
            "database": self.database.info(),
            "embedding_model": (
                self.embedding_manager
                .model_information()
            ),
        }

    def close(self):
        """
        Close the underlying database.
        """

        self.database.close()

    def __repr__(self):

        return (
            f"KnowledgeRetriever("
            f"top_k={self.top_k})"
        )