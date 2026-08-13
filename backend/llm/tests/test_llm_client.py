"""
test_llm_client.py

Tests the local Ollama LLM client.
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

from backend.llm.generation import LLMClient


# --------------------------------------------------------------
# Main Test
# --------------------------------------------------------------

def main():

    print("=" * 70)
    print("LLM CLIENT TEST")
    print("=" * 70)

    # ----------------------------------------------------------
    # Create client
    # ----------------------------------------------------------

    client = LLMClient()

    print("\nClient Information")
    print(client.info())

    # ----------------------------------------------------------
    # Check Ollama
    # ----------------------------------------------------------

    print("\nOllama Availability")

    if not client.is_available():

        raise RuntimeError(
            "Ollama is not available. "
            "Make sure Ollama is running."
        )

    print("Ollama Available: PASS")

    # ----------------------------------------------------------
    # Check model
    # ----------------------------------------------------------

    print("\nModel Availability")

    if not client.model_available():

        raise RuntimeError(
            f"Model '{client.model}' is not available "
            "in Ollama."
        )

    print(
        f"Model Available ({client.model}): PASS"
    )

    # ----------------------------------------------------------
    # Generate response
    # ----------------------------------------------------------

    print("\nGenerating Response...")

    prompt = (
        "Explain in one short sentence what a "
        "failed SSH password attempt means."
    )

    response = client.generate(
        prompt
    )

    print("\nLLM Response")
    print("-" * 70)
    print(response)

    # ----------------------------------------------------------
    # Validate response
    # ----------------------------------------------------------

    if not response.answer:

        raise AssertionError(
            "LLM returned an empty answer."
        )

    if response.model != client.model:

        raise AssertionError(
            "Response model does not match client model."
        )

    if response.metadata.get("source") != "ollama":

        raise AssertionError(
            "Response source should be Ollama."
        )

    if response.metadata.get("done") is not True:

        raise AssertionError(
            "Ollama did not report completed generation."
        )

    print(
        "\nResponse Validation: PASS"
    )

    # ----------------------------------------------------------
    # Final result
    # ----------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        "LLM CLIENT TEST PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()