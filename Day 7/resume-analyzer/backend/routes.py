import os
import shutil
import uuid
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, List

from backend.parser import parse_resume
from backend.analyzer import ResumeAnalyzer
from backend.reporter import generate_pdf_report

router = APIRouter()
analyzer = ResumeAnalyzer()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Pydantic models for request bodies
class AnalyzeRequest(BaseModel):
    text: str
    contact_info: Dict[str, str]

class ReportRequest(BaseModel):
    ats_score: int
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    missing_keywords: List[str]
    grammar: List[str]
    recommendations: List[str]
    formatting_suggestions: List[str] = []
    career_suggestions: List[str] = []
    interview_readiness: str = ""
    readability_score: int = 70
    interview_probability: int = 50
    contact_info: Dict[str, str] = {}

def delete_file_after_delay(file_path: str):
    """Utility task to cleanup files after serving them."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Cleaned up file: {file_path}")
    except Exception as e:
        print(f"Error cleaning up file {file_path}: {e}")

@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    """
    Uploads a resume PDF, validates size & format, and extracts structured text.
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    # Save file temporarily to read its size and parse it
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    temp_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        # Read stream in chunks to enforce 10MB limit
        max_size = 10 * 1024 * 1024  # 10MB
        total_size = 0
        
        with open(temp_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024 * 64)  # Read 64KB chunks
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > max_size:
                    raise HTTPException(status_code=400, detail="File size exceeds the 10MB limit.")
                buffer.write(chunk)
                
        # Parse PDF text and structures
        parsed_data = parse_resume(temp_path)
        parsed_data["file_id"] = unique_filename
        
        return parsed_data
        
    except HTTPException:
        # Re-raise size or format HTTP exceptions
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

@router.post("/analyze")
async def analyze_resume(request: AnalyzeRequest):
    """
    Takes extracted text & parsed fields, runs them through the Grok API,
    and returns the comprehensive ATS analysis report.
    """
    try:
        # Reconstruct structured details for the analyzer
        parsed_data = {
            "text": request.text,
            "contact_info": request.contact_info,
            "sections": {}  # Can pass empty since text contains the whole document
        }
        
        # We can simulate saving a temp text or direct query.
        # Let's run analyzer orchestrator
        # We need a dummy path or modify analyzer to work directly with text.
        # Since ResumeAnalyzer works with a pdf_path, we can write a quick utility or 
        # modify analyzer to accept text directly.
        # Let's call the Grok integration directly from here to make it fast!
        from backend.grok import analyze_resume_text_with_grok
        
        try:
            report = await analyze_resume_text_with_grok(request.text, request.contact_info)
            report["is_fallback"] = False
        except Exception as e:
            # Fallback locally if Grok fails or isn't key-configured
            print(f"Grok evaluation failed: {e}. Running fallback analysis.")
            report = ResumeAnalyzer.get_fallback_analysis(parsed_data)
            report["is_fallback"] = True
            report["error_detail"] = str(e)
            
        report["contact_info"] = request.contact_info
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/report")
async def download_report(request: ReportRequest, background_tasks: BackgroundTasks):
    """
    Generates a professional PDF report on the fly based on the ATS results
    and streams it back for instant download.
    """
    temp_report_name = f"report_{uuid.uuid4()}.pdf"
    temp_report_path = os.path.join(UPLOAD_DIR, temp_report_name)
    
    try:
        # Generate the PDF
        generate_pdf_report(request.dict(), temp_report_path)
        
        # Verify file exists
        if not os.path.exists(temp_report_path):
            raise HTTPException(status_code=500, detail="Failed to write PDF report to disk.")
            
        # Add background cleanup task to delete PDF after response is finished
        background_tasks.add_task(delete_file_after_delay, temp_report_path)
        
        return FileResponse(
            path=temp_report_path,
            filename="ATS_Resume_Analysis_Report.pdf",
            media_type="application/pdf"
        )
    except Exception as e:
        if os.path.exists(temp_report_path):
            os.remove(temp_report_path)
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF report: {str(e)}")

@router.delete("/cleanup")
async def cleanup_uploads():
    """
    Wipes out all temporary files in the uploads folder.
    """
    cleaned_count = 0
    errors = []
    
    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
                cleaned_count += 1
        except Exception as e:
            errors.append(f"Failed to delete {filename}: {str(e)}")
            
    if errors:
        return {"status": "partial_success", "cleaned_count": cleaned_count, "errors": errors}
    return {"status": "success", "cleaned_count": cleaned_count}
