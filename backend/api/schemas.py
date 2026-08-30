"""
schemas.py

Pydantic request and response models for the LogLlamalyzer API.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """
    Request model for security analysis.

    The source field is optional so existing clients that send
    only a query remain compatible.
    """

    query: str

    source: Optional[str] = None


class AnalyzeMetadata(BaseModel):
    """
    Metadata describing the evidence used during analysis.
    """

    sources: List[str] = Field(
        default_factory=list
    )

    log_results: int = 0

    knowledge_results: int = 0


class AnalyzeResponse(BaseModel):
    """
    Response model returned by the analysis endpoint.
    """

    query: str

    answer: str

    source: Optional[str] = None

    metadata: AnalyzeMetadata = Field(
        default_factory=AnalyzeMetadata
    )