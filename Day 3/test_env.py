import os
import sys

# Insert backend directory at the beginning of the Python search path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

try:
    print("=== Testing environment loader ===")
    from app.core.config import settings
    print(f"Base Directory: {settings.BASE_DIR}")
    print(f"Upload Directory: {settings.UPLOAD_DIR}")
    print(f"Vectorstore Directory: {settings.VECTORSTORE_DIR}")
    
    print("\n=== Testing embedding service ===")
    from app.services.embedding_service import get_embeddings
    print("Embedding service loaded successfully.")

    print("\n=== Testing PDF loader ===")
    from app.services.pdf_loader import load_and_split_pdf
    print("PDF loader service loaded successfully.")
    
    print("\n=== Testing RAG coordinator ===")
    from app.services.rag_service import query_rag
    print("RAG service loaded successfully.")
    
    print("\n=== Testing FastAPI application ===")
    from app.main import app
    print("FastAPI routes loaded successfully:")
    for route in app.routes:
        path = getattr(route, "path", None)
        if path is None and hasattr(route, "routes"):
            for sub_route in route.routes:
                print(f"  Route: {getattr(sub_route, 'path', '')}")
        else:
            print(f"  Route: {path}")
            
    print("\nVerification Check Passed: Environment is ready!")
except Exception as e:
    print(f"Verification Check Failed: {e}")
    sys.exit(1)
