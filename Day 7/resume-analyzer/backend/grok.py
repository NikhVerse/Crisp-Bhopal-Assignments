import os
import json
import httpx
from typing import Dict, Any

# Fetch API key and model config from environment
GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-2-1212")  # default to grok-2-1212 or grok-2-latest
GROK_API_URL = "https://api.x.ai/v1/chat/completions"

async def analyze_resume_text_with_grok(resume_text: str, parsed_details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Asynchronously calls the Grok or Groq API to perform ATS Resume Analysis.
    Returns a structured dictionary matching the required ATS report schema.
    """
    api_key = os.getenv("GROK_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GROK_API_KEY is not set in the environment variables.")

    # Automatically detect provider (Groq vs xAI) based on the key prefix
    if api_key.startswith("gsk_"):
        api_url = "https://api.groq.com/openai/v1/chat/completions"
        model = os.getenv("GROK_MODEL", "llama-3.3-70b-versatile")
        print(f"Routing to Groq API endpoint with model: {model}")
    else:
        api_url = "https://api.x.ai/v1/chat/completions"
        model = os.getenv("GROK_MODEL", "grok-2-1212")
        print(f"Routing to xAI Grok API endpoint with model: {model}")


    system_prompt = (
        "You are an expert ATS (Applicant Tracking System) optimizer and hiring manager. "
        "Analyze the candidate's resume text and structured details to perform a deep ATS compatibility audit. "
        "Your feedback must be brutally honest, highly constructive, and structure-oriented. "
        "You MUST respond ONLY with a valid JSON object matching the requested schema. Do not output any preamble, markdown formatting (like ```json), or trailing text."
    )

    user_prompt = f"""
Analyze this resume text and extracted metadata:

--- RESUME TEXT ---
{resume_text}

--- PARSED METADATA ---
{json.dumps(parsed_details, indent=2)}

--- ANALYSIS REQUIREMENTS ---
You must evaluate:
1. Resume Formatting, ATS Compatibility & Readability
2. Grammar & Style Quality
3. Technical and Soft Skills coverage
4. Job Readiness, Action Verbs, and Professional Summary quality
5. Missing Keywords

You MUST return a JSON object with the following structure:
{{
  "ats_score": (integer between 0 and 100, representing overall score),
  "summary": "Detailed professional summary and overall feedback",
  "strengths": ["List of 3-5 specific strengths found in the resume"],
  "weaknesses": ["List of 3-5 specific weaknesses or areas of improvement"],
  "missing_keywords": ["List of high-value industry terms or keywords missing from the resume"],
  "grammar": ["List of grammar, word-choice, spelling, or styling suggestions"],
  "recommendations": ["List of highly actionable recommendations for improvement"],
  "formatting_suggestions": ["List of design, structure, layout, or formatting recommendations"],
  "career_suggestions": ["List of career development, trajectory, or skill acquisition recommendations"],
  "interview_readiness": "Detailed analysis of how ready this resume makes the candidate for an interview",
  "skills_heatmap": [
     {{"keyword": "Name of Skill", "frequency": 4, "importance": "High"}},
     {{"keyword": "Another Skill", "frequency": 1, "importance": "Medium"}}
  ],
  "readability_score": (integer between 0 and 100, estimating the ease of reading),
  "interview_probability": (integer between 0 and 100, representing likelihood of getting an interview based on the resume quality),
  "improvement_checklist": [
     {{"item": "Specific checklist action item", "status": "pending"}},
     {{"item": "Another checklist item", "status": "completed"}}
  ]
}}

Ensure all strings are valid JSON strings and numbers are integers. Double check your output conforms EXACTLY to this schema.
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            response_json = response.json()
            assistant_content = response_json["choices"][0]["message"]["content"]
            
            # Parse and return JSON
            return json.loads(assistant_content)
            
        except httpx.HTTPStatusError as e:
            # Handle specific API key authorization error or rate limits
            if e.response.status_code == 401:
                raise ValueError("Invalid Grok API Key. Please verify your GROK_API_KEY environment variable.")
            raise Exception(f"Grok API HTTP error: {e.response.status_code} - {e.response.text}")
        except json.JSONDecodeError as e:
            # Handle JSON parse errors
            raise Exception(f"Failed to parse Grok API JSON response: {str(e)}")
        except Exception as e:
            # General exception
            raise Exception(f"Grok API Request Failed: {str(e)}")
