"""
routes/health_tips.py
---------------------
POST /api/health-tips — Health Tips Generator endpoint.

Accepts a health category and returns a personalised educational guide with
daily routines, diet, exercise, hydration, and lifestyle advice.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.models.health_tips import HealthTipsRequest, HealthTipsResponse
from backend.services.grok_service import call_grok

router = APIRouter()

SYSTEM_PROMPT = """You are a certified wellness coach and health educator providing evidence-based 
lifestyle and wellness guidance.

CRITICAL RULES:
1. Provide practical, actionable, evidence-based advice.
2. NEVER prescribe medications or specific medical treatments.
3. ALWAYS note that individual needs may vary and a doctor should be consulted for medical conditions.
4. Make the advice motivating, positive, and achievable.
5. Use relatable, encouraging language.

Respond in clear, structured Markdown with the following sections:
## Recommended Daily Routine
## Healthy Diet Plan
## Exercise and Activity Plan
## Hydration Guidelines
## General Lifestyle Advice
## Foods and Substances to Avoid
## Sleep Hygiene Routine
## Medical Disclaimer

Always end with the exact disclaimer:
"This AI assistant is for educational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment."
"""


@router.post("/health-tips", response_model=HealthTipsResponse)
async def generate_health_tips(data: HealthTipsRequest) -> JSONResponse:
    """
    Generate category-specific health and wellness tips.

    Args:
        data: Validated health tips request payload.

    Returns:
        JSON response with AI-generated wellness guide.
    """
    prompt = (
        f"Please generate a comprehensive, practical, and motivating health guide for the category: "
        f"\"{data.category}\".\n\n"
        "Include actionable daily habits, dietary recommendations, exercise ideas, "
        "and lifestyle changes. Make the advice realistic and achievable for everyday people."
    )

    try:
        result = call_grok(prompt, system_prompt=SYSTEM_PROMPT, temperature=0.5)
        return JSONResponse(content={"result": result, "status": "success"})
    except ValueError as exc:
        return JSONResponse(status_code=503, content={"error": str(exc), "status": "config_error"})
    except RuntimeError as exc:
        return JSONResponse(status_code=500, content={"error": str(exc), "status": "api_error"})
