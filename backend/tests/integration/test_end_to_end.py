"""
test_end_to_end.py

End-to-end integration tests for LogLlamalyzer.

Tests the complete flow from the API request through
the RAG + LLM analysis pipeline.
"""

from fastapi.testclient import TestClient

from backend.api.app import app


client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["application"] == "LogLlamalyzer"
    assert data["status"] == "running"


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"


def test_status_endpoint():
    response = client.get("/status")

    assert response.status_code == 200

    data = response.json()

    assert data["application"] == "LogLlamalyzer"
    assert data["status"] == "operational"


def test_analyze_end_to_end():
    """
    Test the complete frontend/API/RAG/LLM analysis path
    through the FastAPI application.
    """

    response = client.post(
        "/analyze",
        json={
            "query": "failed SSH authentication brute force attack"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "query" in data
    assert "answer" in data

    assert (
        data["query"]
        == "failed SSH authentication brute force attack"
    )

    assert isinstance(data["answer"], str)
    assert len(data["answer"].strip()) > 0


def test_empty_query_rejected():
    response = client.post(
        "/analyze",
        json={
            "query": ""
        },
    )

    assert response.status_code in [400, 422]


def test_missing_query_rejected():
    response = client.post(
        "/analyze",
        json={}
    )

    assert response.status_code == 422


def test_invalid_method():
    response = client.get("/analyze")

    assert response.status_code == 405


if __name__ == "__main__":

    print("=" * 60)
    print("PHASE 20 END-TO-END INTEGRATION TEST")
    print("=" * 60)

    test_root_endpoint()
    print("Root Endpoint: PASS")

    test_health_endpoint()
    print("Health Endpoint: PASS")

    test_status_endpoint()
    print("Status Endpoint: PASS")

    test_analyze_end_to_end()
    print("End-to-End Analyze Pipeline: PASS")

    test_empty_query_rejected()
    print("Empty Query Rejection: PASS")

    test_missing_query_rejected()
    print("Missing Query Rejection: PASS")

    test_invalid_method()
    print("Invalid Method: PASS")

    print("=" * 60)
    print("PHASE 20 END-TO-END TEST PASSED")
    print("=" * 60)