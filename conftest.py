import pytest

from backend.llm.analysis import AnalysisParser


@pytest.fixture
def parser():
    return AnalysisParser()
