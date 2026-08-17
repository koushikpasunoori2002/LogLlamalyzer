"""
schemas.py

Pydantic request and response models for the LogLlamalyzer API.
"""

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    """
    Request model for security analysis.
    """

    query: str


class AnalyzeResponse(BaseModel):
    """
    Response model returned by the analysis endpoint.
    """

    query: str
    answer: str
    