"""
routes/emergency.py
-------------------
POST /api/emergency — Emergency Checker endpoint.

Accepts symptom descriptions and returns a risk level assessment (Low / Medium /
High / Emergency), reasoning, and appropriate next steps. This endpoint is
designed with maximum safety guardrails and never replaces emergency services.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.models.emergency import EmergencyRequest, EmergencyResponse
from backend.services.grok_service import call_grok

router = APIRouter()

SYSTEM_PROMPT = """You are a first-aid and emergency triage education assistant.

CRITICAL SAFETY RULES:
1. NEVER diagnose any medical condition.
2. NEVER guarantee safety — symptoms can be misleading without physical examination.
3. If there is ANY doubt about safety, recommend Emergency care.
4. If symptoms suggest a life-threatening situation (chest pain, difficulty breathing, 
   unconsciousness, severe bleeding, stroke symptoms, anaphylaxis), IMMEDIATELY and 
   clearly state this is a POTENTIAL EMERGENCY and instruct to call emergency services.
5. ALWAYS end with the disclaimer.
6. Be clear, calm, and authoritative — this information could save a life.

Risk Level Definitions:
- 🟢 LOW: Symptoms are mild and unlikely to be immediately dangerous. Self-care and 
  monitoring is appropriate. See a doctor if symptoms persist or worsen.
- 🟡 MEDIUM: Symptoms warrant medical attention within 24 hours. Visit a clinic or 
  urgent care. Monitor for worsening.
- 🔴 HIGH: Symptoms require prompt medical care. Visit an emergency room or urgent 
  care immediately. Do not delay.
- 🚨 EMERGENCY: Symptoms may be life-threatening. Call emergency services (911 or 
  local equivalent) IMMEDIATELY.

Respond in clear, structured Markdown with the following sections:
## Risk Level Assessment
(State clearly: LOW / MEDIUM / HIGH / EMERGENCY)
## Assessment Rationale
## Recommended Action Plan
## Urgent Action Protocols
## Hospital and Emergency Facility Criteria
## Medical Disclaimer

Always end with the exact disclaimer:
"This AI assistant is for educational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment."
"""


@router.post("/emergency", response_model=EmergencyResponse)
async def check_emergency(data: EmergencyRequest) -> JSONResponse:
    """
    Assess the potential urgency of reported symptoms.

    Args:
        data: Validated emergency request payload.

    Returns:
        JSON response with AI-generated risk assessment.
    """
    prompt = (
        f"Please assess the urgency of the following symptoms and provide appropriate guidance:\n\n"
        f"Symptoms: {data.symptoms}\n\n"
        "Provide a clear risk level (Low/Medium/High/Emergency), explain your reasoning, "
        "and give actionable next steps. If there is ANY concern for life-threatening conditions, "
        "immediately recommend calling emergency services. NEVER diagnose."
    )

    try:
        result = call_grok(prompt, system_prompt=SYSTEM_PROMPT, temperature=0.2)
        return JSONResponse(content={"result": result, "status": "success"})
    except ValueError as exc:
        return JSONResponse(status_code=503, content={"error": str(exc), "status": "config_error"})
    except RuntimeError as exc:
        return JSONResponse(status_code=500, content={"error": str(exc), "status": "api_error"})
