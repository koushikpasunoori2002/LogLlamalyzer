"""
endpoints.py

Security analysis API endpoints for LogLlamalyzer.
"""

from fastapi import APIRouter, HTTPException

from backend.api.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
)

from backend.database.chroma import ChromaDatabase

from backend.rag.context import (
    ContextBuilder,
    RAGContext,
)

from backend.rag.retriever import Retriever

from backend.knowledge.knowledge_retriever import (
    KnowledgeRetriever,
)

from backend.llm.generation import RAGAnalyzer


router = APIRouter()


# ----------------------------------------------------------
# Helper - Extract Sources
# ----------------------------------------------------------

def extract_sources(context):
    """
    Extract unique source identifiers from log results
    contained in the RAG context.
    """

    sources = set()

    for result in context.log_results:

        metadata = result.get(
            "metadata",
            {},
        )

        if not isinstance(
            metadata,
            dict,
        ):
            continue

        source = metadata.get(
            "source"
        )

        if source is None:

            source = metadata.get(
                "synchronized_source"
            )

        if source is not None:

            source = str(
                source
            ).strip()

            if source:

                sources.add(
                    source
                )

    return sorted(
        sources
    )


# ----------------------------------------------------------
# Analyze Endpoint
# ----------------------------------------------------------

@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
)
def analyze(
    request: AnalyzeRequest,
):
    """
    Analyse a security query using the complete
    RAG + LLM pipeline.

    An optional source can be supplied to restrict
    log retrieval to one synchronized source.
    """

    # ------------------------------------------------------
    # Validate query
    # ------------------------------------------------------

    query = request.query.strip()

    if not query:

        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty.",
        )

    # ------------------------------------------------------
    # Validate source
    # ------------------------------------------------------

    source = None

    if request.source is not None:

        source = request.source.strip()

        if not source:

            raise HTTPException(
                status_code=400,
                detail="Source cannot be empty.",
            )

    # ------------------------------------------------------
    # Create log database explicitly
    #
    # Passing the database into Retriever makes the API's
    # data source explicit and allows controlled testing of
    # source-aware retrieval.
    # ------------------------------------------------------

    log_database = ChromaDatabase(
        collection_name="log_embeddings",
    )

    # ------------------------------------------------------
    # Create log retriever
    # ------------------------------------------------------

    log_retriever = Retriever(
        database=log_database,
        top_k=3,
        distance_threshold=0.98,
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
    # Context builder
    # ------------------------------------------------------

    context_builder = ContextBuilder(
        log_retriever=log_retriever,
        knowledge_retriever=knowledge_retriever,
        top_k_logs=3,
        top_k_knowledge=3,
    )

    # ------------------------------------------------------
    # Build RAG context
    # ------------------------------------------------------

    if source is None:

        context = context_builder.build(
            query
        )

    else:

        # --------------------------------------------------
        # Source-filtered log retrieval
        # --------------------------------------------------

        source_results = (
            log_retriever.retrieve(
                query=query,
                top_k=3,
                source=source,
            )
        )

        # --------------------------------------------------
        # Security knowledge is not source-specific.
        # --------------------------------------------------

        knowledge_results = (
            knowledge_retriever.retrieve(
                query=query,
                top_k=3,
            )
        )

        context = RAGContext(
            query=query
        )

        context_builder._add_results(
            context,
            source_results,
            result_type="log",
        )

        context_builder._add_results(
            context,
            knowledge_results,
            result_type="knowledge",
        )

        context.metadata = {
            "log_count": context.log_count(),
            "knowledge_count": (
                context.knowledge_count()
            ),
            "top_k_logs": 3,
            "top_k_knowledge": 3,
            "source": source,
        }

    # ------------------------------------------------------
    # Generate security analysis
    # ------------------------------------------------------

    analyzer = RAGAnalyzer()

    response = analyzer.analyze(
        context
    )

    # ------------------------------------------------------
    # Extract response metadata
    # ------------------------------------------------------

    sources = extract_sources(
        context
    )

    response_metadata = {
        "sources": sources,
        "log_results": context.log_count(),
        "knowledge_results": (
            context.knowledge_count()
        ),
    }

    # ------------------------------------------------------
    # Close resources
    # ------------------------------------------------------

    try:

        log_retriever.close()

    except Exception:

        pass

    try:

        knowledge_database.close()

    except Exception:

        pass

    # ------------------------------------------------------
    # Return response
    # ------------------------------------------------------

    return AnalyzeResponse(
        query=query,
        answer=response.answer,
        source=source,
        metadata=response_metadata,
    )