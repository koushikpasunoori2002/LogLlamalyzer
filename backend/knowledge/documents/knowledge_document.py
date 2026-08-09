"""
knowledge_document.py

Defines a security knowledge document used by
the LogLlamalyzer knowledge base.
"""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class KnowledgeDocument:
    """
    Represents a single security knowledge document.
    """

    document_id: str
    text: str
    source: str
    category: str
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self):
        """
        Convert the knowledge document to a dictionary.
        """

        return {
            "document_id": self.document_id,
            "text": self.text,
            "source": self.source,
            "category": self.category,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create a KnowledgeDocument from a dictionary.
        """

        return cls(
            document_id=data.get(
                "document_id",
                "",
            ),
            text=data.get(
                "text",
                "",
            ),
            source=data.get(
                "source",
                "",
            ),
            category=data.get(
                "category",
                "",
            ),
            metadata=data.get(
                "metadata",
                {},
            ),
        )

    def __len__(self):
        """
        Return the length of the document text.
        """

        return len(self.text)

    def __str__(self):

        return (
            f"Knowledge Document\n"
            f"ID       : {self.document_id}\n"
            f"Source   : {self.source}\n"
            f"Category : {self.category}\n"
            f"Length   : {len(self.text)} characters\n"
            f"Metadata : {self.metadata}\n"
            f"Text     : {self.text}"
        )

    def __repr__(self):

        return (
            f"KnowledgeDocument("
            f"document_id='{self.document_id}', "
            f"source='{self.source}', "
            f"category='{self.category}', "
            f"length={len(self.text)})"
        )