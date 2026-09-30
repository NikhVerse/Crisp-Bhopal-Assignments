import os
import shutil
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load local environment configurations
load_dotenv()

# Import local modules from root
from utils import parse_resume, generate_pdf_report
from prompts import analyze_resume_text_with_grok

app = FastAPI(
    title="AI Resume Analyzer API",
    description="Unified Backend API for parsing, analyzing, and auditing resumes.",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Cleaned up file: {file_path}")
    except Exception as e:
        print(f"Error cleaning up file {file_path}: {e}")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "grok_api_configured": bool(os.getenv("GROK_API_KEY"))
    }

@app.post("/api/upload")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    temp_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        max_size = 10 * 1024 * 1024  # 10MB
        total_size = 0
        
        with open(temp_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024 * 64)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > max_size:
                    raise HTTPException(status_code=400, detail="File size exceeds the 10MB limit.")
                buffer.write(chunk)
                
        parsed_data = parse_resume(temp_path)
        parsed_data["file_id"] = unique_filename
        
        return parsed_data
        
    except HTTPException:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

@app.post("/api/analyze")
async def analyze_resume(request: AnalyzeRequest):
    try:
        # Import fallback generator from analyzer if needed
        # We can implement a clean local fallback analysis helper directly inside prompts/app
        # to ensure it is self-contained. Let's make a mock generator:
        try:
            report = await analyze_resume_text_with_grok(request.text, request.contact_info)
            report["is_fallback"] = False
        except Exception as e:
            print(f"Live API evaluation failed: {e}. Running local fallback analysis.")
            # Local fallback mock structure
            report = {
                "ats_score": 65,
                "summary": (
                    f"NOTICE: This is a fallback local analysis. Extracted details for candidate: "
                    f"{request.contact_info.get('name', 'Candidate')}. Setup GROK_API_KEY to unlock full AI audit."
                ),
                "strengths": [
                    "Extracted email and phone links cleanly.",
                    "Basic resume headers found.",
                ],
                "weaknesses": [
                    "Grok API Key not set or connection timed out.",
                    "AI keywords optimization audit was skipped."
                ],
                "missing_keywords": ["ATS Optimization", "Action Verbs"],
                "grammar": ["Ensure all bullets start with active verbs."],
                "recommendations": ["Set the GROK_API_KEY environment variable to activate Grok/Groq analysis."],
                "formatting_suggestions": ["Ensure 1 inch margins and safe system fonts."],
                "career_suggestions": ["Tailor skill tags directly to the target job specs."],
                "interview_readiness": "Limited local heuristic analysis.",
                "skills_heatmap": [
                    {"keyword": "Communication", "frequency": 2, "importance": "Medium"},
                    {"keyword": "Problem Solving", "frequency": 1, "importance": "High"}
                ],
                "readability_score": 75,
                "interview_probability": 45,
                "improvement_checklist": [
                    {"item": "Configure GROK_API_KEY in environment", "status": "pending"},
                    {"item": "Validate contact info fields", "status": "completed"}
                ],
                "is_fallback": True,
                "error_detail": str(e)
            }
            
        report["contact_info"] = request.contact_info
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/report")
async def download_report(request: ReportRequest, background_tasks: BackgroundTasks):
    temp_report_name = f"report_{uuid.uuid4()}.pdf"
    temp_report_path = os.path.join(UPLOAD_DIR, temp_report_name)
    
    try:
        generate_pdf_report(request.dict(), temp_report_path)
        
        if not os.path.exists(temp_report_path):
            raise HTTPException(status_code=500, detail="Failed to write PDF report.")
            
        background_tasks.add_task(delete_file_after_delay, temp_report_path)
        
        return FileResponse(
            path=temp_report_path,
            filename="ATS_Resume_Analysis_Report.pdf",
            media_type="application/pdf"
        )
    except Exception as e:
        if os.path.exists(temp_report_path):
            os.remove(temp_report_path)
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@app.delete("/api/cleanup")
async def cleanup_uploads():
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

# Mount static frontend files
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    # Check if there is a flat static folder or fallback
    @app.get("/")
    def read_root():
        return HTMLResponse(
            content="<h3>CVGrok API running!</h3><p>Static frontend files not found under 'frontend/' folder.</p>",
            status_code=200
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
