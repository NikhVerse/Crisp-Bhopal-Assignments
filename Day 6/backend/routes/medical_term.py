"""
routes/medical_term.py
----------------------
POST /api/medical-term — Medical Term Explainer endpoint.

Accepts a medical term, abbreviation, or phrase and returns a plain-language
explanation with causes, symptoms, diagnosis, treatment, and prevention.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.models.medical_term import MedicalTermRequest, MedicalTermResponse
from backend.services.grok_service import call_grok

router = APIRouter()

SYSTEM_PROMPT = """You are a medical education specialist who explains complex medical terms 
in simple, accessible language for patients and their families.

CRITICAL RULES:
1. Explain terms clearly — as if speaking to someone with no medical background.
2. NEVER diagnose the user based on the term they ask about.
3. ALWAYS encourage consulting a doctor for personal medical questions.
4. Use empathetic, reassuring language.

Respond in clear, structured Markdown with the following sections:
## Definition
## Clinical Causes
## Associated Symptoms
## Diagnosis Methods
## Treatment Options
## Prevention
## Plain-Language Summary
## Medical Disclaimer

Always end with the exact disclaimer:
"This AI assistant is for educational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment."
"""


@router.post("/medical-term", response_model=MedicalTermResponse)
async def explain_medical_term(data: MedicalTermRequest) -> JSONResponse:
    """
    Explain a medical term in plain language.

    Args:
        data: Validated medical term request payload.

    Returns:
        JSON response with AI-generated explanation.
    """
    prompt = (
        f"Please explain the medical term: \"{data.term}\"\n\n"
        "Provide a comprehensive but easy-to-understand explanation following the required format. "
        "Avoid jargon where possible. Include real-world context to make it relatable."
    )

    try:
        result = call_grok(prompt, system_prompt=SYSTEM_PROMPT, temperature=0.4)
        return JSONResponse(content={"result": result, "status": "success"})
    except ValueError as exc:
        return JSONResponse(status_code=503, content={"error": str(exc), "status": "config_error"})
    except RuntimeError as exc:
        return JSONResponse(status_code=500, content={"error": str(exc), "status": "api_error"})
