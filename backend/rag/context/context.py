"""
context.py

Defines the structured context passed from the RAG
retrieval layer to the LLM layer.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class RAGContext:
    """
    Represents combined context retrieved from logs
    and security knowledge.
    """

    query: str

    log_results: List[Dict[str, Any]] = field(
        default_factory=list
    )

    knowledge_results: List[Dict[str, Any]] = field(
        default_factory=list
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def add_log_result(self, result):
        """
        Add a retrieved log result.
        """

        self.log_results.append(result)

    def add_knowledge_result(self, result):
        """
        Add a retrieved knowledge result.
        """

        self.knowledge_results.append(result)

    def log_count(self):
        """
        Return the number of log results.
        """

        return len(self.log_results)

    def knowledge_count(self):
        """
        Return the number of knowledge results.
        """

        return len(self.knowledge_results)

    def to_dict(self):
        """
        Convert the context to a dictionary.
        """

        return {
            "query": self.query,
            "log_results": self.log_results,
            "knowledge_results": self.knowledge_results,
            "metadata": self.metadata,
        }

    def __str__(self):

        return (
            f"RAGContext\n"
            f"Query              : {self.query}\n"
            f"Log Results        : {self.log_count()}\n"
            f"Knowledge Results  : {self.knowledge_count()}\n"
            f"Metadata           : {self.metadata}"
        )

    def __repr__(self):

        return (
            f"RAGContext("
            f"query='{self.query}', "
            f"logs={self.log_count()}, "
            f"knowledge={self.knowledge_count()})"
        )