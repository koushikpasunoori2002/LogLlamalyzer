"""
endpoints.py

Security analysis API endpoints for LogLlamalyzer.
"""

from fastapi import APIRouter

from backend.api.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
)

from backend.database.chroma import ChromaDatabase

from backend.rag.context import ContextBuilder
from backend.rag.retriever import Retriever
from backend.knowledge.knowledge_retriever import KnowledgeRetriever

from backend.llm.generation import RAGAnalyzer


router = APIRouter()


# ----------------------------------------------------------
# Analyze Endpoint
# ----------------------------------------------------------

@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
)
def analyze(request: AnalyzeRequest):
    """
    Analyse a security query using the complete
    RAG + LLM pipeline.
    """

    # ------------------------------------------------------
    # Validate query
    # ------------------------------------------------------

    query = request.query.strip()

    if not query:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty.",
        )

    # ------------------------------------------------------
    # Create log retriever
    # ------------------------------------------------------

    log_retriever = Retriever(
        top_k=3
    )

    # ------------------------------------------------------
    # Create knowledge database
    # ------------------------------------------------------

    knowledge_database = ChromaDatabase(
        collection_name="knowledge_embeddings"
    )

    # ------------------------------------------------------
    # Create knowledge retriever
    # ------------------------------------------------------

    knowledge_retriever = KnowledgeRetriever(
        database=knowledge_database,
        top_k=3,
    )

    # ------------------------------------------------------
    # Build RAG context
    # ------------------------------------------------------

    context_builder = ContextBuilder(
        log_retriever=log_retriever,
        knowledge_retriever=knowledge_retriever,
        top_k_logs=3,
        top_k_knowledge=3,
    )

    context = context_builder.build(
        query
    )

    # ------------------------------------------------------
    # Generate security analysis
    # ------------------------------------------------------

    analyzer = RAGAnalyzer()

    response = analyzer.analyze(
        context
    )

    # ------------------------------------------------------
    # Return API response
    # ------------------------------------------------------

    return AnalyzeResponse(
        query=query,
        answer=response.answer,
    )