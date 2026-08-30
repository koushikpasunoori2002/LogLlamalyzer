"""
Reliability evaluation.

Verifies that LogLlamalyzer remains stable when:

- invalid inputs are supplied
- repeated requests are made
- Ollama is unavailable
- Ollama requests time out
- Ollama returns an unsuccessful response
- Ollama returns an empty response
- Retriever input validation is triggered
- valid requests continue to work after handled failures

The test uses mocked HTTP failures for Ollama so that reliability
behaviour can be tested without deliberately shutting down Ollama.
"""

from pathlib import Path
import sys


# ------------------------------------------------------------------
# Project path
# ------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------

from unittest.mock import Mock, patch

import requests

from backend.llm.generation import LLMClient
from backend.rag.retriever import Retriever


# ------------------------------------------------------------------
# Main reliability evaluation
# ------------------------------------------------------------------

def main():

    print("=" * 70)
    print("RELIABILITY EVALUATION")
    print("=" * 70)

    passed = 0
    failed = 0

    def check(
        name,
        condition,
    ):

        nonlocal passed, failed

        if condition:

            print(
                f"{name}: PASS"
            )

            passed += 1

        else:

            print(
                f"{name}: FAIL"
            )

            failed += 1

    # ==============================================================
    # TEST 1 - LLM CLIENT CONFIGURATION
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 1 - LLM CLIENT CONFIGURATION")

    client = LLMClient()

    information = client.info()

    print(
        "Client information:",
        information,
    )

    configuration_valid = (
        information.get("component")
        == "LLMClient"
        and information.get("provider")
        == "Ollama"
        and information.get("model")
        == "llama3.1:8b"
        and information.get("timeout")
        is not None
        and information.get("num_predict")
        is not None
        and information.get("keep_alive")
        is not None
    )

    check(
        "LLM client configuration test",
        configuration_valid,
    )

    # ==============================================================
    # TEST 2 - EMPTY PROMPT VALIDATION
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 2 - EMPTY PROMPT VALIDATION")

    empty_prompt_handled = False

    try:

        client.generate("")

    except ValueError:

        empty_prompt_handled = True

    except Exception as exc:

        print(
            "Unexpected exception:",
            exc,
        )

    print(
        "Empty prompt handling:",
        "PASS"
        if empty_prompt_handled
        else "FAIL",
    )

    check(
        "Empty prompt validation",
        empty_prompt_handled,
    )

    # ==============================================================
    # TEST 3 - INVALID PROMPT TYPE
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 3 - INVALID PROMPT TYPE")

    invalid_prompt_handled = False

    try:

        client.generate(
            None
        )

    except TypeError:

        invalid_prompt_handled = True

    except Exception as exc:

        print(
            "Unexpected exception:",
            exc,
        )

    print(
        "Invalid prompt handling:",
        "PASS"
        if invalid_prompt_handled
        else "FAIL",
    )

    check(
        "Invalid prompt type validation",
        invalid_prompt_handled,
    )

    # ==============================================================
    # TEST 4 - OLLAMA CONNECTION FAILURE
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 4 - OLLAMA CONNECTION FAILURE")

    connection_failure_handled = False

    with patch(
        "backend.llm.generation.llm_client.requests.post"
    ) as mock_post:

        mock_post.side_effect = (
            requests.exceptions.ConnectionError(
                "Connection refused"
            )
        )

        try:

            client.generate(
                "test security query"
            )

        except RuntimeError as exc:

            connection_failure_handled = (
                "Could not connect to Ollama"
                in str(exc)
            )

            print(
                "Handled error:",
                exc,
            )

        except Exception as exc:

            print(
                "Unexpected exception:",
                exc,
            )

    check(
        "Ollama connection failure handling",
        connection_failure_handled,
    )

    # ==============================================================
    # TEST 5 - OLLAMA TIMEOUT
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 5 - OLLAMA TIMEOUT")

    timeout_handled = False

    with patch(
        "backend.llm.generation.llm_client.requests.post"
    ) as mock_post:

        mock_post.side_effect = (
            requests.exceptions.Timeout(
                "Request timed out"
            )
        )

        try:

            client.generate(
                "test security query"
            )

        except RuntimeError as exc:

            timeout_handled = (
                "timed out"
                in str(exc).lower()
            )

            print(
                "Handled error:",
                exc,
            )

        except Exception as exc:

            print(
                "Unexpected exception:",
                exc,
            )

    check(
        "Ollama timeout handling",
        timeout_handled,
    )

    # ==============================================================
    # TEST 6 - OLLAMA HTTP REQUEST FAILURE
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 6 - OLLAMA REQUEST FAILURE")

    request_failure_handled = False

    with patch(
        "backend.llm.generation.llm_client.requests.post"
    ) as mock_post:

        mock_response = Mock()

        mock_response.raise_for_status.side_effect = (
            requests.exceptions.HTTPError(
                "HTTP 500"
            )
        )

        mock_post.return_value = (
            mock_response
        )

        try:

            client.generate(
                "test security query"
            )

        except RuntimeError as exc:

            request_failure_handled = (
                "request failed"
                in str(exc).lower()
            )

            print(
                "Handled error:",
                exc,
            )

        except Exception as exc:

            print(
                "Unexpected exception:",
                exc,
            )

    check(
        "Ollama request failure handling",
        request_failure_handled,
    )

    # ==============================================================
    # TEST 7 - EMPTY OLLAMA RESPONSE
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 7 - EMPTY OLLAMA RESPONSE")

    empty_response_handled = False

    with patch(
        "backend.llm.generation.llm_client.requests.post"
    ) as mock_post:

        mock_response = Mock()

        mock_response.raise_for_status.return_value = (
            None
        )

        mock_response.json.return_value = {
            "response": "",
            "done": True,
        }

        mock_post.return_value = (
            mock_response
        )

        try:

            client.generate(
                "test security query"
            )

        except RuntimeError as exc:

            empty_response_handled = (
                "empty response"
                in str(exc).lower()
            )

            print(
                "Handled error:",
                exc,
            )

        except Exception as exc:

            print(
                "Unexpected exception:",
                exc,
            )

    check(
        "Empty Ollama response handling",
        empty_response_handled,
    )

    # ==============================================================
    # TEST 8 - RETRIEVER EMPTY QUERY
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 8 - RETRIEVER EMPTY QUERY")

    retriever_empty_query_handled = False

    try:

        retriever = Retriever(
            top_k=3,
        )

        retriever.retrieve(
            query=""
        )

    except ValueError:

        retriever_empty_query_handled = True

    except Exception as exc:

        print(
            "Unexpected exception:",
            exc,
        )

    else:

        try:

            retriever.close()

        except Exception:

            pass

    print(
        "Empty query handling:",
        "PASS"
        if retriever_empty_query_handled
        else "FAIL",
    )

    check(
        "Retriever empty query validation",
        retriever_empty_query_handled,
    )

    # ==============================================================
    # TEST 9 - RETRIEVER INVALID TOP-K
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 9 - RETRIEVER INVALID TOP-K")

    invalid_top_k_handled = False

    try:

        Retriever(
            top_k=0
        )

    except ValueError:

        invalid_top_k_handled = True

    except Exception as exc:

        print(
            "Unexpected exception:",
            exc,
        )

    print(
        "Invalid top_k handling:",
        "PASS"
        if invalid_top_k_handled
        else "FAIL",
    )

    check(
        "Retriever top_k validation",
        invalid_top_k_handled,
    )

    # ==============================================================
    # TEST 10 - RETRIEVER INVALID THRESHOLD
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 10 - RETRIEVER INVALID DISTANCE THRESHOLD")

    invalid_threshold_handled = False

    try:

        Retriever(
            top_k=3,
            distance_threshold=-1,
        )

    except ValueError:

        invalid_threshold_handled = True

    except Exception as exc:

        print(
            "Unexpected exception:",
            exc,
        )

    print(
        "Invalid distance threshold handling:",
        "PASS"
        if invalid_threshold_handled
        else "FAIL",
    )

    check(
        "Retriever distance threshold validation",
        invalid_threshold_handled,
    )

    # ==============================================================
    # TEST 11 - VALID LLM REQUEST AFTER FAILURE
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 11 - VALID REQUEST AFTER FAILURE")

    recovery_success = False

    with patch(
        "backend.llm.generation.llm_client.requests.post"
    ) as mock_post:

        # First request fails.
        failing_response = Mock()

        mock_post.side_effect = [
            requests.exceptions.Timeout(
                "temporary timeout"
            ),
        ]

        try:

            client.generate(
                "temporary failure test"
            )

        except RuntimeError:

            pass

        # Replace the mocked failure with a valid response.
        successful_response = Mock()

        successful_response.raise_for_status.return_value = (
            None
        )

        successful_response.json.return_value = {
            "response": (
                "Security analysis completed."
            ),
            "done": True,
            "total_duration": 1000000,
            "load_duration": 100000,
            "eval_count": 10,
            "eval_duration": 900000,
        }

        mock_post.side_effect = None

        mock_post.return_value = (
            successful_response
        )

        try:

            response = client.generate(
                "valid recovery test"
            )

            recovery_success = (
                response is not None
                and bool(
                    response.answer.strip()
                )
            )

        except Exception as exc:

            print(
                "Recovery request error:",
                exc,
            )

    print(
        "Recovery after handled failure:",
        "PASS"
        if recovery_success
        else "FAIL",
    )

    check(
        "Post-failure recovery",
        recovery_success,
    )

    # ==============================================================
    # TEST 12 - REPEATED VALID REQUESTS
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 12 - REPEATED VALID REQUESTS")

    repeated_request_success = True

    with patch(
        "backend.llm.generation.llm_client.requests.post"
    ) as mock_post:

        successful_response = Mock()

        successful_response.raise_for_status.return_value = (
            None
        )

        successful_response.json.return_value = {
            "response": (
                "Repeated request handled successfully."
            ),
            "done": True,
        }

        mock_post.return_value = (
            successful_response
        )

        for index in range(3):

            try:

                response = client.generate(
                    f"repeated reliability test {index}"
                )

                if (
                    response is None
                    or not response.answer.strip()
                ):

                    repeated_request_success = False

            except Exception as exc:

                repeated_request_success = False

                print(
                    "Repeated request error:",
                    exc,
                )

    print(
        "Repeated requests:",
        "PASS"
        if repeated_request_success
        else "FAIL",
    )

    check(
        "Repeated valid request stability",
        repeated_request_success,
    )

    # ==============================================================
    # RESULTS
    # ==============================================================

    print()
    print("=" * 70)
    print("RELIABILITY RESULTS")
    print("=" * 70)

    print(
        f"Reliability tests passed: "
        f"{passed}/12"
    )

    print(
        f"Reliability tests failed: "
        f"{failed}"
    )

    # ==============================================================
    # Validation
    # ==============================================================

    if failed != 0:

        raise AssertionError(
            "Reliability evaluation failed."
        )

    if passed != 12:

        raise AssertionError(
            "Expected all 12 reliability tests to pass."
        )

    print()
    print(
        "Input validation: PASS"
    )

    print(
        "Ollama connection failure handling: PASS"
    )

    print(
        "Ollama timeout handling: PASS"
    )

    print(
        "Ollama request failure handling: PASS"
    )

    print(
        "Empty response handling: PASS"
    )

    print(
        "Retriever validation: PASS"
    )

    print(
        "Post-failure recovery: PASS"
    )

    print(
        "Repeated request stability: PASS"
    )

    print()
    print("=" * 70)
    print(
        "RELIABILITY EVALUATION PASSED"
    )
    print("=" * 70)


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    main()