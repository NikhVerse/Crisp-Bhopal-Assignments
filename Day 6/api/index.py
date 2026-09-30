# Vercel entry point
import sys
import os

# Add root folder to sys.path so backend module can be imported in Vercel lambda
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
