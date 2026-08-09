"""
context_builder.py

Combines log retrieval and security knowledge retrieval
into a single RAGContext.
"""

from .context import RAGContext


class ContextBuilder:
    """
    Builds a RAGContext from log and knowledge retrievers.
    """

    def __init__(
        self,
        log_retriever=None,
        knowledge_retriever=None,
        top_k_logs=3,
        top_k_knowledge=3,
    ):
        self.log_retriever = log_retriever
        self.knowledge_retriever = knowledge_retriever

        self.top_k_logs = top_k_logs
        self.top_k_knowledge = top_k_knowledge

    # ----------------------------------------------------------
    # Build Context
    # ----------------------------------------------------------

    def build(self, query):
        """
        Retrieve logs and security knowledge for a query
        and combine them into a RAGContext.
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

        context = RAGContext(
            query=query
        )

        # ------------------------------------------------------
        # Retrieve logs
        # ------------------------------------------------------

        if self.log_retriever is not None:

            log_results = self.log_retriever.retrieve(
                query=query,
                top_k=self.top_k_logs,
            )

            self._add_results(
                context,
                log_results,
                result_type="log",
            )

        # ------------------------------------------------------
        # Retrieve security knowledge
        # ------------------------------------------------------

        if self.knowledge_retriever is not None:

            knowledge_results = (
                self.knowledge_retriever.retrieve(
                    query=query,
                    top_k=self.top_k_knowledge,
                )
            )

            self._add_results(
                context,
                knowledge_results,
                result_type="knowledge",
            )

        # ------------------------------------------------------
        # Metadata
        # ------------------------------------------------------

        context.metadata = {
            "log_count": context.log_count(),
            "knowledge_count": context.knowledge_count(),
            "top_k_logs": self.top_k_logs,
            "top_k_knowledge": self.top_k_knowledge,
        }

        return context

    # ----------------------------------------------------------
    # Result Conversion
    # ----------------------------------------------------------

    def _add_results(
        self,
        context,
        results,
        result_type,
    ):
        """
        Convert ChromaDB results into individual result
        dictionaries and add them to the context.
        """

        if not results:
            return

        ids = results.get(
            "ids",
            [[]],
        )

        documents = results.get(
            "documents",
            [[]],
        )

        metadatas = results.get(
            "metadatas",
            [[]],
        )

        distances = results.get(
            "distances",
            [[]],
        )

        ids = ids[0] if ids else []
        documents = documents[0] if documents else []
        metadatas = metadatas[0] if metadatas else []
        distances = distances[0] if distances else []

        count = len(documents)

        for index in range(count):

            result = {
                "id": (
                    ids[index]
                    if index < len(ids)
                    else None
                ),
                "document": documents[index],
                "metadata": (
                    metadatas[index]
                    if index < len(metadatas)
                    else {}
                ),
                "distance": (
                    distances[index]
                    if index < len(distances)
                    else None
                ),
            }

            if result_type == "log":

                context.add_log_result(
                    result
                )

            elif result_type == "knowledge":

                context.add_knowledge_result(
                    result
                )

    # ----------------------------------------------------------
    # Information
    # ----------------------------------------------------------

    def info(self):
        """
        Return builder configuration.
        """

        return {
            "component": "ContextBuilder",
            "top_k_logs": self.top_k_logs,
            "top_k_knowledge": self.top_k_knowledge,
            "log_retriever": (
                self.log_retriever is not None
            ),
            "knowledge_retriever": (
                self.knowledge_retriever is not None
            ),
        }

    def __repr__(self):

        return (
            f"ContextBuilder("
            f"top_k_logs={self.top_k_logs}, "
            f"top_k_knowledge="
            f"{self.top_k_knowledge})"
        )
    