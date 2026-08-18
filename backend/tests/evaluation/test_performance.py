"""
Performance evaluation tests.
"""

import time

from fastapi.testclient import TestClient

from backend.api.app import app


client = TestClient(app)


QUERIES = [
    "failed SSH authentication brute force attack",
    "suspicious sudo privilege escalation activity",
    "possible malware execution detected in system logs",
    "possible network scanning and suspicious connection attempts",
    "repeated failed login attempts",
]


def measure_query(query):
    start_time = time.perf_counter()

    response = client.post(
        "/analyze",
        json={"query": query},
    )

    end_time = time.perf_counter()

    elapsed = end_time - start_time

    return response, elapsed


def test_performance_queries():

    timings = []

    for query in QUERIES:

        response, elapsed = measure_query(query)

        assert response.status_code == 200

        data = response.json()

        assert "query" in data
        assert "answer" in data
        assert isinstance(data["answer"], str)
        assert data["answer"].strip()

        timings.append(elapsed)

    assert len(timings) == len(QUERIES)


def test_performance_success_rate():

    successful = 0

    for query in QUERIES:

        response, _ = measure_query(query)

        if response.status_code == 200:
            successful += 1

    success_rate = successful / len(QUERIES)

    assert success_rate == 1.0


if __name__ == "__main__":

    print("=" * 60)
    print("PERFORMANCE EVALUATION")
    print("=" * 60)

    timings = []
    successful = 0

    for query in QUERIES:

        response, elapsed = measure_query(query)

        timings.append(elapsed)

        if response.status_code == 200:
            successful += 1
            print(
                f"PASS: {query}"
            )
            print(
                f"Response Time: {elapsed:.2f} seconds"
            )
        else:
            print(
                f"FAIL: {query}"
            )

    average_time = sum(timings) / len(timings)
    minimum_time = min(timings)
    maximum_time = max(timings)
    success_rate = (
        successful / len(QUERIES)
    ) * 100

    print("=" * 60)
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
    print("=" * 60)

    if successful == len(QUERIES):
        print("PERFORMANCE EVALUATION PASSED")
    else:
        print("PERFORMANCE EVALUATION FAILED")

    print("=" * 60)
