"""
Source-aware API evaluation.

Verifies that the /analyze endpoint supports optional
source selection while preserving backwards compatibility.
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
# Client
# ------------------------------------------------------------------

client = TestClient(app)


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------

def main():

    print("=" * 70)
    print("SOURCE-AWARE API EVALUATION")
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
    # TEST 1 - BACKWARDS COMPATIBILITY
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 1 - BACKWARDS COMPATIBILITY")

    response = client.post(
        "/analyze",
        json={
            "query": (
                "failed SSH authentication "
                "brute force attack"
            )
        },
    )

    print(
        "HTTP status:",
        response.status_code,
    )

    data = response.json()

    print(
        "Response fields:",
        sorted(data.keys()),
    )

    compatibility_pass = (
        response.status_code == 200
        and data.get("query")
        == (
            "failed SSH authentication "
            "brute force attack"
        )
        and isinstance(
            data.get("answer"),
            str,
        )
        and bool(
            data.get("answer", "").strip()
        )
        and data.get("source") is None
    )

    check(
        "Existing query-only API compatibility",
        compatibility_pass,
    )

    # ==============================================================
    # TEST 2 - REQUEST SCHEMA
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 2 - REQUEST SCHEMA")

    fields = set(
        AnalyzeRequest.model_fields.keys()
    )

    print(
        "AnalyzeRequest fields:",
        sorted(fields),
    )

    schema_pass = (
        fields
        == {
            "query",
            "source",
        }
    )

    check(
        "Source-aware request schema",
        schema_pass,
    )

    # ==============================================================
    # TEST 3 - SERVER-A SOURCE
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 3 - SERVER-A SOURCE")

    response = client.post(
        "/analyze",
        json={
            "query": (
                "failed SSH authentication "
                "brute force attack"
            ),
            "source": "server-a",
        },
    )

    print(
        "HTTP status:",
        response.status_code,
    )

    data = response.json()

    print(
        "Returned source:",
        data.get("source"),
    )

    server_a_pass = (
        response.status_code == 200
        and data.get("source")
        == "server-a"
        and isinstance(
            data.get("answer"),
            str,
        )
        and bool(
            data.get("answer", "").strip()
        )
    )

    check(
        "Server-A source request",
        server_a_pass,
    )

    # ==============================================================
    # TEST 4 - SERVER-B SOURCE
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 4 - SERVER-B SOURCE")

    response = client.post(
        "/analyze",
        json={
            "query": (
                "suspicious sudo "
                "privilege escalation activity"
            ),
            "source": "server-b",
        },
    )

    print(
        "HTTP status:",
        response.status_code,
    )

    data = response.json()

    print(
        "Returned source:",
        data.get("source"),
    )

    server_b_pass = (
        response.status_code == 200
        and data.get("source")
        == "server-b"
        and isinstance(
            data.get("answer"),
            str,
        )
        and bool(
            data.get("answer", "").strip()
        )
    )

    check(
        "Server-B source request",
        server_b_pass,
    )

    # ==============================================================
    # TEST 5 - SERVER-C SOURCE
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 5 - SERVER-C SOURCE")

    response = client.post(
        "/analyze",
        json={
            "query": (
                "network scanning "
                "suspicious connections"
            ),
            "source": "server-c",
        },
    )

    print(
        "HTTP status:",
        response.status_code,
    )

    data = response.json()

    print(
        "Returned source:",
        data.get("source"),
    )

    server_c_pass = (
        response.status_code == 200
        and data.get("source")
        == "server-c"
        and isinstance(
            data.get("answer"),
            str,
        )
        and bool(
            data.get("answer", "").strip()
        )
    )

    check(
        "Server-C source request",
        server_c_pass,
    )

    # ==============================================================
    # TEST 6 - EMPTY SOURCE
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 6 - EMPTY SOURCE VALIDATION")

    response = client.post(
        "/analyze",
        json={
            "query": (
                "failed SSH authentication"
            ),
            "source": "   ",
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

    empty_source_pass = (
        response.status_code == 400
    )

    check(
        "Empty source validation",
        empty_source_pass,
    )

    # ==============================================================
    # TEST 7 - SOURCE ISOLATION AT API LEVEL
    # ==============================================================

    print()
    print("-" * 70)
    print("TEST 7 - SOURCE ISOLATION")

    requests_to_test = [
        (
            "server-a",
            "failed SSH authentication",
        ),
        (
            "server-b",
            "sudo privilege escalation",
        ),
        (
            "server-c",
            "network scanning",
        ),
    ]

    source_results = []

    for source, query in requests_to_test:

        response = client.post(
            "/analyze",
            json={
                "query": query,
                "source": source,
            },
        )

        returned_source = (
            response.json().get(
                "source"
            )
            if response.status_code == 200
            else None
        )

        source_results.append(
            returned_source
        )

        print(
            f"{source}: "
            f"returned={returned_source}"
        )

    source_isolation_pass = (
        source_results
        == [
            "server-a",
            "server-b",
            "server-c",
        ]
    )

    check(
        "API source isolation",
        source_isolation_pass,
    )

    # ==============================================================
    # RESULTS
    # ==============================================================

    print()
    print("=" * 70)
    print("SOURCE-AWARE API RESULTS")
    print("=" * 70)

    print(
        f"Tests passed: "
        f"{passed}/7"
    )

    print(
        f"Tests failed: "
        f"{failed}"
    )

    if failed != 0:

        raise AssertionError(
            "Source-aware API evaluation failed."
        )

    print()
    print(
        "Backwards compatibility: PASS"
    )

    print(
        "Source-aware request schema: PASS"
    )

    print(
        "Server-A support: PASS"
    )

    print(
        "Server-B support: PASS"
    )

    print(
        "Server-C support: PASS"
    )

    print(
        "Source validation: PASS"
    )

    print(
        "API source isolation: PASS"
    )

    print()
    print("=" * 70)
    print(
        "SOURCE-AWARE API EVALUATION PASSED"
    )
    print("=" * 70)


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    main()