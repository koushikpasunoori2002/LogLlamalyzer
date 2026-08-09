"""
text_loader.py

Loads security knowledge from plain text files.
"""

from pathlib import Path

from backend.knowledge.documents import KnowledgeDocument


class TextKnowledgeLoader:
    """
    Loads plain-text knowledge files.
    """

    def load(
        self,
        file_path,
        category="general",
    ):
        """
        Load a text file as a KnowledgeDocument.

        Parameters
        ----------
        file_path : str | Path
            Path to the text file.

        category : str
            Knowledge category.

        Returns
        -------
        KnowledgeDocument
        """

        file_path = Path(file_path)

        if not file_path.exists():

            raise FileNotFoundError(
                f"Knowledge file not found: {file_path}"
            )

        if not file_path.is_file():

            raise ValueError(
                f"Path is not a file: {file_path}"
            )

        text = file_path.read_text(
            encoding="utf-8"
        ).strip()

        if not text:

            raise ValueError(
                f"Knowledge file is empty: {file_path}"
            )

        document_id = (
            f"KB_{file_path.stem}"
        )

        return KnowledgeDocument(
            document_id=document_id,
            text=text,
            source=file_path.name,
            category=category,
            metadata={
                "file_type": "txt",
                "file_path": str(file_path),
            },
        )

    def load_directory(
        self,
        directory,
        category="general",
    ):
        """
        Load all TXT files from a directory.

        Returns
        -------
        list[KnowledgeDocument]
        """

        directory = Path(directory)

        if not directory.exists():

            raise FileNotFoundError(
                f"Knowledge directory not found: "
                f"{directory}"
            )

        if not directory.is_dir():

            raise ValueError(
                f"Path is not a directory: "
                f"{directory}"
            )

        documents = []

        for file_path in sorted(
            directory.glob("*.txt")
        ):

            document = self.load(
                file_path=file_path,
                category=category,
            )

            documents.append(document)

        return documents

    def __repr__(self):

        return "TextKnowledgeLoader()"