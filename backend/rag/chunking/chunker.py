"""
chunker.py

Splits text into chunks for embedding.
"""

from .chunk import Chunk


class Chunker:
    """
    Splits text into fixed-size chunks with optional overlap.
    """

    def __init__(
        self,
        chunk_size=500,
        overlap=50,
    ):
        """
        Parameters
        ----------
        chunk_size : int
            Maximum number of characters in each chunk.

        overlap : int
            Number of overlapping characters between chunks.
        """

        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0.")

        if overlap < 0:
            raise ValueError("overlap cannot be negative.")

        if overlap >= chunk_size:
            raise ValueError(
                "overlap must be smaller than chunk_size."
            )

        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(
        self,
        text,
        source="unknown",
        metadata=None,
    ):
        """
        Split text into Chunk objects.
        """

        if metadata is None:
            metadata = {}

        text = str(text)

        chunks = []

        start = 0
        chunk_number = 1

        while start < len(text):

            end = start + self.chunk_size

            chunk_text = text[start:end]

            chunk = Chunk(
                chunk_id=f"chunk_{chunk_number}",
                text=chunk_text,
                source=source,
                metadata=metadata.copy(),
            )

            chunks.append(chunk)

            start += self.chunk_size - self.overlap

            chunk_number += 1

        return chunks

    def chunk_record(
        self,
        record,
        source="unknown",
    ):
        """
        Convert a LogRecord into chunks.
        """

        metadata = {}

        if hasattr(record, "__dict__"):

            metadata = vars(record).copy()

            text = metadata.pop(
                "message",
                str(record),
            )

        else:

            text = str(record)

        return self.chunk_text(
            text=text,
            source=source,
            metadata=metadata,
        )

    def __repr__(self):

        return (
            f"Chunker("
            f"chunk_size={self.chunk_size}, "
            f"overlap={self.overlap})"
        )