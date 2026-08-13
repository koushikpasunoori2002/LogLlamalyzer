"""
test_llm_response.py

Tests the LLMResponse data structure.
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

from backend.llm.generation import LLMResponse


# --------------------------------------------------------------
# Main Test
# --------------------------------------------------------------

def main():

    print("=" * 70)
    print("LLM RESPONSE TEST")
    print("=" * 70)

    # ----------------------------------------------------------
    # Create response
    # ----------------------------------------------------------

    response = LLMResponse(
        query="failed SSH authentication",
        answer=(
            "Repeated failed SSH authentication attempts "
            "may indicate a brute-force attack."
        ),
        model="llama3.1:8b",
        metadata={
            "source": "local",
            "rag": True,
        },
    )

    print("\nResponse")
    print(response)

    # ----------------------------------------------------------
    # Verify attributes
    # ----------------------------------------------------------

    if response.query != "failed SSH authentication":

        raise AssertionError(
            "Query was not stored correctly."
        )

    if "brute-force" not in response.answer:

        raise AssertionError(
            "Answer was not stored correctly."
        )

    if response.model != "llama3.1:8b":

        raise AssertionError(
            "Model was not stored correctly."
        )

    if response.metadata["source"] != "local":

        raise AssertionError(
            "Metadata was not stored correctly."
        )

    print("\nAttribute Test: PASS")

    # ----------------------------------------------------------
    # Dictionary conversion
    # ----------------------------------------------------------

    response_dict = response.to_dict()

    print("\nDictionary")
    print(response_dict)

    expected_keys = {
        "query",
        "answer",
        "model",
        "metadata",
    }

    if set(response_dict.keys()) != expected_keys:

        raise AssertionError(
            "Dictionary keys are incorrect."
        )

    if response_dict["query"] != response.query:

        raise AssertionError(
            "Dictionary query is incorrect."
        )

    if response_dict["answer"] != response.answer:

        raise AssertionError(
            "Dictionary answer is incorrect."
        )

    print("\nDictionary Test: PASS")

    # ----------------------------------------------------------
    # Length
    # ----------------------------------------------------------

    answer_length = len(response)

    print("\nAnswer Length")
    print(answer_length)

    if answer_length != len(response.answer):

        raise AssertionError(
            "Response length is incorrect."
        )

    if answer_length <= 0:

        raise AssertionError(
            "Response answer should not be empty."
        )

    print("\nLength Test: PASS")

    # ----------------------------------------------------------
    # Representation
    # ----------------------------------------------------------

    representation = repr(response)

    print("\nRepresentation")
    print(representation)

    if "LLMResponse" not in representation:

        raise AssertionError(
            "Invalid repr output."
        )

    print("\nRepresentation Test: PASS")

    # ----------------------------------------------------------
    # Final result
    # ----------------------------------------------------------

    print("\n" + "=" * 70)
    print("LLM RESPONSE TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()