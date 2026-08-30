"""
Multi-source API baseline evaluation.

Establishes the current behaviour of the LogLlamalyzer API
before multi-source API integration changes are introduced.

The baseline verifies:

- basic /analyze request handling
- response schema
- query preservation
- non-empty analysis response
- empty-query validation
- representative security queries
- current AnalyzeRequest schema
- current absence of source selection in the API request
"""

from pathlib import Path
import sys


# ------------------------------------------------------------------
# Project path
# ------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# ------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------

from fastapi.testclient import TestClient

from backend.api.app import app
from backend.api.schemas import AnalyzeRequest


# ------------------------------------------------------------------
# Test client
# ------------------------------------------------------------------

client = TestClient(app)


# ------------------------------------------------------------------
# Baseline queries
# ------------------------------------------------------------------

QUERIES = [
    "failed SSH authentication brute force attack",
    "suspicious sudo privilege escalation activity",
    "possible malware execution detected",
    "possible network scanning suspicious connections",
    "repeated failed login attempts",
]


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def is_valid_response(data):
    """
    Check the current /analyze response structure.
    """

    if not isinstance(
        data,
        dict,
    ):
        return False

    if "query" not in data:
        return False

    if "answer" not in data:
        return False

    if not isinstance(
        data["query"],
        str,
    ):
        return False

    if not isinstance(
        data["answer"],
        str,
    ):
        return False

    if not data["answer"].strip():
        return False

    return True


# ------------------------------------------------------------------
# Main evaluation
# ------------------------------------------------------------------

