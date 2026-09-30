import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.upload import router as upload_router
from app.api.chat import router as chat_router

# Configure logging format and levels
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG PDF Chatbot API",
    description="A complete production-ready backend API for PDF Question Answering using LangChain, ChromaDB, and Grok API.",
    version="1.0.0"
)

# Setup CORS middleware to enable API usage from different hosts/ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register endpoints (upload, chat, clear, health are registered directly on root path)
app.include_router(upload_router)
app.include_router(chat_router)

# Resolve path for static frontend assets
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
frontend_dir = os.path.join(base_dir, "frontend")

if os.path.exists(frontend_dir):
    logger.info(f"Serving frontend static files from: {frontend_dir}")
    # Mount static assets at root, falls back to index.html
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    logger.warning(f"Frontend directory not found at: {frontend_dir}. Static file serving is disabled.")
