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

    An optional distance threshold can be used to
    reject results that are considered too distant
    from the query.
    """

    def __init__(
        self,
        database=None,
        embedding_manager=None,
        top_k=5,
        distance_threshold=None,
    ):
        """
        Initialize the retriever.

        Parameters
        ----------
        database : ChromaDatabase, optional
            Vector database instance.

        embedding_manager : EmbeddingManager, optional
            Manager responsible for generating embeddings.

        top_k : int
            Number of results to retrieve.

        distance_threshold : float, optional
            Maximum allowed ChromaDB distance.

            Results with a distance greater than this
            value are removed.

            If None, no distance filtering is applied.
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

        # ----------------------------------------------------------
        # Optional retrieval distance threshold
        # ----------------------------------------------------------

        if distance_threshold is not None:

            if distance_threshold < 0:
                raise ValueError(
                    "distance_threshold must be "
                    "greater than or equal to 0."
                )

        self.distance_threshold = (
            distance_threshold
        )

    def retrieve(
        self,
        query,
        top_k=None,
        source=None,
    ):
        """
        Retrieve documents relevant to a query.

        Parameters
        ----------
        query : str
            User search query.

        top_k : int, optional
            Number of results to retrieve.

        source : str, optional
            Synchronized source identifier used to
            restrict retrieval to a specific source.

        Returns
        -------
        dict
            ChromaDB search results.

        Notes
        -----
        If distance_threshold is configured, results
        with distances greater than the threshold are
        removed after ChromaDB retrieval.
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

        # ----------------------------------------------------------
        # Optional source-aware filtering
        # ----------------------------------------------------------

        where = None

        if source is not None:

            where = {
                "synchronized_source": str(source)
            }

        results = self.database.search(
            query_embedding=query_embedding,
            n_results=number_of_results,
            where=where,
        )

        # ----------------------------------------------------------
        # Optional distance filtering
        # ----------------------------------------------------------

        if self.distance_threshold is None:

            return results

        return self._apply_distance_threshold(
            results
        )

    def _apply_distance_threshold(
        self,
        results,
    ):
        """
        Remove retrieved results whose distance
        exceeds the configured threshold.

        ChromaDB returns query results as lists
        because multiple queries can be executed
        at once. The retriever currently processes
        one query at a time.
        """

        distances = results.get(
            "distances",
            [],
        )

        if not distances:

            return results

        filtered_results = dict(results)

        # ----------------------------------------------------------
        # Process the first query result set
        # ----------------------------------------------------------

        query_distances = distances[0]

        keep_indices = [
            index
            for index, distance in enumerate(
                query_distances
            )
            if distance <= self.distance_threshold
        ]

        # ----------------------------------------------------------
        # Filter result fields that contain
        # one entry per retrieved document.
        # ----------------------------------------------------------

        fields_to_filter = [
            "ids",
            "documents",
            "metadatas",
            "distances",
            "embeddings",
            "uris",
            "data",
        ]

        for field in fields_to_filter:

            values = results.get(field)

            if values is None:
                continue

            # Query-result fields normally contain
            # one list per query.

            if (
                isinstance(values, list)
                and len(values) > 0
                and isinstance(values[0], list)
            ):

                filtered_results[field] = [
                    [
                        values[0][index]
                        for index in keep_indices
                    ]
                ]

        return filtered_results

    def retrieve_documents(
        self,
        query,
        top_k=None,
        source=None,
    ):
        """
        Retrieve only the documents from a query.

        Parameters
        ----------
        query : str
            User search query.

        top_k : int, optional
            Number of results to return.

        source : str, optional
            Synchronized source identifier.

        Returns
        -------
        list
            Relevant document texts.
        """

        results = self.retrieve(
            query=query,
            top_k=top_k,
            source=source,
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
        source=None,
    ):
        """
        Retrieve metadata associated with results.

        Parameters
        ----------
        query : str
            User search query.

        top_k : int, optional
            Number of results to return.

        source : str, optional
            Synchronized source identifier.
        """

        results = self.retrieve(
            query=query,
            top_k=top_k,
            source=source,
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
        source=None,
    ):
        """
        Return documents together with similarity
        distances.

        Parameters
        ----------
        query : str
            User search query.

        top_k : int, optional
            Number of results to return.

        source : str, optional
            Synchronized source identifier.
        """

        results = self.retrieve(
            query=query,
            top_k=top_k,
            source=source,
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
            "distance_threshold": (
                self.distance_threshold
            ),
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
            f"distance_threshold="
            f"{self.distance_threshold}, "
            f"records={self.count()})"
        )