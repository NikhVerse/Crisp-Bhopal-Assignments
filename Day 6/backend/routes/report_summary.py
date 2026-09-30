"""
routes/report_summary.py
------------------------
POST /api/report-summary — Medical Report Summarizer endpoint.

Accepts raw medical report text and returns a simplified, patient-friendly
summary with key findings, abnormal values, and recommended questions for
the patient's doctor.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.models.report_summary import ReportSummaryRequest, ReportSummaryResponse
from backend.services.grok_service import call_grok

router = APIRouter()

SYSTEM_PROMPT = """You are a medical literacy specialist who translates complex medical reports 
into plain language that patients and their families can understand.

CRITICAL RULES:
1. Simplify all medical terminology — use plain, everyday language.
2. NEVER make a diagnosis based on the report.
3. NEVER tell the patient to ignore abnormal values without consulting a doctor.
4. ALWAYS encourage the patient to discuss findings with their doctor.
5. Be reassuring but honest about findings that require attention.
6. Clearly flag any values that are outside normal range.

Respond in clear, structured Markdown with the following sections:
## Executive Report Summary
## Key Findings
## Flagged Abnormal Values
## Clinical Significance and Interpretation
## Questions to Ask Your Treating Physician
## Recommended Next Steps
## Medical Disclaimer

Always end with the exact disclaimer:
"This AI assistant is for educational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment."
"""


@router.post("/report-summary", response_model=ReportSummaryResponse)
async def summarize_report(data: ReportSummaryRequest) -> JSONResponse:
    """
    Summarize a medical report in patient-friendly language.

    Args:
        data: Validated report summary request payload.

    Returns:
        JSON response with AI-generated report summary.
    """
    prompt = (
        f"Please summarize the following medical report in simple, patient-friendly language:\n\n"
        f"---\n{data.report_text}\n---\n\n"
        "Explain what the findings mean, highlight any abnormal values, and suggest "
        "questions the patient should ask their doctor. Do NOT make any diagnosis."
    )

    try:
        result = call_grok(prompt, system_prompt=SYSTEM_PROMPT, temperature=0.3)
        return JSONResponse(content={"result": result, "status": "success"})
    except ValueError as exc:
        return JSONResponse(status_code=503, content={"error": str(exc), "status": "config_error"})
    except RuntimeError as exc:
        return JSONResponse(status_code=500, content={"error": str(exc), "status": "api_error"})
