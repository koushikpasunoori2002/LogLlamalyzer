"""
rag_analyzer.py

Connects Phase 15 RAG context with the local LLM.
"""

from backend.rag.context import RAGContext

from .llm_client import LLMClient
from .prompt_builder import PromptBuilder
from .response import LLMResponse


class RAGAnalyzer:
    """
    Uses retrieved RAG context to generate a
    security analysis using the local LLM.
    """

    def __init__(
        self,
        llm_client=None,
        prompt_builder=None,
    ):

        self.llm_client = (
            llm_client
            if llm_client is not None
            else LLMClient()
        )

        self.prompt_builder = (
            prompt_builder
            if prompt_builder is not None
            else PromptBuilder()
        )

    # ----------------------------------------------------------
    # Analyse RAG Context
    # ----------------------------------------------------------

    def analyze(self, context):
        """
        Generate an LLM security analysis from RAGContext.
        """

        if not isinstance(
            context,
            RAGContext,
        ):
            raise TypeError(
                "context must be a RAGContext."
            )

        prompt = self.prompt_builder.build(
            context
        )

        response = self.llm_client.generate(
            prompt
        )

        if not isinstance(
            response,
            LLMResponse,
        ):
            raise TypeError(
                "LLM client must return an LLMResponse."
            )

        # Preserve the original user query.
        response.query = context.query

        response.metadata.update({
            "rag": True,
            "log_results": len(
                context.log_results
            ),
            "knowledge_results": len(
                context.knowledge_results
            ),
        })

        return response

    # ----------------------------------------------------------
    # Information
    # ----------------------------------------------------------

    def info(self):
        """
        Return analyzer information.
        """

        return {
            "component": "RAGAnalyzer",
            "llm_client": self.llm_client.info(),
            "prompt_builder": self.prompt_builder.info(),
        }

    def __repr__(self):

        return (
            "RAGAnalyzer("
            f"model='{self.llm_client.model}')"
        )
    