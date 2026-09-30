import os
import shutil
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.services.pdf_loader import load_and_split_pdf
from app.services.chroma_service import create_vectorstore

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Endpoint to upload a PDF file, process it, extract text, split it into chunks,
    compute embeddings, and store them in ChromaDB.
    Clears any previous uploaded files and vector collections.
    """
    logger.info(f"Received file upload request for file: {file.filename}")
    
    # Validation 1: Check if file is provided
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file selected for upload."
        )
        
    # Validation 2: Check extension
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF files are allowed."
        )
        
    # Generate path to save the PDF
    upload_dir = settings.UPLOAD_DIR
    temp_file_path = os.path.join(upload_dir, file.filename)
    
    try:
        # Save uploaded file to disk
        logger.info(f"Saving uploaded file to: {temp_file_path}")
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Validation 3: Check file size
        if os.path.getsize(temp_file_path) == 0:
            raise ValueError("The uploaded PDF file is empty.")
            
        # Parse PDF and split text using text splitter
        logger.info("Parsing PDF and splitting text into chunks...")
        chunks = load_and_split_pdf(temp_file_path)
        
        if not chunks:
            raise ValueError("No text content could be extracted from the PDF. The file may be empty, image-only, or password-protected.")
            
        # Store in ChromaDB (automatically clears previous database internally)
        logger.info("Generating embeddings and writing to ChromaDB...")
        create_vectorstore(chunks)
        
        logger.info(f"Upload and vectorization complete for: {file.filename}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "PDF uploaded and processed successfully.",
                "filename": file.filename,
                "chunks_count": len(chunks),
                "status": "success"
            }
        )
        
    except ValueError as ve:
        logger.error(f"Validation error during PDF processing: {str(ve)}")
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
        
    except Exception as e:
        logger.error(f"Internal error processing PDF: {str(e)}", exc_info=True)
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the PDF: {str(e)}"
        )
