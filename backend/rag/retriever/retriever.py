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

    Supports:

    - configurable top_k
    - optional source filtering
    - optional distance-threshold filtering
    - document retrieval
    - metadata retrieval
    - scored retrieval
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
            Default number of results to retrieve.

        distance_threshold : float, optional
            Maximum allowed ChromaDB distance.

            Results with a distance greater than this
            value are removed after retrieval.

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
        # Optional distance threshold
        # ----------------------------------------------------------

        if distance_threshold is not None:

            if distance_threshold < 0:
                raise ValueError(
                    "distance_threshold must be "
                    "greater than or equal to 0."
                )

        self.distance_threshold = distance_threshold

    # ------------------------------------------------------------------
    # Main retrieval
    # ------------------------------------------------------------------

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
            Source identifier used to restrict retrieval
            to a specific synchronized log source.

        Returns
        -------
        dict
            ChromaDB search results.

        Notes
        -----
        Source filtering uses the ``source`` metadata field.

        If distance_threshold is configured, results whose
        distance exceeds the threshold are removed after
        ChromaDB retrieval.
        """

        # ----------------------------------------------------------
        # Validate query
        # ----------------------------------------------------------

        if not query or not str(query).strip():
            raise ValueError(
                "Query cannot be empty."
            )

        # ----------------------------------------------------------
        # Determine number of results
        # ----------------------------------------------------------

        number_of_results = (
            top_k
            if top_k is not None
            else self.top_k
        )

        if number_of_results <= 0:
            raise ValueError(
                "top_k must be greater than 0."
            )

        # ----------------------------------------------------------
        # Generate query embedding
        # ----------------------------------------------------------

        query_embedding = (
            self.embedding_manager.embed_text(
                str(query)
            )
        )

        # ----------------------------------------------------------
        # Optional source-aware filtering
        #
        # The project metadata schema stores the synchronized
        # source identifier under the ``source`` field.
        # ----------------------------------------------------------

        where = None

        if source is not None:

            source_value = str(source).strip()

            if not source_value:
                raise ValueError(
                    "source cannot be empty."
                )

            where = {
                "source": source_value
            }

        # ----------------------------------------------------------
        # Search vector database
        # ----------------------------------------------------------

        results = self.database.search(
            query_embedding=query_embedding,
            n_results=number_of_results,
            where=where,
        )

        # ----------------------------------------------------------
        # Apply optional distance filtering
        # ----------------------------------------------------------

        if self.distance_threshold is None:
            return results

        return self._apply_distance_threshold(
            results
        )

    # ------------------------------------------------------------------
    # Distance threshold
    # ------------------------------------------------------------------

    def _apply_distance_threshold(
        self,
        results,
    ):
        """
        Remove retrieved results whose distance exceeds
        the configured distance threshold.

        ChromaDB returns query results as lists because
        multiple queries can be executed at once.

        The Retriever currently processes one query at
        a time.
        """

        if not results:
            return results

        distances = results.get(
            "distances",
            [],
        )

        if not distances:
            return results

        if not isinstance(distances, list):
            return results

        if len(distances) == 0:
            return results

        # ----------------------------------------------------------
        # First query result set
        # ----------------------------------------------------------

        query_distances = distances[0]

        if not isinstance(query_distances, list):
            return results

        # ----------------------------------------------------------
        # Determine which results remain
        # ----------------------------------------------------------

        keep_indices = [
            index
            for index, distance in enumerate(
                query_distances
            )
            if distance <= self.distance_threshold
        ]

        # ----------------------------------------------------------
        # Copy original result structure
        # ----------------------------------------------------------

        filtered_results = dict(results)

        # ----------------------------------------------------------
        # Filter fields containing one entry per
        # retrieved document.
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

            if not isinstance(values, list):
                continue

            if len(values) == 0:
                continue

            # ------------------------------------------------------
            # Standard ChromaDB structure:
            #
            # [
            #     [result1, result2, result3]
            # ]
            # ------------------------------------------------------

            if isinstance(values[0], list):

                filtered_results[field] = [
                    [
                        values[0][index]
                        for index in keep_indices
                    ]
                ]

        return filtered_results

    # ------------------------------------------------------------------
    # Document retrieval
    # ------------------------------------------------------------------

    def retrieve_documents(
        self,
        query,
        top_k=None,
        source=None,
    ):
        """
        Retrieve only document text.

        Parameters
        ----------
        query : str
            User search query.

        top_k : int, optional
            Number of results.

        source : str, optional
            Source identifier used to restrict retrieval.

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

        if not isinstance(documents, list):
            return []

        if not isinstance(documents[0], list):
            return []

        return documents[0]

    # ------------------------------------------------------------------
    # Metadata retrieval
    # ------------------------------------------------------------------

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
            Number of results.

        source : str, optional
            Source identifier used to restrict retrieval.

        Returns
        -------
        list
            Metadata dictionaries.
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

        if not isinstance(metadata, list):
            return []

        if not isinstance(metadata[0], list):
            return []

        return metadata[0]

    # ------------------------------------------------------------------
    # Retrieval with scores
    # ------------------------------------------------------------------

    def retrieve_with_scores(
        self,
        query,
        top_k=None,
        source=None,
    ):
        """
        Return retrieved documents together with their
        ChromaDB distances.

        Parameters
        ----------
        query : str
            User search query.

        top_k : int, optional
            Number of results.

        source : str, optional
            Source identifier used to restrict retrieval.

        Returns
        -------
        list of dict
            Each item contains:

            {
                "document": "...",
                "distance": float
            }
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

        if not isinstance(documents, list):
            return []

        if not isinstance(documents[0], list):
            return []

        documents = documents[0]

        if (
            isinstance(distances, list)
            and len(distances) > 0
            and isinstance(distances[0], list)
        ):
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

    # ------------------------------------------------------------------
    # Database count
    # ------------------------------------------------------------------

    def count(self):
        """
        Return the number of records currently stored
        in the vector database.
        """

        return self.database.count()

    # ------------------------------------------------------------------
    # Retriever information
    # ------------------------------------------------------------------

    def info(self):
        """
        Return information about the Retriever.
        """

        return {
            "component": "Retriever",
            "top_k": self.top_k,
            "distance_threshold": (
                self.distance_threshold
            ),
            "database": self.database.info(),
            "embedding_model": (
                self.embedding_manager.model_information()
            ),
        }

    # ------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------

    def close(self):
        """
        Close the underlying database.
        """

        self.database.close()

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self):

        return (
            f"Retriever("
            f"top_k={self.top_k}, "
            f"distance_threshold="
            f"{self.distance_threshold}, "
            f"records={self.count()})"
        )