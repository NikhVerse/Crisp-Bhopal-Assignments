"""
routes/prescription.py
----------------------
POST /api/prescription — Prescription Explainer endpoint.

Accepts medicine names and returns educational information including purpose,
side effects, dosage info, food restrictions, storage, and warnings.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.models.prescription import PrescriptionRequest, PrescriptionResponse
from backend.services.grok_service import call_grok

router = APIRouter()

SYSTEM_PROMPT = """You are a licensed pharmacist educator who explains medications in plain language.

CRITICAL RULES:
1. Provide factual, educational information about medicines.
2. NEVER recommend specific dosages for individual patients — always say "as prescribed by your doctor".
3. ALWAYS warn patients NOT to self-medicate.
4. ALWAYS advise consulting a doctor or pharmacist before starting or stopping any medication.
5. Highlight serious warnings clearly.

Respond in clear, structured Markdown with the following sections for EACH medicine mentioned:
## [Medicine Name]
### Therapeutic Purpose and Medical Uses
### Common and Serious Side Effects
### Dosage Information
### Food, Beverage, and Drug Interactions
### Storage Requirements
### Important Safety Warnings and Contraindications
---
## Medical Disclaimer

Always end with the exact disclaimer:
"This AI assistant is for educational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment."
"""


@router.post("/prescription", response_model=PrescriptionResponse)
async def explain_prescription(data: PrescriptionRequest) -> JSONResponse:
    """
    Explain one or more medicines in patient-friendly language.

    Args:
        data: Validated prescription request payload.

    Returns:
        JSON response with AI-generated medicine explanations.
    """
    prompt = (
        f"Please provide detailed educational information about the following medicines:\n"
        f"{data.medicines}\n\n"
        "Cover each medicine separately. Use simple language. "
        "Include all safety warnings and do NOT recommend specific doses."
    )

    try:
        result = call_grok(prompt, system_prompt=SYSTEM_PROMPT, temperature=0.3)
        return JSONResponse(content={"result": result, "status": "success"})
    except ValueError as exc:
        return JSONResponse(status_code=503, content={"error": str(exc), "status": "config_error"})
    except RuntimeError as exc:
        return JSONResponse(status_code=500, content={"error": str(exc), "status": "api_error"})
