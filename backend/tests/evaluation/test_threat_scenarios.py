"""
Threat scenario evaluation tests.
"""

from fastapi.testclient import TestClient

from backend.api.app import app


client = TestClient(app)


SCENARIOS = [
    {
        "name": "SSH Brute Force",
        "query": "failed SSH authentication brute force attack",
        "keywords": [
            "ssh",
            "authentication",
            "brute",
            "attack",
        ],
    },
    {
        "name": "Privilege Escalation",
        "query": "suspicious sudo privilege escalation activity",
        "keywords": [
            "sudo",
            "privilege",
            "escalation",
        ],
    },
    {
        "name": "Malware Activity",
        "query": "possible malware execution detected in system logs",
        "keywords": [
            "malware",
            "execution",
        ],
    },
    {
        "name": "Network Scanning",
        "query": "possible network scanning and suspicious connection attempts",
        "keywords": [
            "network",
            "scanning",
            "connection",
        ],
    },
    {
        "name": "Repeated Login Failures",
        "query": "repeated failed login attempts",
        "keywords": [
            "login",
            "failed",
        ],
    },
]


def analyse_scenario(scenario):
    response = client.post(
        "/analyze",
        json={"query": scenario["query"]},
    )

    if response.status_code != 200:
        return False, response, ""

    data = response.json()

    if "answer" not in data:
        return False, response, ""

    answer = data["answer"]

    if not isinstance(answer, str):
        return False, response, ""

    if not answer.strip():
        return False, response, ""

    answer_lower = answer.lower()

    keyword_matches = sum(
        1
        for keyword in scenario["keywords"]
        if keyword.lower() in answer_lower
    )

    return keyword_matches >= 1, response, answer


def test_ssh_brute_force():
    passed, response, answer = analyse_scenario(
        SCENARIOS[0]
    )

    assert response.status_code == 200
    assert passed
    assert answer.strip()


def test_privilege_escalation():
    passed, response, answer = analyse_scenario(
        SCENARIOS[1]
    )

    assert response.status_code == 200
    assert passed
    assert answer.strip()


def test_malware_activity():
    passed, response, answer = analyse_scenario(
        SCENARIOS[2]
    )

    assert response.status_code == 200
    assert passed
    assert answer.strip()


def test_network_scanning():
    passed, response, answer = analyse_scenario(
        SCENARIOS[3]
    )

    assert response.status_code == 200
    assert passed
    assert answer.strip()


def test_repeated_login_failures():
    passed, response, answer = analyse_scenario(
        SCENARIOS[4]
    )

    assert response.status_code == 200
    assert passed
    assert answer.strip()


if __name__ == "__main__":

    print("=" * 60)
    print("THREAT SCENARIO EVALUATION")
    print("=" * 60)

    passed_count = 0

    for scenario in SCENARIOS:

        passed, response, answer = analyse_scenario(
            scenario
        )

        if passed:
            print(
                f"PASS: {scenario['name']}"
            )
            passed_count += 1
        else:
            print(
                f"FAIL: {scenario['name']}"
            )

    print("=" * 60)

    print(
        f"Evaluation Result: "
        f"{passed_count}/{len(SCENARIOS)} scenarios passed"
    )

    if passed_count == len(SCENARIOS):
        print("THREAT SCENARIO EVALUATION PASSED")
    else:
        print("THREAT SCENARIO EVALUATION FAILED")

    print("=" * 60)
