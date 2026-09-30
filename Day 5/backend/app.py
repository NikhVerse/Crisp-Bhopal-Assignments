import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import engine, Base
from backend.routes import router
from backend.config import settings
from backend.utils import logger

# Initialize database tables on app startup
try:
    logger.info("Initializing SQLite database and tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
except Exception as e:
    logger.error(f"Error creating database tables on startup: {e}")

app = FastAPI(
    title="AI Smart Personal Assistant - Tool Integration",
    description="FastAPI Backend integrating Weather and Google Calendar APIs via AI Agent routing.",
    version="1.0.0",
    debug=settings.DEBUG
)

# Configure CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router
app.include_router(router)

# Mount Frontend static files to serve the Web UI directly from root '/'
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
frontend_dir = os.path.join(parent_dir, "frontend")

if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    logger.info(f"Frontend static files successfully mounted from: {frontend_dir}")
else:
    logger.warning(f"Frontend directory was not found at {frontend_dir}. API will run, but Web UI will not be served.")

# Main block for local direct execution
if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}...")
    uvicorn.run("backend.app:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
