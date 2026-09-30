"""
routes/symptom.py
-----------------
POST /api/symptom — Symptom Analyzer endpoint.

Accepts patient details and returns an AI-generated educational analysis
including possible conditions, urgency level, specialist recommendation,
home care tips, and warning signs.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.models.symptom import SymptomRequest, SymptomResponse
from backend.services.grok_service import call_grok

router = APIRouter()

SYSTEM_PROMPT = """You are a compassionate and knowledgeable medical education assistant.
Your role is to provide helpful, educational information about symptoms and health concerns.

CRITICAL RULES:
1. NEVER diagnose any disease or medical condition.
2. NEVER claim certainty — always use language like "may suggest", "could be associated with", "possible considerations".
3. ALWAYS recommend consulting a qualified healthcare professional.
4. ALWAYS include the standard disclaimer.
5. If symptoms suggest an emergency, urgently recommend calling emergency services.

Respond in clear, structured Markdown with the following sections:
## Possible Conditions (Educational Only)
## Clinical Explanation
## Urgency Level
## Recommended Specialist
## Home Care Advice
## Emergency Warning Signs
## Lifestyle Recommendations
## Medical Disclaimer

Always end with the exact disclaimer:
"This AI assistant is for educational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment."
"""


@router.post("/symptom", response_model=SymptomResponse)
async def analyze_symptom(data: SymptomRequest) -> JSONResponse:
    """
    Analyze patient-reported symptoms and return an educational health summary.

    Args:
        data: Validated symptom request payload.

    Returns:
        JSON response with AI-generated analysis and disclaimer.
    """
    prompt = (
        f"Patient Information:\n"
        f"- Age: {data.age} years old\n"
        f"- Gender: {data.gender}\n"
        f"- Medical History: {data.medical_history}\n"
        f"- Current Symptoms: {data.current_symptoms}\n"
        f"- Duration of Symptoms: {data.duration}\n"
        f"- Severity: {data.severity}\n"
        f"- Current Medications: {data.current_medicines}\n\n"
        "Please provide a thorough educational analysis of these symptoms following the required format. "
        "Do NOT diagnose. Recommend seeing a qualified doctor."
    )

    try:
        result = call_grok(prompt, system_prompt=SYSTEM_PROMPT, temperature=0.3)
        return JSONResponse(content={"result": result, "status": "success"})
    except ValueError as exc:
        return JSONResponse(status_code=503, content={"error": str(exc), "status": "config_error"})
    except RuntimeError as exc:
        return JSONResponse(status_code=500, content={"error": str(exc), "status": "api_error"})
