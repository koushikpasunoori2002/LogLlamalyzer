"""
endpoints.py

Security analysis API endpoints for LogLlamalyzer.
"""

from fastapi import APIRouter, HTTPException

from backend.api.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    EvidenceItem,
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
# Helper - Determine Evidence Classification
# ----------------------------------------------------------

def determine_evidence_classification(
    context,
):
    """
    Determine a simple evidence classification from
    the retrieved log evidence.

    Returns
    -------
    str
        NOT SUPPORTED
        POSSIBLE
        SUPPORTED
    """

    log_results = context.log_results

    # ------------------------------------------------------
    # No log evidence
    # ------------------------------------------------------

    if not log_results:

        return "NOT SUPPORTED"

    # ------------------------------------------------------
    # Collect event types
    # ------------------------------------------------------

    event_types = set()

    for result in log_results:

        metadata = result.get(
            "metadata",
            {},
        )

        if not isinstance(
            metadata,
            dict,
        ):
            continue

        event_type = metadata.get(
            "event_type"
        )

        if event_type:

            event_types.add(
                str(event_type).upper()
            )

    # ------------------------------------------------------
    # Sudo-only evidence
    # ------------------------------------------------------

    if event_types:

        if event_types.issubset(
            {"SUDO_COMMAND"}
        ):

            return "POSSIBLE"

    # ------------------------------------------------------
    # Other evidence
    # ------------------------------------------------------

    return "POSSIBLE"


# ----------------------------------------------------------
# Helper - Build Evidence
# ----------------------------------------------------------

def build_evidence(
    results,
):
    """
    Convert security retrieval results into
    EvidenceItem objects for the API response.
    """

    evidence = []

    documents = results.get(
        "documents",
        [[]],
    )

    metadatas = results.get(
        "metadatas",
        [[]],
    )

    distances = results.get(
        "distances",
        [[]],
    )

    documents = (
        documents[0]
        if documents
        and isinstance(
            documents[0],
            list,
        )
        else []
    )

    metadatas = (
        metadatas[0]
        if metadatas
        and isinstance(
            metadatas[0],
            list,
        )
        else []
    )

    distances = (
        distances[0]
        if distances
        and isinstance(
            distances[0],
            list,
        )
        else []
    )

    for index, document in enumerate(
        documents
    ):

        metadata = (
            metadatas[index]
            if index < len(metadatas)
            and isinstance(
                metadatas[index],
                dict,
            )
            else {}
        )

        distance = (
            distances[index]
            if index < len(distances)
            else None
        )

        evidence.append(
            EvidenceItem(
                timestamp=metadata.get(
                    "timestamp"
                ),
                hostname=metadata.get(
                    "hostname"
                ),
                process=metadata.get(
                    "process"
                ),
                severity=metadata.get(
                    "severity"
                ),
                event=metadata.get(
                    "event"
                ),
                event_type=metadata.get(
                    "event_type"
                ),
                user=metadata.get(
                    "user"
                ),
                ip=metadata.get(
                    "ip"
                ),
                port=metadata.get(
                    "port"
                ),
                protocol=metadata.get(
                    "protocol"
                ),
                source_file=metadata.get(
                    "source_file"
                ),
                source=metadata.get(
                    "source"
                )
                or metadata.get(
                    "synchronized_source"
                ),
                message=str(
                    metadata.get(
                        "message",
                        document,
                    )
                ),
                distance=distance,
            )
        )

    return evidence


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
    # Create log database
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
    # Retrieve security evidence
    # ------------------------------------------------------

    security_evidence = (
        log_retriever.retrieve_security_evidence(
            query=query,
            top_k=4,
            candidate_k=100,
            source=source,
        )
    )

    # ------------------------------------------------------
    # Build structured evidence
    # ------------------------------------------------------

    evidence = build_evidence(
        security_evidence
    )

    # ------------------------------------------------------
    # Create knowledge database
    # ------------------------------------------------------

    knowledge_database = ChromaDatabase(
        collection_name="security_knowledge"
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
        top_k_logs=4,
        top_k_knowledge=3,
    )

    context = RAGContext(
        query=query
    )

    # ------------------------------------------------------
    # Add exact log evidence to context
    # ------------------------------------------------------

    context_builder._add_results(
        context,
        security_evidence,
        result_type="log",
    )

    # ------------------------------------------------------
    # Retrieve security knowledge
    # ------------------------------------------------------

    knowledge_results = (
        knowledge_retriever.retrieve_relevant(
            query=query,
            top_k=3,
        )
    )

    context_builder._add_results(
        context,
        knowledge_results,
        result_type="knowledge",
    )

    # ------------------------------------------------------
    # Context metadata
    # ------------------------------------------------------

    context.metadata = {
        "log_count": context.log_count(),
        "knowledge_count": (
            context.knowledge_count()
        ),
        "top_k_logs": 4,
        "top_k_knowledge": 3,
        "source": source,
    }

    # ------------------------------------------------------
    # Determine evidence classification
    # ------------------------------------------------------

    evidence_classification = (
        determine_evidence_classification(
            context
        )
    )

    context.metadata[
        "evidence_classification"
    ] = evidence_classification

    # ------------------------------------------------------
    # Generate security analysis
    # ------------------------------------------------------

    if context.log_count() == 0:

        # --------------------------------------------------
        # No direct log evidence
        # --------------------------------------------------

        response_text = (
            "THREAT ASSESSMENT\n\n"
            "NOT SUPPORTED\n\n"
            "SECURITY INTERPRETATION\n\n"
            "No direct log evidence was found for the requested "
            "security query. The available synchronized logs do "
            "not establish the queried threat.\n\n"
            "SEVERITY\n\n"
            "LOW\n\n"
            "RECOMMENDED ACTIONS\n\n"
            "1. Review additional log sources for related activity.\n"
            "2. Use a more specific query to investigate the event.\n"
            "3. Correlate the available logs with other security "
            "evidence if further investigation is required."
        )

        # --------------------------------------------------
        # Knowledge-only disclaimer
        # --------------------------------------------------

        if context.knowledge_count() > 0:

            response_text += (
                "\n\nRelevant security knowledge was found, "
                "but this is background information and does "
                "not establish that the queried event occurred "
                "in the monitored logs."
            )

        # --------------------------------------------------
        # No log evidence cards
        # --------------------------------------------------

        evidence = []

    else:

        # --------------------------------------------------
        # Generate normal LLM analysis
        # --------------------------------------------------

        analyzer = RAGAnalyzer()

        response = analyzer.analyze(
            context
        )

        response_text = response.answer

        # --------------------------------------------------
        # Rebuild structured evidence from context
        # --------------------------------------------------

        evidence = build_evidence(
            security_evidence
        )

    # ------------------------------------------------------
    # Extract response metadata
    # ------------------------------------------------------

    sources = extract_sources(
        context
    )

    response_metadata = {
        "sources": sources,
        "log_results": len(evidence),
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
        answer=response_text,
        source=source,
        metadata=response_metadata,
        evidence=evidence,
    )