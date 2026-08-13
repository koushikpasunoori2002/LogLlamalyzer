"""
test_analysis_parser.py

Tests conversion of an LLMResponse into a
structured SecurityAnalysis.
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

from backend.llm.analysis import (
    AnalysisParser,
    SecurityAnalysis,
)

from backend.llm.generation import LLMResponse


# --------------------------------------------------------------
# Main Test
# --------------------------------------------------------------

def main():

    print("=" * 70)
    print("ANALYSIS PARSER TEST")
    print("=" * 70)

    # ----------------------------------------------------------
    # Sample LLM response
    # ----------------------------------------------------------

    answer = """
**THREAT ASSESSMENT**

The evidence indicates a potential security threat: YES

**EVIDENCE**

1. Failed password for root from 192.168.1.20.
2. Failed password for admin from 192.168.1.30.
3. Both attempts targeted SSH port 22.

**SECURITY INTERPRETATION**

The repeated failed authentication attempts may
indicate a brute-force attack.

**SEVERITY**

Estimated severity: HIGH

**RECOMMENDED ACTIONS**

1. Investigate the source IP addresses.
2. Review SSH authentication controls.
3. Monitor for further failed attempts.

**LIMITATIONS**

The evidence does not confirm a successful compromise.
"""

    response = LLMResponse(
        query="failed SSH authentication",
        answer=answer,
        model="llama3.1:8b",
        metadata={
            "source": "ollama",
            "rag": True,
        },
    )

    # ----------------------------------------------------------
    # Parser
    # ----------------------------------------------------------

    parser = AnalysisParser()

    print("\nParser Information")

    print(
        parser.info()
    )

    # ----------------------------------------------------------
    # Parse
    # ----------------------------------------------------------

    analysis = parser.parse(
        response
    )

    if not isinstance(
        analysis,
        SecurityAnalysis,
    ):

        raise AssertionError(
            "Parser did not return SecurityAnalysis."
        )

    print(
        "\nParsed Security Analysis"
    )

    print(
        analysis
    )

    # ----------------------------------------------------------
    # Field validation
    # ----------------------------------------------------------

    if not analysis.threat_assessment:

        raise AssertionError(
            "Threat assessment was not parsed."
        )

    if len(
        analysis.evidence
    ) != 3:

        raise AssertionError(
            "Expected 3 evidence items."
        )

    if not analysis.security_interpretation:

        raise AssertionError(
            "Security interpretation was not parsed."
        )

    if analysis.severity != "HIGH":

        raise AssertionError(
            "Severity was not parsed correctly."
        )

    if len(
        analysis.recommended_actions
    ) != 3:

        raise AssertionError(
            "Expected 3 recommended actions."
        )

    if not analysis.limitations:

        raise AssertionError(
            "Limitations were not parsed."
        )

    print(
        "\nField Parsing: PASS"
    )

    # ----------------------------------------------------------
    # Metadata validation
    # ----------------------------------------------------------

    if not analysis.metadata.get(
        "parsed"
    ):

        raise AssertionError(
            "Parsed metadata is missing."
        )

    print(
        "Metadata Parsing: PASS"
    )

    # ----------------------------------------------------------
    # Validation
    # ----------------------------------------------------------

    if not analysis.is_valid():

        raise AssertionError(
            "Parsed SecurityAnalysis is invalid."
        )

    print(
        "Analysis Validation: PASS"
    )

    # ----------------------------------------------------------
    # Final result
    # ----------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "ANALYSIS PARSER TEST PASSED"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":

    main()