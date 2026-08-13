"""
test_security_analysis.py

Tests the SecurityAnalysis data structure.
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
# Import
# --------------------------------------------------------------

from backend.llm.analysis import SecurityAnalysis


# --------------------------------------------------------------
# Main Test
# --------------------------------------------------------------

def main():

    print("=" * 70)
    print("SECURITY ANALYSIS TEST")
    print("=" * 70)

    # ----------------------------------------------------------
    # Create analysis
    # ----------------------------------------------------------

    analysis = SecurityAnalysis(
        threat_assessment=(
            "Potential SSH brute-force activity detected."
        ),
        evidence=[
            "Failed password for root from 192.168.1.20",
            "Failed password for admin from 192.168.1.30",
        ],
        security_interpretation=(
            "Repeated failed SSH authentication attempts "
            "may indicate brute-force activity."
        ),
        severity="HIGH",
        recommended_actions=[
            "Investigate source IP addresses.",
            "Review SSH authentication controls.",
            "Monitor for further failed attempts.",
        ],
        limitations=(
            "The available evidence does not confirm "
            "that a successful compromise occurred."
        ),
        metadata={
            "source": "llama3.1:8b",
            "rag": True,
        },
    )

    print("\nSecurity Analysis")
    print(analysis)

    # ----------------------------------------------------------
    # Dictionary
    # ----------------------------------------------------------

    print("\nDictionary")

    print(
        analysis.to_dict()
    )

    # ----------------------------------------------------------
    # Validation
    # ----------------------------------------------------------

    print("\nValidation")

    print(
        "Valid:",
        analysis.is_valid()
    )

    if not analysis.is_valid():

        raise AssertionError(
            "SecurityAnalysis validation failed."
        )

    print(
        "Validation Test: PASS"
    )

    # ----------------------------------------------------------
    # Information
    # ----------------------------------------------------------

    print("\nInformation")

    print(
        analysis.info()
    )

    # ----------------------------------------------------------
    # Field Tests
    # ----------------------------------------------------------

    if analysis.severity != "HIGH":

        raise AssertionError(
            "Severity value is incorrect."
        )

    if len(
        analysis.evidence
    ) != 2:

        raise AssertionError(
            "Evidence count is incorrect."
        )

    if len(
        analysis.recommended_actions
    ) != 3:

        raise AssertionError(
            "Recommended action count is incorrect."
        )

    if not analysis.threat_assessment:

        raise AssertionError(
            "Threat assessment is empty."
        )

    if not analysis.security_interpretation:

        raise AssertionError(
            "Security interpretation is empty."
        )

    print(
        "Field Test: PASS"
    )

    # ----------------------------------------------------------
    # Final Result
    # ----------------------------------------------------------

    print("\n" + "=" * 70)

    print(
        "SECURITY ANALYSIS TEST PASSED"
    )

    print("=" * 70)


# --------------------------------------------------------------
# Entry Point
# --------------------------------------------------------------

if __name__ == "__main__":

    main()