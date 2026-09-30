"""
grok_service.py
---------------
Reusable service layer for calling the Grok API (OpenAI-compatible endpoint).
All API routes consume this single function to keep the codebase DRY.
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GROK_API_KEY: str = os.getenv("GROK_API_KEY", "")
DEFAULT_TIMEOUT: int = 60  # seconds

# Auto-detect provider based on key format
IS_GROQ = GROK_API_KEY.startswith("gsk_")

if IS_GROQ:
    GROK_BASE_URL = "https://api.groq.com/openai/v1"
    GROK_MODEL = "llama-3.3-70b-versatile"
else:
    GROK_BASE_URL = "https://api.x.ai/v1"
    GROK_MODEL = "grok-3-mini"



def call_grok(prompt: str, system_prompt: str = "", temperature: float = 0.4) -> str:
    """
    Send a prompt to the Grok API and return the assistant's text response.

    Args:
        prompt:        The user-facing message / question.
        system_prompt: Optional system-level instructions that shape the AI's behaviour.
        temperature:   Sampling temperature (lower = more deterministic, safer for medical context).

    Returns:
        The assistant's reply as a plain string.

    Raises:
        ValueError:   When the API key is missing or empty.
        RuntimeError: When the API call fails or returns an unexpected payload.
    """
    if not GROK_API_KEY:
        raise ValueError(
            "GROK_API_KEY is not set. "
            "Copy .env.example to .env and add your API key."
        )

    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json",
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": GROK_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 2048,
    }

    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            response = client.post(
                f"{GROK_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    except httpx.TimeoutException:
        raise RuntimeError(
            "The request to the Grok API timed out. "
            "Please try again in a moment."
        )
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status == 401:
            raise RuntimeError("Invalid GROK_API_KEY. Please check your .env file.")
        if status == 429:
            raise RuntimeError("Grok API rate limit exceeded. Please wait and retry.")
        raise RuntimeError(f"Grok API returned HTTP {status}: {exc.response.text}")
    except (KeyError, IndexError):
        raise RuntimeError("Unexpected response format from Grok API.")
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Grok API call failed: {exc}") from exc
