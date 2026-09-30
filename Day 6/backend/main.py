"""
main.py
-------
Healthcare AI Clinical Assistant — FastAPI Application Entry Point.

Run with:
    uvicorn backend.main:app --reload

The frontend is served as a static SPA from frontend/index.html.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.routes import symptom, medical_term, prescription, health_tips, report_summary, emergency

# ---------------------------------------------------------------------------
# App initialisation
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Healthcare AI Clinical Assistant",
    description=(
        "An AI-powered educational healthcare assistant that helps users understand "
        "symptoms, medications, medical reports, and healthy lifestyle recommendations. "
        "Powered by the Grok API. This tool is NOT a substitute for professional medical advice."
    ),
    version="1.0.0",
    contact={
        "name": "Healthcare AI Team",
        "email": "support@healthcareai.example.com",
    },
    license_info={
        "name": "MIT License",
    },
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — Allow the frontend (file:// or any local dev server) to call the API
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Frontend served from file:// in dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Route registration — all routes under /api prefix
# ---------------------------------------------------------------------------

app.include_router(symptom.router,       prefix="/api", tags=["Symptom Analyzer"])
app.include_router(medical_term.router,  prefix="/api", tags=["Medical Term Explainer"])
app.include_router(prescription.router,  prefix="/api", tags=["Prescription Explainer"])
app.include_router(health_tips.router,   prefix="/api", tags=["Health Tips Generator"])
app.include_router(report_summary.router, prefix="/api", tags=["Medical Report Summarizer"])
app.include_router(emergency.router,     prefix="/api", tags=["Emergency Checker"])

# ---------------------------------------------------------------------------
# Health check endpoint
# ---------------------------------------------------------------------------

@app.get("/api/health", tags=["Status"])
async def health_check() -> JSONResponse:
    """
    Simple health check endpoint.

    Returns:
        JSON with status 'ok' and basic API information.
    """
    api_key_configured = bool(os.getenv("GROK_API_KEY", "").strip())
    return JSONResponse(content={
        "status": "ok",
        "service": "Healthcare AI Clinical Assistant",
        "version": "1.0.0",
        "api_key_configured": api_key_configured,
        "disclaimer": (
            "This AI assistant is for educational purposes only and is not a substitute "
            "for professional medical advice, diagnosis, or treatment."
        ),
    })


# ---------------------------------------------------------------------------
# Root redirect info
# ---------------------------------------------------------------------------

@app.get("/", tags=["Root"])
async def root() -> JSONResponse:
    """Root endpoint — directs users to API docs or the frontend."""
    return JSONResponse(content={
        "message": "Healthcare AI Clinical Assistant API is running.",
        "docs": "/docs",
        "health": "/api/health",
        "frontend": "Open frontend/index.html in your browser.",
    })
