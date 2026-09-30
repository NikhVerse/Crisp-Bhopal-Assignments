import os
import sys

# Ensure backend package can be imported directly without shadowing
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from app.services.pdf_loader import load_and_split_pdf
from app.services.chroma_service import clear_vectorstore, get_vectorstore

def get_db_status() -> dict:
    """
    Checks if Chroma database is initialized.
    """
    db = get_vectorstore()
    return {
        "database_exists": db is not None,
        "uploads_dir": os.path.exists("backend/uploads")
    }
