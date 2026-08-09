"""
context_formatter.py

Formats RAG context into structured text suitable
for consumption by an LLM.
"""

from .context import RAGContext


class ContextFormatter:
    """
    Converts RAGContext into readable LLM context.
    """

    def format(self, context):
        """
        Format a RAGContext object as text.
        """

        if not isinstance(context, RAGContext):
            raise TypeError(
                "context must be a RAGContext."
            )

        sections = []

        # ------------------------------------------------------
        # Query
        # ------------------------------------------------------

        sections.append(
            "USER QUERY\n"
            "----------\n"
            f"{context.query}"
        )

        # ------------------------------------------------------
        # Retrieved Logs
        # ------------------------------------------------------

        if context.log_results:

            log_section = [
                "RETRIEVED LOGS",
                "--------------",
            ]

            for index, result in enumerate(
                context.log_results,
                start=1,
            ):

                log_section.append(
                    f"\nLog Result {index}"
                )

                if isinstance(result, dict):

                    for key, value in result.items():

                        log_section.append(
                            f"{key}: {value}"
                        )

                else:

                    log_section.append(
                        str(result)
                    )

            sections.append(
                "\n".join(log_section)
            )

        # ------------------------------------------------------
        # Security Knowledge
        # ------------------------------------------------------

        if context.knowledge_results:

            knowledge_section = [
                "SECURITY KNOWLEDGE",
                "------------------",
            ]

            for index, result in enumerate(
                context.knowledge_results,
                start=1,
            ):

                knowledge_section.append(
                    f"\nKnowledge Result {index}"
                )

                if isinstance(result, dict):

                    for key, value in result.items():

                        knowledge_section.append(
                            f"{key}: {value}"
                        )

                else:

                    knowledge_section.append(
                        str(result)
                    )

            sections.append(
                "\n".join(knowledge_section)
            )

        # ------------------------------------------------------
        # Metadata
        # ------------------------------------------------------

        if context.metadata:

            metadata_section = [
                "CONTEXT METADATA",
                "-----------------",
            ]

            for key, value in context.metadata.items():

                metadata_section.append(
                    f"{key}: {value}"
                )

            sections.append(
                "\n".join(metadata_section)
            )

        # ------------------------------------------------------
        # Final context
        # ------------------------------------------------------

        return "\n\n".join(
            sections
        )

    def format_for_prompt(self, context):
        """
        Format context with instructions for an LLM.
        """

        formatted_context = self.format(
            context
        )

        return (
            "Use the following retrieved information "
            "to analyse the user's security query.\n\n"
            f"{formatted_context}\n\n"
            "Base the analysis on the retrieved evidence."
        )

    def __call__(self, context):
        """
        Allow the formatter to be called directly.
        """

        return self.format(context)