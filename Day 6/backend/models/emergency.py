"""
models/emergency.py
-------------------
Pydantic models for the Emergency Checker endpoint.
"""

from pydantic import BaseModel, Field, field_validator


class EmergencyRequest(BaseModel):
    """Input payload for the emergency checker endpoint."""

    symptoms: str = Field(
        ..., min_length=5, max_length=2000,
        description="Symptoms the patient is currently experiencing"
    )

    @field_validator("symptoms", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip leading/trailing whitespace."""
        return v.strip() if isinstance(v, str) else v


class EmergencyResponse(BaseModel):
    """Structured response from the emergency checker."""

    result: str
    disclaimer: str = (
        "This AI assistant is for educational purposes only and is not a substitute "
        "for professional medical advice, diagnosis, or treatment."
    )
