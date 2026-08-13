"""
test_rag_analyzer.py

Tests the integration between:
RAGContext → PromptBuilder → LLMClient → LLMResponse
"""

from pathlib import Path
import sys


# --------------------------------------------------------------
# Project Root
# --------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --------------------------------------------------------------
# Imports
# --------------------------------------------------------------

from backend.rag.context import RAGContext
from backend.llm.generation import RAGAnalyzer
from backend.llm.generation import LLMResponse


# --------------------------------------------------------------
# Main Test
# --------------------------------------------------------------

def main():

    print("=" * 70)
    print("RAG ANALYZER INTEGRATION TEST")
    print("=" * 70)

    # ----------------------------------------------------------
    # Create RAG Context
    # ----------------------------------------------------------

    context = RAGContext(
        query="failed SSH authentication brute force attack"
    )

    # ----------------------------------------------------------
    # Add Retrieved Log Evidence
    # ----------------------------------------------------------

    context.add_log_result({
        "id": "rag_log_001",
        "document": (
            "Failed password for root "
            "from 192.168.1.20 port 22 ssh2"
        ),
        "metadata": {
            "source": "auth.log",
            "log_type": "auth",
            "severity": "HIGH",
        },
        "distance": 0.82,
    })

    context.add_log_result({
        "id": "rag_log_002",
        "document": (
            "Failed password for admin "
            "from 192.168.1.30 port 22 ssh2"
        ),
        "metadata": {
            "source": "auth.log",
            "log_type": "auth",
            "severity": "HIGH",
        },
        "distance": 0.85,
    })

    # ----------------------------------------------------------
    # Add Retrieved Security Knowledge
    # ----------------------------------------------------------

    context.add_knowledge_result({
        "id": "KB_test_knowledge_chunk_1",
        "document": (
            "Repeated failed SSH authentication attempts "
            "from the same source may indicate a "
            "brute-force attack."
        ),
        "metadata": {
            "source": "test_knowledge.txt",
            "category": "authentication",
        },
        "distance": 0.36,
    })

    context.add_knowledge_result({
        "id": "KB_test_knowledge_chunk_2",
        "document": (
            "Brute-force attacks involve repeated "
            "authentication attempts."
        ),
        "metadata": {
            "source": "test_knowledge.txt",
            "category": "authentication",
        },
        "distance": 0.78,
    })

    print("\nRAG Context")
    print(context)

    # ----------------------------------------------------------
    # Create Analyzer
    # ----------------------------------------------------------

    analyzer = RAGAnalyzer()

    print("\nAnalyzer Information")
    print(analyzer.info())

    # ----------------------------------------------------------
    # Generate Analysis
    # ----------------------------------------------------------

    print("\nGenerating Security Analysis...")
    print("Please wait for llama3.1:8b...")

    response = analyzer.analyze(
        context
    )

    # ----------------------------------------------------------
    # Display Response
    # ----------------------------------------------------------

    print("\n" + "=" * 70)
    print("LLM SECURITY ANALYSIS")
    print("=" * 70)

    print(response.answer)

    # ----------------------------------------------------------
    # Response Validation
    # ----------------------------------------------------------

    if not isinstance(
        response,
        LLMResponse,
    ):

        raise AssertionError(
            "Analyzer did not return an LLMResponse."
        )

    if not response.answer:

        raise AssertionError(
            "LLM returned an empty analysis."
        )

    if response.model != "llama3.1:8b":

        raise AssertionError(
            "Unexpected LLM model."
        )

    if response.query != context.query:

        raise AssertionError(
            "Original query was not preserved."
        )

    print("\nResponse Type Test: PASS")
    print("Response Content Test: PASS")
    print("Model Test: PASS")
    print("Query Preservation Test: PASS")

    # ----------------------------------------------------------
    # RAG Metadata Validation
    # ----------------------------------------------------------

    if response.metadata.get("rag") is not True:

        raise AssertionError(
            "RAG metadata flag is missing."
        )

    if response.metadata.get("log_results") != 2:

        raise AssertionError(
            "Incorrect log result count."
        )

    if response.metadata.get("knowledge_results") != 2:

        raise AssertionError(
            "Incorrect knowledge result count."
        )

    print("\nRAG Metadata Test: PASS")

    # ----------------------------------------------------------
    # Verify Evidence Appears in Generated Answer
    # ----------------------------------------------------------

    answer_lower = response.answer.lower()

    evidence_terms = [
        "ssh",
        "authentication",
    ]

    found_terms = []

    for term in evidence_terms:

        if term in answer_lower:
            found_terms.append(term)

    print("\nEvidence Terms Found")
    print(found_terms)

    if len(found_terms) == 0:

        raise AssertionError(
            "Generated response does not appear "
            "to address the security evidence."
        )

    print("Evidence Relevance Test: PASS")

    # ----------------------------------------------------------
    # Final Result
    # ----------------------------------------------------------

    print("\n" + "=" * 70)
    print("RAG ANALYZER INTEGRATION TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()