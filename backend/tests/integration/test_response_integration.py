"""
test_response_integration.py

Validates the security analysis response returned by the API.
"""

from fastapi.testclient import TestClient

from backend.api.app import app


client = TestClient(app)


def test_security_analysis_response():

    response = client.post(
        "/analyze",
        json={
            "query": "failed SSH authentication brute force attack"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)

    assert "query" in data
    assert "answer" in data

    assert data["query"] == (
        "failed SSH authentication brute force attack"
    )

    answer = data["answer"]

    assert isinstance(answer, str)
    assert len(answer.strip()) > 0

    answer_lower = answer.lower()

    relevant_terms = [
        "ssh",
        "authentication",
        "security",
        "threat",
    ]

    matches = [
        term
        for term in relevant_terms
        if term in answer_lower
    ]

    assert len(matches) >= 2


def test_response_is_json():

    response = client.post(
        "/analyze",
        json={
            "query": "failed SSH authentication"
        },
    )

    assert response.status_code == 200

    assert response.headers["content-type"].startswith(
        "application/json"
    )

    data = response.json()

    assert isinstance(data, dict)


if __name__ == "__main__":

    print("=" * 60)
    print("SECURITY RESPONSE INTEGRATION TEST")
    print("=" * 60)

    test_security_analysis_response()
    print("Security Analysis Response: PASS")

    test_response_is_json()
    print("JSON Response: PASS")

    print("=" * 60)
    print("RESPONSE INTEGRATION TEST PASSED")
    print("=" * 60)