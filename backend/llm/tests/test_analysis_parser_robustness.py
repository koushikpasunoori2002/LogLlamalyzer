"""
test_analysis_parser_robustness.py

Tests AnalysisParser against multiple LLM response formats.

"""

from pathlib import Path
import sys


# --------------------------------------------------------------
# Project Root
# --------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# --------------------------------------------------------------
# Imports
# --------------------------------------------------------------

from backend.llm.analysis import (
    AnalysisParser,
    SecurityAnalysis,
)

from backend.llm.generation import LLMResponse


# --------------------------------------------------------------
# Test Helper
# --------------------------------------------------------------

def create_response(answer):

    return LLMResponse(
        query="failed SSH authentication",
        answer=answer,
        model="llama3.1:8b",
        metadata={
            "source": "test",
        },
    )


# --------------------------------------------------------------
# Test 1
# --------------------------------------------------------------

def test_numbered_format(parser):

    answer = """
**THREAT ASSESSMENT**

The evidence indicates a potential security threat: YES

**EVIDENCE**

1. Failed password for root from 192.168.1.20.
2. Failed password for admin from 192.168.1.30.
3. Both attempts targeted SSH port 22.

**SECURITY INTERPRETATION**

The repeated failed authentication attempts may indicate
a brute-force attack.

**SEVERITY**

Estimated severity: HIGH

**RECOMMENDED ACTIONS**

1. Investigate the source IP addresses.
2. Review SSH authentication controls.
3. Monitor for further failed attempts.

**LIMITATIONS**

The evidence does not confirm a successful compromise.
"""

    analysis = parser.parse(
        create_response(answer)
    )

    assert isinstance(
        analysis,
        SecurityAnalysis,
    )

    assert len(
        analysis.evidence
    ) == 3

    assert len(
        analysis.recommended_actions
    ) == 3

    assert analysis.severity == "HIGH"

    print(
        "Numbered Format: PASS"
    )


# --------------------------------------------------------------
# Test 2
# --------------------------------------------------------------

def test_bullet_format(parser):

    answer = """
THREAT ASSESSMENT

Potential security threat detected.

EVIDENCE

- Failed SSH password for root.
- Failed SSH password for admin.
- Both attempts targeted port 22.

SECURITY INTERPRETATION

The activity may indicate brute-force authentication attempts.

SEVERITY

MEDIUM

RECOMMENDED ACTIONS

- Investigate source addresses.
- Review SSH configuration.
- Monitor authentication logs.

LIMITATIONS

The evidence does not prove successful compromise.
"""

    analysis = parser.parse(
        create_response(answer)
    )

    assert len(
        analysis.evidence
    ) == 3

    assert len(
        analysis.recommended_actions
    ) == 3

    assert analysis.severity == "MEDIUM"

    print(
        "Bullet Format: PASS"
    )


# --------------------------------------------------------------
# Test 3
# --------------------------------------------------------------

def test_markdown_heading_format(parser):

    answer = """
## THREAT ASSESSMENT

Yes, the evidence indicates a potential threat.

## EVIDENCE

1. Failed SSH authentication.
2. Root account targeted.
3. SSH port 22 was targeted.

## SECURITY INTERPRETATION

The activity may represent brute-force authentication.

## SEVERITY

**CRITICAL**

## RECOMMENDED ACTIONS

1. Investigate the source.
2. Review SSH controls.

## LIMITATIONS

No successful login is shown in the evidence.
"""

    analysis = parser.parse(
        create_response(answer)
    )

    assert len(
        analysis.evidence
    ) == 3

    assert len(
        analysis.recommended_actions
    ) == 2

    assert analysis.severity == "CRITICAL"

    print(
        "Markdown Heading Format: PASS"
    )


# --------------------------------------------------------------
# Test 4
# --------------------------------------------------------------

def test_note_limitation(parser):

    answer = """
**THREAT ASSESSMENT**

Potential security threat detected.

**EVIDENCE**

1. Failed SSH authentication was observed.
2. The root account was targeted.

**SECURITY INTERPRETATION**

This may indicate an authentication attack.

**SEVERITY**

HIGH

**RECOMMENDED ACTIONS**

1. Investigate the source.
2. Monitor future attempts.

Note: The available evidence does not confirm
a successful compromise.
"""

    analysis = parser.parse(
        create_response(answer)
    )

    assert analysis.severity == "HIGH"

    assert (
        "successful compromise"
        in analysis.limitations
    )

    print(
        "Note Limitation: PASS"
    )


# --------------------------------------------------------------
# Test 5
# --------------------------------------------------------------

def test_multiline_items(parser):

    answer = """
THREAT ASSESSMENT

Potential security threat detected.

EVIDENCE

1. Failed password for root from 192.168.1.20
   on SSH port 22.
2. Failed password for admin from 192.168.1.30
   on SSH port 22.

SECURITY INTERPRETATION

Repeated failed authentication attempts may indicate
brute-force activity.

SEVERITY

HIGH

RECOMMENDED ACTIONS

1. Investigate the source IP addresses and determine
   whether they are legitimate.
2. Review SSH configuration and authentication controls.

LIMITATIONS

The evidence does not demonstrate a successful login.
"""

    analysis = parser.parse(
        create_response(answer)
    )

    assert len(
        analysis.evidence
    ) == 2

    assert len(
        analysis.recommended_actions
    ) == 2

    assert (
        "192.168.1.20"
        in analysis.evidence[0]
    )

    assert (
        "legitimate"
        in analysis.recommended_actions[0]
    )

    print(
        "Multiline Items: PASS"
    )


# --------------------------------------------------------------
# Main
# --------------------------------------------------------------

def main():

    print("=" * 70)
    print("ANALYSIS PARSER ROBUSTNESS TEST")
    print("=" * 70)

    parser = AnalysisParser()

    print(
        "\nParser Information"
    )

    print(
        parser.info()
    )

    print(
        "\nRunning parser format tests..."
    )

    test_numbered_format(
        parser
    )

    test_bullet_format(
        parser
    )

    test_markdown_heading_format(
        parser
    )

    test_note_limitation(
        parser
    )

    test_multiline_items(
        parser
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "ANALYSIS PARSER ROBUSTNESS TEST PASSED"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()