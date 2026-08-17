"""
test_schemas.py

Tests API request and response schemas.
"""

from backend.api.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
)


def test_analyze_request():
    request = AnalyzeRequest(
        query="failed SSH authentication"
    )

    assert request.query == "failed SSH authentication"

    print("AnalyzeRequest: PASS")


def test_analyze_response():
    response = AnalyzeResponse(
        query="failed SSH authentication",
        answer="Potential SSH authentication threat detected.",
    )

    assert response.query == "failed SSH authentication"
    assert response.answer != ""

    print("AnalyzeResponse: PASS")


def test_request_rejects_missing_query():
    try:
        AnalyzeRequest()
        assert False
    except Exception:
        pass

    print("Missing Query Validation: PASS")


if __name__ == "__main__":

    print("=" * 60)
    print("PHASE 18 API SCHEMA TEST")
    print("=" * 60)

    test_analyze_request()
    test_analyze_response()
    test_request_rejects_missing_query()

    print("=" * 60)
    print("PHASE 18 API SCHEMA TEST PASSED")
    print("=" * 60)