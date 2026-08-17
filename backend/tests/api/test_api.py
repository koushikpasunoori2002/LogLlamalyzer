"""
test_api.py

Tests the FastAPI endpoints for LogLlamalyzer.
"""

from fastapi.testclient import TestClient

from backend.api.app import app


client = TestClient(app)


# ----------------------------------------------------------
# Root Endpoint
# ----------------------------------------------------------

def test_root_endpoint():
    """
    Test the root API endpoint.
    """

    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["application"] == "LogLlamalyzer"
    assert data["status"] == "running"
    assert data["version"] == "1.0.0"


# ----------------------------------------------------------
# Health Endpoint
# ----------------------------------------------------------

def test_health_endpoint():
    """
    Test the API health endpoint.
    """

    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"


# ----------------------------------------------------------
# Status Endpoint
# ----------------------------------------------------------

def test_status_endpoint():
    """
    Test the API status endpoint.
    """

    response = client.get("/status")

    assert response.status_code == 200

    data = response.json()

    assert data["application"] == "LogLlamalyzer"
    assert data["status"] == "operational"


# ----------------------------------------------------------
# Invalid Endpoint
# ----------------------------------------------------------

def test_invalid_endpoint():
    """
    Verify that an unknown endpoint returns 404.
    """

    response = client.get("/invalid-endpoint")

    assert response.status_code == 404


# ----------------------------------------------------------
# API Test Runner
# ----------------------------------------------------------

if __name__ == "__main__":

    print("=" * 60)
    print("PHASE 18 API TEST")
    print("=" * 60)

    test_root_endpoint()
    print("Root Endpoint: PASS")

    test_health_endpoint()
    print("Health Endpoint: PASS")

    test_status_endpoint()
    print("Status Endpoint: PASS")

    test_invalid_endpoint()
    print("Invalid Endpoint: PASS")

    print("=" * 60)
    print("PHASE 18 API TEST PASSED")
    print("=" * 60)