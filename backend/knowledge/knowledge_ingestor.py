"""
knowledge_ingestor.py

Converts security knowledge documents into chunks,
embeddings, and vector database records.
"""

from backend.rag.chunking import ChunkManager
from backend.llm.embeddings import EmbeddingManager
from backend.database.chroma import ChromaDatabase


class KnowledgeIngestor:
    """
    Ingests KnowledgeDocument objects into ChromaDB.
    """

    def __init__(
        self,
        database=None,
        embedding_manager=None,
        chunk_size=500,
        overlap=50,
    ):
        """
        Initialize the knowledge ingestor.
        """

        self.database = (
            database
            if database is not None
            else ChromaDatabase(
                collection_name="security_knowledge"
            )
        )

        self.embedding_manager = (
            embedding_manager
            if embedding_manager is not None
            else EmbeddingManager()
        )

        self.chunk_size = chunk_size
        self.overlap = overlap

    # ----------------------------------------------------------
    # Ingest one document
    # ----------------------------------------------------------

    def ingest_document(self, document):
        """
        Ingest a single KnowledgeDocument.

        Returns
        -------
        list
            Created chunks.
        """

        chunk_manager = ChunkManager(
            chunk_size=self.chunk_size,
            overlap=self.overlap,
        )

        chunks = chunk_manager.add_text(
            text=document.text,
            source=document.source,
            metadata={
                "document_id": document.document_id,
                "category": document.category,
                **document.metadata,
            },
        )

        if not chunks:
            return []

        # ------------------------------------------------------
        # Generate embeddings
        # ------------------------------------------------------

        embeddings = (
            self.embedding_manager.embed_chunks(
                chunks
            )
        )

        # ------------------------------------------------------
        # Prepare ChromaDB records
        # ------------------------------------------------------

        ids = [
            (
                f"{document.document_id}_"
                f"{chunk.chunk_id}"
            )
            for chunk in chunks
        ]

        documents = [
            chunk.text
            for chunk in chunks
        ]

        metadatas = [
            {
                "document_id": document.document_id,
                "source": document.source,
                "category": document.category,
                "chunk_id": chunk.chunk_id,
                **document.metadata,
            }
            for chunk in chunks
        ]

        # ------------------------------------------------------
        # Store in ChromaDB
        # ------------------------------------------------------

        self.database.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        return chunks

    # ----------------------------------------------------------
    # Ingest multiple documents
    # ----------------------------------------------------------

    def ingest_documents(self, documents):
        """
        Ingest multiple KnowledgeDocument objects.

        Returns
        -------
        list
            All generated chunks.
        """

        all_chunks = []

        for document in documents:

            chunks = self.ingest_document(
                document
            )

            all_chunks.extend(
                chunks
            )

        return all_chunks

    # ----------------------------------------------------------
    # Database information
    # ----------------------------------------------------------

    def count(self):
        """
        Return the number of vectors stored.
        """

        return self.database.count()

    def info(self):
        """
        Return ingestion/database information.
        """

        return {
            "component": "KnowledgeIngestor",
            "chunk_size": self.chunk_size,
            "overlap": self.overlap,
            "database": self.database.info(),
            "embedding_model": (
                self.embedding_manager
                .model_information()
            ),
        }

    def clear(self):
        """
        Clear the knowledge vector collection.
        """

        self.database.clear()

    def close(self):
        """
        Close the database.
        """

        self.database.close()

    def __repr__(self):

        return (
            f"KnowledgeIngestor("
            f"count={self.count()}, "
            f"chunk_size={self.chunk_size})"
        )