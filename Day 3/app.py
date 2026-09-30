import os
import sys

# Ensure backend package can be imported directly without shadowing
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

import uvicorn
from app.main import app

if __name__ == "__main__":
    print("Starting Antigravity PDF Chatbot native launcher...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
