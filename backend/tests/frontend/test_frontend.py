"""
test_frontend.py

Tests the Phase 19 frontend files and API integration.
"""

from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT.parent / "frontend"


def test_frontend_files_exist():
    """Verify all required frontend files exist."""

    required_files = [
        "index.html",
        "style.css",
        "script.js",
    ]

    for filename in required_files:
        path = FRONTEND_DIR / filename

        assert path.exists(), (
            f"Missing frontend file: {filename}"
        )

    print("Frontend Files: PASS")


def test_html_structure():
    """Verify the main HTML elements exist."""

    html = (
        FRONTEND_DIR / "index.html"
    ).read_text(
        encoding="utf-8"
    )

    required_elements = [
        "<html",
        "<head",
        "<body",
        'id="query"',
        'id="analyze-button"',
        'id="result"',
        'id="status"',
    ]

    for element in required_elements:
        assert element in html, (
            f"Missing HTML element: {element}"
        )

    print("HTML Structure: PASS")


def test_css_exists():
    """Verify CSS contains styling rules."""

    css = (
        FRONTEND_DIR / "style.css"
    ).read_text(
        encoding="utf-8"
    )

    assert len(css.strip()) > 0
    assert "body" in css

    print("CSS: PASS")


def test_javascript_api_configuration():
    """Verify JavaScript contains the API configuration."""

    javascript = (
        FRONTEND_DIR / "script.js"
    ).read_text(
        encoding="utf-8"
    )

    assert "API_URL" in javascript

    assert (
        "http://127.0.0.1:8001"
        in javascript
    )

    print("JavaScript API Configuration: PASS")


def test_javascript_analyze_function():
    """Verify the frontend contains the analysis logic."""

    javascript = (
        FRONTEND_DIR / "script.js"
    ).read_text(
        encoding="utf-8"
    )

    required_content = [
        "analyzeSecurity",
        "fetch",
        "/analyze",
        "POST",
        "Content-Type",
        "application/json",
        "query",
        "data.answer",
    ]

    for item in required_content:
        assert item in javascript, (
            f"Missing JavaScript component: {item}"
        )

    print("JavaScript Analyze Function: PASS")


def test_javascript_error_handling():
    """Verify frontend handles API errors."""

    javascript = (
        FRONTEND_DIR / "script.js"
    ).read_text(
        encoding="utf-8"
    )

    assert "try" in javascript
    assert "catch" in javascript
    assert "Analysis failed." in javascript

    print("JavaScript Error Handling: PASS")


def test_javascript_button_handler():
    """Verify the Analyse button triggers analysis."""

    javascript = (
        FRONTEND_DIR / "script.js"
    ).read_text(
        encoding="utf-8"
    )

    assert "addEventListener" in javascript
    assert "analyzeSecurity" in javascript

    print("Button Event Handler: PASS")


if __name__ == "__main__":

    print("=" * 60)
    print("PHASE 19 FRONTEND TEST")
    print("=" * 60)

    test_frontend_files_exist()
    test_html_structure()
    test_css_exists()
    test_javascript_api_configuration()
    test_javascript_analyze_function()
    test_javascript_error_handling()
    test_javascript_button_handler()

    print("=" * 60)
    print("PHASE 19 FRONTEND TEST PASSED")
    print("=" * 60)