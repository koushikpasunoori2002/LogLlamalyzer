"""
routes.py

Basic API routes for LogLlamalyzer.
"""

from fastapi import APIRouter


router = APIRouter()


@router.get("/status")
def status():
    """
    Return the current API status.
    """

    return {
        "application": "LogLlamalyzer",
        "status": "operational",
    }