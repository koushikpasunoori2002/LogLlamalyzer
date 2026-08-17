"""
app.py

Main FastAPI application for LogLlamalyzer.
"""

from fastapi import FastAPI

from backend.api.routes import router as status_router
from backend.api.endpoints import router as analysis_router


app = FastAPI(
    title="LogLlamalyzer API",
    description="API for LLM-based security log analysis.",
    version="1.0.0",
)


app.include_router(status_router)
app.include_router(analysis_router)


@app.get("/")
def root():
    """
    Basic API health endpoint.
    """

    return {
        "application": "LogLlamalyzer",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    """
    API health check.
    """

    return {
        "status": "healthy",
    }