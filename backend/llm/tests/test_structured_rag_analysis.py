"""
test_structured_rag_analysis.py

Phase 17 Step 3 integration test.

Tests:

RAGContext
    ->
RAGAnalyzer
    ->
LLMResponse
    ->
AnalysisParser
    ->
SecurityAnalysis
"""

from pathlib import Path
import sys


# --------------------------------------------------------------
# Project Root
# --------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# --------------------------------------------------------------
# Imports
# --------------------------------------------------------------

from backend.rag.context import RAGContext

from backend.llm.generation import RAGAnalyzer
from backend.llm.generation import LLMResponse

from backend.llm.analysis import SecurityAnalysis


# --------------------------------------------------------------
# Main Test
# --------------------------------------------------------------

def main():

    print("=" * 70)
    print("STRUCTURED RAG ANALYSIS TEST")
    print("=" * 70)

    # ----------------------------------------------------------
    # Create RAG context
    # ----------------------------------------------------------

    context = RAGContext(
        query=(
            "failed SSH authentication "
            "brute force attack"
        )
    )

    # ----------------------------------------------------------
    # Add retrieved logs
    # ----------------------------------------------------------

    context.add_log_result({
        "id": "log_001",
        "document": (
            "Failed password for root "
            "from 192.168.1.20 port 22 ssh2"
        ),
        "metadata": {
            "severity": "HIGH",
            "source": "auth.log",
            "log_type": "auth",
        },
        "distance": 0.8,
    })

    context.add_log_result({
        "id": "log_002",
        "document": (
            "Failed password for admin "
            "from 192.168.1.30 port 22 ssh2"
        ),
        "metadata": {
            "severity": "HIGH",
            "source": "auth.log",
            "log_type": "auth",
        },
        "distance": 0.82,
    })

    # ----------------------------------------------------------
    # Add security knowledge
    # ----------------------------------------------------------

    context.add_knowledge_result({
        "id": "KB_001",
        "document": (
            "Repeated failed SSH authentication "
            "attempts may indicate a brute-force attack."
        ),
        "metadata": {
            "category": "authentication",
        },
        "distance": 0.3,
    })

    context.add_knowledge_result({
        "id": "KB_002",
        "document": (
            "Brute-force attacks involve repeated "
            "authentication attempts against a service."
        ),
        "metadata": {
            "category": "authentication",
        },
        "distance": 0.75,
    })

    print("\nRAG Context")
    print(context)

    # ----------------------------------------------------------
    # Create analyzer
    # ----------------------------------------------------------

    analyzer = RAGAnalyzer()

    print("\nAnalyzer Information")

    print(
        analyzer.info()
    )

    # ----------------------------------------------------------
    # Generate raw response first
    # ----------------------------------------------------------

    print(
        "\nGenerating LLM analysis..."
    )

    response = analyzer.analyze(
        context
    )

    if not isinstance(
        response,
        LLMResponse,
    ):
        raise AssertionError(
            "analyze() did not return LLMResponse."
        )

    if not response.answer:
        raise AssertionError(
            "LLM response contains no answer."
        )

    print(
        "\nRaw LLM Response: PASS"
    )

    # ----------------------------------------------------------
    # Generate structured response
    # ----------------------------------------------------------

    print(
        "\nParsing structured security analysis..."
    )

    analysis = analyzer.analyze_structured(
        context
    )

    # ----------------------------------------------------------
    # Type validation
    # ----------------------------------------------------------

    if not isinstance(
        analysis,
        SecurityAnalysis,
    ):
        raise AssertionError(
            "analyze_structured() did not return "
            "SecurityAnalysis."
        )

    print(
        "SecurityAnalysis Type: PASS"
    )

    # ----------------------------------------------------------
    # Display analysis
    # ----------------------------------------------------------

    print(
        "\nStructured Security Analysis"
    )

    print(
        analysis
    )

    # ----------------------------------------------------------
    # Validate fields
    # ----------------------------------------------------------

    if not analysis.threat_assessment:

        raise AssertionError(
            "Threat assessment is empty."
        )

    if not analysis.evidence:

        raise AssertionError(
            "Evidence was not parsed."
        )

    if not analysis.security_interpretation:

        raise AssertionError(
            "Security interpretation is empty."
        )

    if analysis.severity not in [
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    ]:

        raise AssertionError(
            "Invalid severity value: "
            + str(analysis.severity)
        )

    if not analysis.recommended_actions:

        raise AssertionError(
            "Recommended actions were not parsed."
        )

    print(
        "\nStructured Fields: PASS"
    )

    # ----------------------------------------------------------
    # Validate metadata
    # ----------------------------------------------------------

    if not analysis.metadata.get(
        "rag"
    ):

        raise AssertionError(
            "RAG metadata missing."
        )

    if analysis.metadata.get(
        "query"
    ) != context.query:

        raise AssertionError(
            "Query was not preserved."
        )

    if analysis.metadata.get(
        "model"
    ) != response.model:

        raise AssertionError(
            "Model metadata was not preserved."
        )

    print(
        "Metadata Preservation: PASS"
    )

    # ----------------------------------------------------------
    # Validate analysis
    # ----------------------------------------------------------

    if not analysis.is_valid():

        raise AssertionError(
            "Structured security analysis is invalid."
        )

    print(
        "Analysis Validation: PASS"
    )

    # ----------------------------------------------------------
    # Relevance check
    # ----------------------------------------------------------

    combined_text = (
        analysis.threat_assessment
        + " "
        + analysis.security_interpretation
        + " "
        + " ".join(
            analysis.evidence
        )
    ).lower()

    relevant_terms = [
        "ssh",
        "authentication",
        "failed",
    ]

    found_terms = [
        term
        for term in relevant_terms
        if term in combined_text
    ]

    print(
        "\nRelevant Terms Found"
    )

    print(
        found_terms
    )

    if len(found_terms) < 2:

        raise AssertionError(
            "Structured analysis is not sufficiently "
            "relevant to the query."
        )

    print(
        "Analysis Relevance: PASS"
    )

    # ----------------------------------------------------------
    # Final result
    # ----------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "STRUCTURED RAG ANALYSIS TEST PASSED"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":

    main()