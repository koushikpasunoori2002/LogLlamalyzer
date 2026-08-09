"""
knowledge_manager.py

Manages security knowledge documents used by
the LogLlamalyzer RAG system.
"""

from pathlib import Path

from .documents import KnowledgeDocument
from .loaders import TextKnowledgeLoader


class KnowledgeManager:
    """
    Manages a collection of KnowledgeDocument objects.
    """

    def __init__(self):

        self.loader = TextKnowledgeLoader()

        self.documents = []

    # ----------------------------------------------------------
    # Add Documents
    # ----------------------------------------------------------

    def add_document(self, document):
        """
        Add a KnowledgeDocument to the manager.
        """

        if not isinstance(
            document,
            KnowledgeDocument,
        ):

            raise TypeError(
                "document must be a "
                "KnowledgeDocument."
            )

        # Prevent duplicate document IDs
        existing = self.get_document(
            document.document_id
        )

        if existing is not None:

            raise ValueError(
                f"Document already exists: "
                f"{document.document_id}"
            )

        self.documents.append(
            document
        )

        return document

    def load_file(
        self,
        file_path,
        category="general",
    ):
        """
        Load a text knowledge file and add it.
        """

        document = self.loader.load(
            file_path=file_path,
            category=category,
        )

        self.add_document(
            document
        )

        return document

    def load_directory(
        self,
        directory,
        category="general",
    ):
        """
        Load all TXT files from a directory.
        """

        documents = self.loader.load_directory(
            directory=directory,
            category=category,
        )

        added_documents = []

        for document in documents:

            existing = self.get_document(
                document.document_id
            )

            if existing is not None:
                continue

            self.documents.append(
                document
            )

            added_documents.append(
                document
            )

        return added_documents

    # ----------------------------------------------------------
    # Retrieve Documents
    # ----------------------------------------------------------

    def get_document(
        self,
        document_id,
    ):
        """
        Retrieve a document by ID.
        """

        for document in self.documents:

            if (
                document.document_id
                == document_id
            ):

                return document

        return None

    def get_documents(
        self,
        category=None,
    ):
        """
        Return all documents.

        If category is provided, only documents
        from that category are returned.
        """

        if category is None:

            return list(
                self.documents
            )

        return [
            document
            for document in self.documents
            if document.category
            == category
        ]

    # ----------------------------------------------------------
    # Information
    # ----------------------------------------------------------

    def count(self):
        """
        Return the number of stored documents.
        """

        return len(
            self.documents
        )

    def categories(self):
        """
        Return all unique knowledge categories.
        """

        return sorted(
            set(
                document.category
                for document in self.documents
            )
        )

    def sources(self):
        """
        Return all knowledge sources.
        """

        return sorted(
            set(
                document.source
                for document in self.documents
            )
        )

    # ----------------------------------------------------------
    # Management
    # ----------------------------------------------------------

    def remove_document(
        self,
        document_id,
    ):
        """
        Remove a document by ID.
        """

        document = self.get_document(
            document_id
        )

        if document is None:
            return False

        self.documents.remove(
            document
        )

        return True

    def clear(self):
        """
        Remove all documents.
        """

        self.documents.clear()

    # ----------------------------------------------------------
    # Representation
    # ----------------------------------------------------------

    def __len__(self):

        return len(
            self.documents
        )

    def __repr__(self):

        return (
            f"KnowledgeManager("
            f"documents={len(self.documents)})"
        )