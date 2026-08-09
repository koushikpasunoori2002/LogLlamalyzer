"""
chunk.py

Defines a Chunk object used in the RAG pipeline.
"""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class Chunk:
    """
    Represents a single text chunk.
    """

    chunk_id: str
    text: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        """
        Convert the chunk to a dictionary.
        """

        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "source": self.source,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create a Chunk from a dictionary.
        """

        return cls(
            chunk_id=data.get("chunk_id", ""),
            text=data.get("text", ""),
            source=data.get("source", ""),
            metadata=data.get("metadata", {}),
        )

    def __len__(self):
        """
        Return the length of the chunk text.
        """

        return len(self.text)

    def __str__(self):
        """
        Return a readable string representation.
        """

        return (
            f"Chunk ID : {self.chunk_id}\n"
            f"Source   : {self.source}\n"
            f"Length   : {len(self.text)} characters\n"
            f"Metadata : {self.metadata}\n"
            f"Text     : {self.text}"
        )

    def __repr__(self):
        return (
            f"Chunk(chunk_id='{self.chunk_id}', "
            f"source='{self.source}', "
            f"length={len(self.text)})"
        )