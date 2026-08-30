"""
Performance evaluation tests.

Measures the performance and reliability of the LogLlamalyzer
analysis API across representative security-related queries.

The evaluation covers:
- API response time
- successful request rate
- average response time
- minimum response time
- maximum response time
"""

from pathlib import Path
import sys
import time


# ------------------------------------------------------------------
# Project path
# ------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------

from fastapi.testclient import TestClient

from backend.api.app import app


# ------------------------------------------------------------------
# Test client
# ------------------------------------------------------------------

client = TestClient(app)


# ------------------------------------------------------------------
# Performance queries
# ------------------------------------------------------------------

QUERIES = [
    "failed SSH authentication brute force attack",
    "suspicious sudo privilege escalation activity",
    "possible malware execution detected in system logs",
    "possible network scanning and suspicious connection attempts",
    "repeated failed login attempts",
]


# ------------------------------------------------------------------
# Measure one API query
# ------------------------------------------------------------------

def measure_query(query):
    """
    Send one analysis request and measure its response time.

    Parameters
    ----------
    query : str
        Security-analysis query.

    Returns
    -------
    tuple
        API response and elapsed time in seconds.
    """

    start_time = time.perf_counter()

    response = client.post(
        "/analyze",
        json={
            "query": query
        },
    )

    end_time = time.perf_counter()

    elapsed = (
        end_time - start_time
    )

    return response, elapsed


# ------------------------------------------------------------------
# Pytest performance test
# ------------------------------------------------------------------

def test_performance_queries():
    """
    Verify that all representative analysis queries
    complete successfully.
    """

    timings = []

    for query in QUERIES:

        response, elapsed = measure_query(
            query
        )

        assert response.status_code == 200

        data = response.json()

        assert "query" in data
        assert "answer" in data

        assert isinstance(
            data["answer"],
            str,
        )

        assert data["answer"].strip()

        timings.append(elapsed)

    assert len(timings) == len(
        QUERIES
    )


# ------------------------------------------------------------------
# Pytest success-rate test
# ------------------------------------------------------------------

def test_performance_success_rate():
    """
    Verify that every performance query
    receives a successful API response.
    """

    successful = 0

    for query in QUERIES:

        response, _ = measure_query(
            query
        )

        if response.status_code == 200:
            successful += 1

    success_rate = (
        successful / len(QUERIES)
    )

    assert success_rate == 1.0


# ------------------------------------------------------------------
# Standalone evaluation
# ------------------------------------------------------------------

if __name__ == "__main__":

    print("=" * 70)
    print("PERFORMANCE EVALUATION")
    print("=" * 70)

    print(
        f"\nProject Root: {PROJECT_ROOT}"
    )

    print(
        f"Queries Evaluated: {len(QUERIES)}"
    )

    print("-" * 70)

    timings = []

    successful = 0

    # --------------------------------------------------------------
    # Execute performance queries
    # --------------------------------------------------------------

    for index, query in enumerate(
        QUERIES,
        start=1,
    ):

        print(
            f"\nQUERY {index}/{len(QUERIES)}"
        )

        print(
            f"Query: {query}"
        )

        response, elapsed = measure_query(
            query
        )

        timings.append(elapsed)

        if response.status_code == 200:

            successful += 1

            print(
                "Status: PASS"
            )

            print(
                f"Response Time: "
                f"{elapsed:.2f} seconds"
            )

            try:

                data = response.json()

                answer = data.get(
                    "answer",
                    "",
                )

                print(
                    "Answer Generated: "
                    f"{bool(answer.strip())}"
                )

            except Exception:

                print(
                    "Answer Generated: "
                    "UNKNOWN"
                )

        else:

            print(
                "Status: FAIL"
            )

            print(
                f"HTTP Status: "
                f"{response.status_code}"
            )

            print(
                f"Response Time: "
                f"{elapsed:.2f} seconds"
            )

            try:

                print(
                    "Response:",
                    response.text,
                )

            except Exception:

                pass

    # --------------------------------------------------------------
    # Calculate performance statistics
    # --------------------------------------------------------------

    if not timings:

        print(
            "\nNo performance timings were recorded."
        )

        raise SystemExit(1)

    average_time = (
        sum(timings)
        / len(timings)
    )

    minimum_time = min(
        timings
    )

    maximum_time = max(
        timings
    )

    success_rate = (
        successful
        / len(QUERIES)
    ) * 100

    # --------------------------------------------------------------
    # Results
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("PERFORMANCE RESULTS")
    print("=" * 70)

    print(
        f"Successful Requests: "
        f"{successful}/{len(QUERIES)}"
    )

    print(
        f"Success Rate: "
        f"{success_rate:.1f}%"
    )

    print(
        f"Average Response Time: "
        f"{average_time:.2f} seconds"
    )

    print(
        f"Minimum Response Time: "
        f"{minimum_time:.2f} seconds"
    )

    print(
        f"Maximum Response Time: "
        f"{maximum_time:.2f} seconds"
    )

    # --------------------------------------------------------------
    # Per-query timing summary
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("PER-QUERY RESPONSE TIMES")
    print("-" * 70)

    for index, (
        query,
        elapsed,
    ) in enumerate(
        zip(
            QUERIES,
            timings,
        ),
        start=1,
    ):

        print(
            f"{index}. "
            f"{elapsed:.2f}s - "
            f"{query}"
        )

    # --------------------------------------------------------------
    # Final validation
    # --------------------------------------------------------------

    print("\n" + "=" * 70)

    if successful == len(QUERIES):

        print(
            "PERFORMANCE EVALUATION PASSED"
        )

        print(
            "All API requests completed successfully."
        )

        print(
            "This result establishes the current "
            "performance baseline."
        )

    else:

        print(
            "PERFORMANCE EVALUATION FAILED"
        )

        print(
            f"{len(QUERIES) - successful} "
            "request(s) failed."
        )

        print(
            "Performance baseline could not be "
            "established successfully."
        )

    print("=" * 70)

    # --------------------------------------------------------------
    # Exit status
    # --------------------------------------------------------------

    if successful != len(QUERIES):

        raise SystemExit(1)