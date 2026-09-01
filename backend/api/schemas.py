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


class EvidenceItem(BaseModel):
    """
    Represents one retrieved log evidence item.
    """

    timestamp: Optional[str] = None

    hostname: Optional[str] = None

    process: Optional[str] = None

    severity: Optional[str] = None

    event: Optional[str] = None

    event_type: Optional[str] = None

    user: Optional[str] = None

    ip: Optional[str] = None

    port: Optional[int] = None

    protocol: Optional[str] = None

    source_file: Optional[str] = None

    source: Optional[str] = None

    message: str = ""

    distance: Optional[float] = None


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

    evidence: List[EvidenceItem] = Field(
        default_factory=list
    )