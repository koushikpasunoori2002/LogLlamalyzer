"""
rag_analyzer.py

Connects Phase 15 RAG context with the local LLM.

Supports both:
    1. Raw LLMResponse analysis
    2. Structured SecurityAnalysis
"""

from backend.rag.context import RAGContext

from backend.llm.analysis import AnalysisParser

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
        analysis_parser=None,
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

        self.analysis_parser = (
            analysis_parser
            if analysis_parser is not None
            else AnalysisParser()
        )

    # ----------------------------------------------------------
    # Analyse RAG Context
    # ----------------------------------------------------------

    def analyze(self, context):
        """
        Generate an LLM security analysis from RAGContext.

        Returns:
            LLMResponse
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
    # Structured Analysis
    # ----------------------------------------------------------

    def analyze_structured(self, context):
        """
        Generate an LLM security analysis and convert
        it into a structured SecurityAnalysis object.
        """

        response = self.analyze(
            context
        )

        analysis = self.analysis_parser.parse(
            response
        )

        # Preserve useful RAG information.
        analysis.metadata.update({
            "query": context.query,
            "model": response.model,
            "rag": True,
            "log_results": len(
                context.log_results
            ),
            "knowledge_results": len(
                context.knowledge_results
            ),
        })

        return analysis

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
            "analysis_parser": self.analysis_parser.info(),
        }

    # ----------------------------------------------------------
    # Representation
    # ----------------------------------------------------------

    def __repr__(self):

        return (
            "RAGAnalyzer("
            f"model='{self.llm_client.model}')"
        )