"""
app.py

Main FastAPI application for LogLlamalyzer.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router as status_router
from backend.api.endpoints import router as analysis_router


app = FastAPI(
    title="LogLlamalyzer API",
    description="API for LLM-based security log analysis.",
    version="1.0.0",
)


# ----------------------------------------------------------
# CORS Configuration
# ----------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8001",
        "http://localhost:8001",
        "null",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------------------------
# Routers
# ----------------------------------------------------------

app.include_router(status_router)
app.include_router(analysis_router)


# ----------------------------------------------------------
# Root Endpoint
# ----------------------------------------------------------

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


# ----------------------------------------------------------
# Health Endpoint
# ----------------------------------------------------------

@app.get("/health")
def health():
    """
    API health check.
    """

    return {
        "status": "healthy",
    }