def main():

    print("=" * 70)
    print("MULTI-SOURCE API BASELINE EVALUATION")
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
    # TEST 1 - BASIC API REQUEST
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 1 - BASIC API REQUEST")

    query = QUERIES[0]

    response = client.post(
        "/analyze",
        json={
            "query": query
        },
    )

    print(
        "HTTP status:",
        response.status_code,
    )

    print(
        "Response:",
        response.json(),
    )

    basic_request_valid = (
        response.status_code == 200
        and is_valid_response(
            response.json()
        )
    )

    check(
        "Basic /analyze request",
        basic_request_valid,
    )

    # ==============================================================
    # TEST 2 - QUERY PRESERVATION
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 2 - QUERY PRESERVATION")

    query = (
        "suspicious sudo privilege escalation activity"
    )

    response = client.post(
        "/analyze",
        json={
            "query": query
        },
    )

    data = response.json()

    preserved = (
        response.status_code == 200
        and data.get("query") == query
    )

    print(
        "Input query:",
        query,
    )

    print(
        "Returned query:",
        data.get("query"),
    )

    check(
        "Query preservation",
        preserved,
    )

    # ==============================================================
    # TEST 3 - ANALYSIS RESPONSE
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 3 - ANALYSIS RESPONSE")

    query = (
        "possible malware execution detected"
    )

    response = client.post(
        "/analyze",
        json={
            "query": query
        },
    )

    data = response.json()

    answer = data.get(
        "answer",
        "",
    )

    analysis_valid = (
        response.status_code == 200
        and isinstance(
            answer,
            str,
        )
        and bool(
            answer.strip()
        )
    )

    print(
        "Answer generated:",
        bool(answer.strip()),
    )

    print(
        "Answer length:",
        len(answer),
    )

    check(
        "Analysis response generation",
        analysis_valid,
    )

    # ==============================================================
    # TEST 4 - SECURITY QUERY COVERAGE
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 4 - SECURITY QUERY COVERAGE")

    successful = 0

    for query in QUERIES:

        response = client.post(
            "/analyze",
            json={
                "query": query
            },
        )

        data = response.json()

        valid = (
            response.status_code == 200
            and is_valid_response(data)
        )

        print(
            f"Query: {query}"
        )

        print(
            "Result:",
            "PASS" if valid else "FAIL",
        )

        if valid:
            successful += 1

    print(
        "Successful security queries:",
        f"{successful}/{len(QUERIES)}",
    )

    check(
        "Security query coverage",
        successful == len(QUERIES),
    )

    # ==============================================================
    # TEST 5 - EMPTY QUERY
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 5 - EMPTY QUERY VALIDATION")

    response = client.post(
        "/analyze",
        json={
            "query": "   "
        },
    )

    print(
        "HTTP status:",
        response.status_code,
    )

    try:

        body = response.json()

    except Exception:

        body = None

    print(
        "Response:",
        body,
    )

    empty_query_valid = (
        response.status_code
        == 400
    )

    check(
        "Empty query validation",
        empty_query_valid,
    )

    # ==============================================================
    # TEST 6 - MISSING QUERY FIELD
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 6 - MISSING QUERY FIELD")

    response = client.post(
        "/analyze",
        json={},
    )

    print(
        "HTTP status:",
        response.status_code,
    )

    missing_query_valid = (
        response.status_code
        == 422
    )

    check(
        "Missing query validation",
        missing_query_valid,
    )

    # ==============================================================
    # TEST 7 - CURRENT REQUEST SCHEMA
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 7 - CURRENT REQUEST SCHEMA")

    schema_fields = set(
        AnalyzeRequest.model_fields.keys()
    )

    print(
        "AnalyzeRequest fields:",
        sorted(schema_fields),
    )

    schema_valid = (
        schema_fields
        == {"query"}
    )

    check(
        "Current AnalyzeRequest schema",
        schema_valid,
    )

    # ==============================================================
    # TEST 8 - CURRENT API DOES NOT EXPOSE SOURCE
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 8 - SOURCE FIELD BASELINE")

    source_supported = (
        "source"
        in AnalyzeRequest.model_fields
    )

    print(
        "Source field currently exposed:",
        source_supported,
    )

    # This is deliberately informational in the baseline.
    # The current API is expected not to expose source selection.
    check(
        "Source-aware API baseline identified",
        not source_supported,
    )

    # ==============================================================
    # TEST 9 - SOURCE REQUEST BASELINE
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 9 - SOURCE REQUEST BASELINE")

    query = (
        "failed SSH authentication brute force attack"
    )

    response = client.post(
        "/analyze",
        json={
            "query": query,
            "source": "server-a",
        },
    )

    print(
        "HTTP status:",
        response.status_code,
    )

    print(
        "Response:",
        response.json(),
    )

    # At baseline the API does not yet define source
    # in AnalyzeRequest. FastAPI/Pydantic ignores the
    # extra field under the current schema behaviour.
    source_ignored = (
        response.status_code == 200
        and "source"
        not in response.json()
    )

    print(
        "Source selection currently returned:",
        "YES"
        if "source"
        in response.json()
        else "NO",
    )

    check(
        "Source-aware API baseline behaviour",
        source_ignored,
    )

    # ==============================================================
    # TEST 10 - RESPONSE SCHEMA
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 10 - RESPONSE SCHEMA")

    response = client.post(
        "/analyze",
        json={
            "query": QUERIES[4]
        },
    )

    data = response.json()

    response_fields = set(
        data.keys()
    )

    print(
        "Response fields:",
        sorted(response_fields),
    )

    response_schema_valid = (
        "query" in response_fields
        and "answer" in response_fields
        and response_fields
        == {"query", "answer"}
    )

    check(
        "Current response schema",
        response_schema_valid,
    )

    # ==============================================================
    # RESULTS
    # ==============================================================

    print()
    print("=" * 70)
    print("MULTI-SOURCE API BASELINE RESULTS")
    print("=" * 70)

    print(
        f"Tests passed: "
        f"{passed}/10"
    )

    print(
        f"Tests failed: "
        f"{failed}"
    )

    print()
    print(
        "Current request fields:",
        sorted(schema_fields),
    )

    print(
        "Current source selection support:",
        (
            "AVAILABLE"
            if source_supported
            else "NOT EXPOSED"
        ),
    )

    print(
        "Security query success rate:",
        f"{successful}/{len(QUERIES)}",
    )

    # ==============================================================
    # Validation
    # ==============================================================

    if failed != 0:

        raise AssertionError(
            "Multi-source API baseline evaluation failed."
        )

    print()
    print("=" * 70)
    print(
        "MULTI-SOURCE API BASELINE EVALUATION PASSED"
    )
    print("=" * 70)

    print(
        "The current API baseline has been established."
    )

    print(
        "The existing /analyze endpoint accepts a query "
        "but does not yet expose source selection."
    )

    print(
        "This provides the baseline for the next "
        "multi-source API integration step."
    )

    print("=" * 70)


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    main()