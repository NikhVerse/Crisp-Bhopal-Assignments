import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Import API routes
from backend.routes import router as api_router

app = FastAPI(
    title="AI Resume Analyzer API",
    description="Backend API for parsing, analyzing, and generating reports for resumes using Grok API.",
    version="1.0.0"
)

# Configure CORS to support frontend deployments on other ports or domains (Vercel, Netlify)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify authorized origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router under /api prefix
app.include_router(api_router, prefix="/api")

# Serve the frontend files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "grok_api_configured": bool(os.getenv("GROK_API_KEY"))
    }

# Mount static files for the frontend if directory exists
if os.path.exists(frontend_dir):
    # Serve index.html and static assets from root
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    @app.get("/")
    def read_root():
        return HTMLResponse(
            content="<h3>Backend running successfully!</h3><p>Frontend assets not found in parent directory.</p>",
            status_code=200
        )

if __name__ == "__main__":
    import uvicorn
    # Get port from environment (for Render/Railway) or default to 8000
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
