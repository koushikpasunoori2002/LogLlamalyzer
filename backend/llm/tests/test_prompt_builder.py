"""
test_prompt_builder.py

Tests the PromptBuilder component.
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
from backend.llm.generation import PromptBuilder


# --------------------------------------------------------------
# Main Test
# --------------------------------------------------------------

def main():

    print("=" * 70)
    print("PROMPT BUILDER TEST")
    print("=" * 70)

    # ----------------------------------------------------------
    # Create RAG context
    # ----------------------------------------------------------

    context = RAGContext(
        query="failed SSH authentication brute force attack"
    )

    context.add_log_result({
        "id": "log_001",
        "document": (
            "Failed password for root "
            "from 192.168.1.20"
        ),
        "metadata": {
            "severity": "HIGH",
            "source": "auth.log",
        },
        "distance": 0.8,
    })

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

    # ----------------------------------------------------------
    # Create builder
    # ----------------------------------------------------------

    builder = PromptBuilder()

    print("\nBuilder Information")
    print(builder.info())

    # ----------------------------------------------------------
    # Build prompt
    # ----------------------------------------------------------

    prompt = builder.build(
        context
    )

    print("\nGenerated Prompt")
    print("-" * 70)
    print(prompt)

    # ----------------------------------------------------------
    # Verify required content
    # ----------------------------------------------------------

    required_content = [
        "cybersecurity log analysis assistant",
        "failed SSH authentication brute force attack",
        "Failed password for root",
        "192.168.1.20",
        "Repeated failed SSH authentication",
        "brute-force attack",
        "THREAT ASSESSMENT",
        "EVIDENCE",
        "SECURITY INTERPRETATION",
        "SEVERITY",
        "RECOMMENDED ACTIONS",
    ]

    for item in required_content:

        if item not in prompt:

            raise AssertionError(
                f"Required prompt content missing: {item}"
            )

    print(
        "\nRequired Content Test: PASS"
    )

    # ----------------------------------------------------------
    # Verify safety instructions
    # ----------------------------------------------------------

    safety_instructions = [
        "Base your analysis only on the retrieved evidence.",
        "Do not invent log events",
        "Clearly distinguish observed evidence",
        "If the evidence is insufficient",
    ]

    for instruction in safety_instructions:

        if instruction not in prompt:

            raise AssertionError(
                f"Safety instruction missing: {instruction}"
            )

    print(
        "Safety Instructions Test: PASS"
    )

    # ----------------------------------------------------------
    # Short prompt
    # ----------------------------------------------------------

    short_prompt = (
        builder.build_analysis_prompt(
            context
        )
    )

    print("\nShort Analysis Prompt")
    print("-" * 70)
    print(short_prompt)

    if context.query not in short_prompt:

        raise AssertionError(
            "Query missing from short prompt."
        )

    if "Failed password for root" not in short_prompt:

        raise AssertionError(
            "Log evidence missing from short prompt."
        )

    if "brute-force attack" not in short_prompt:

        raise AssertionError(
            "Knowledge evidence missing from short prompt."
        )

    print(
        "\nShort Prompt Test: PASS"
    )

    # ----------------------------------------------------------
    # Invalid context test
    # ----------------------------------------------------------

    try:

        builder.build("invalid context")

        raise AssertionError(
            "PromptBuilder accepted an invalid context."
        )

    except TypeError:

        print(
            "Invalid Context Test: PASS"
        )

    # ----------------------------------------------------------
    # Final result
    # ----------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        "PROMPT BUILDER TEST PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()