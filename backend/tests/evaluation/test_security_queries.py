"""
Security query evaluation tests.
"""

from fastapi.testclient import TestClient

from backend.api.app import app


client = TestClient(app)


def run_query(query):
    response = client.post(
        "/analyze",
        json={"query": query},
    )

    if response.status_code != 200:
        return False, response

    data = response.json()

    if "query" not in data:
        return False, response

    if "answer" not in data:
        return False, response

    if not isinstance(data["answer"], str):
        return False, response

    if not data["answer"].strip():
        return False, response

    return True, response


def test_failed_ssh_authentication():
    passed, response = run_query(
        "failed SSH authentication brute force attack"
    )

    assert passed
    assert response.status_code == 200


def test_privilege_escalation():
    passed, response = run_query(
        "suspicious sudo privilege escalation activity"
    )

    assert passed
    assert response.status_code == 200


def test_malware_activity():
    passed, response = run_query(
        "possible malware execution detected in system logs"
    )

    assert passed
    assert response.status_code == 200


def test_network_attack():
    passed, response = run_query(
        "possible network scanning and suspicious connection attempts"
    )

    assert passed
    assert response.status_code == 200


def test_multiple_security_queries():
    queries = [
        "failed SSH authentication brute force attack",
        "suspicious sudo privilege escalation activity",
        "possible malware execution detected",
        "possible network scanning attack",
        "repeated failed login attempts",
    ]

    for query in queries:
        passed, response = run_query(query)

        assert passed
        assert response.status_code == 200


if __name__ == "__main__":

    print("=" * 60)
    print("SECURITY QUERY EVALUATION")
    print("=" * 60)

    queries = [
        "failed SSH authentication brute force attack",
        "suspicious sudo privilege escalation activity",
        "possible malware execution detected",
        "possible network scanning attack",
        "repeated failed login attempts",
    ]

    passed_count = 0

    for query in queries:

        passed, response = run_query(query)

        if passed:
            print("PASS:", query)
            passed_count += 1
        else:
            print("FAIL:", query)

    print("=" * 60)
    print(
        f"Evaluation Result: "
        f"{passed_count}/{len(queries)} queries passed"
    )

    if passed_count == len(queries):
        print("SECURITY QUERY EVALUATION PASSED")
    else:
        print("SECURITY QUERY EVALUATION FAILED")

    print("=" * 60)
