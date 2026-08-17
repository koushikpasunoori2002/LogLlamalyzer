"""
test_analyze_endpoint.py

Tests the /analyze API endpoint.
"""

from fastapi.testclient import TestClient

from backend.api.app import app


client = TestClient(app)


def test_valid_analyze_request():
    response = client.post(
        "/analyze",
        json={
            "query": "failed SSH authentication"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "query" in data
    assert "answer" in data
    assert data["query"] == "failed SSH authentication"

    print("Valid Analyze Request: PASS")


def test_empty_query():
    response = client.post(
        "/analyze",
        json={
            "query": ""
        },
    )

    assert response.status_code in [400, 422]

    print("Empty Query Validation: PASS")


def test_missing_query():
    response = client.post(
        "/analyze",
        json={}
    )

    assert response.status_code in [400, 422]

    print("Missing Query Validation: PASS")


def test_invalid_method():
    response = client.get("/analyze")

    assert response.status_code == 405

    print("Invalid Method: PASS")


def test_response_structure():
    response = client.post(
        "/analyze",
        json={
            "query": "failed SSH authentication"
        },
    )

    assert response.status_code == 200

    data = response.json()

    required_fields = [
        "query",
        "answer",
    ]

    for field in required_fields:
        assert field in data

    assert isinstance(data["query"], str)
    assert isinstance(data["answer"], str)
    assert len(data["answer"]) > 0

    print("Response Structure: PASS")


if __name__ == "__main__":

    print("=" * 60)
    print("PHASE 18 ANALYZE ENDPOINT TEST")
    print("=" * 60)

    test_valid_analyze_request()
    test_empty_query()
    test_missing_query()
    test_invalid_method()
    test_response_structure()

    print("=" * 60)
    print("PHASE 18 ANALYZE ENDPOINT TEST PASSED")
    print("=" * 60)