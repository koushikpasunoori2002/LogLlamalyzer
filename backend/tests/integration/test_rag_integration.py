"""
test_rag_integration.py

Tests integration between:
Retriever
KnowledgeRetriever
ContextBuilder
RAGContext
RAGAnalyzer
"""

from backend.rag.retriever import Retriever
from backend.knowledge.knowledge_retriever import KnowledgeRetriever
from backend.rag.context import ContextBuilder
from backend.rag.context import RAGContext
from backend.llm.generation import RAGAnalyzer
from backend.database.chroma import ChromaDatabase


def test_rag_context_integration():

    query = "failed SSH authentication brute force attack"

    # ------------------------------------------------------
    # Create log retriever
    # ------------------------------------------------------

    log_retriever = Retriever(
        top_k=3
    )

    assert log_retriever is not None

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

    assert knowledge_retriever is not None

    # ------------------------------------------------------
    # Create context builder
    # ------------------------------------------------------

    context_builder = ContextBuilder(
        log_retriever=log_retriever,
        knowledge_retriever=knowledge_retriever,
        top_k_logs=3,
        top_k_knowledge=3,
    )

    assert context_builder is not None

    # ------------------------------------------------------
    # Build RAG context
    # ------------------------------------------------------

    context = context_builder.build(
        query
    )

    assert isinstance(
        context,
        RAGContext,
    )

    assert context.query == query

    # ------------------------------------------------------
    # Validate context structure
    # ------------------------------------------------------

    assert hasattr(
        context,
        "log_results",
    )

    assert hasattr(
        context,
        "knowledge_results",
    )

    assert context.metadata is not None

    # ------------------------------------------------------
    # Create analyzer
    # ------------------------------------------------------

    analyzer = RAGAnalyzer()

    assert analyzer is not None

    # ------------------------------------------------------
    # Generate analysis
    # ------------------------------------------------------

    response = analyzer.analyze(
        context
    )

    assert response is not None

    assert isinstance(
        response.answer,
        str,
    )

    assert len(
        response.answer.strip()
    ) > 0

    # ------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------

    log_retriever.close()
    knowledge_retriever.close()


if __name__ == "__main__":

    print("=" * 60)
    print("PHASE 20 RAG INTEGRATION TEST")
    print("=" * 60)

    test_rag_context_integration()

    print("Retriever: PASS")
    print("Knowledge Retriever: PASS")
    print("ContextBuilder: PASS")
    print("RAGContext: PASS")
    print("RAGAnalyzer: PASS")

    print("=" * 60)
    print("PHASE 20 RAG INTEGRATION TEST PASSED")
    print("=" * 60)