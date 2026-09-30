"""
models/symptom.py
-----------------
Pydantic models for the Symptom Analyzer endpoint.
"""

from typing import Literal
from pydantic import BaseModel, Field, field_validator


class SymptomRequest(BaseModel):
    """Input payload for the symptom analysis endpoint."""

    age: int = Field(..., ge=0, le=120, description="Patient age in years")
    gender: Literal["Male", "Female", "Other"] = Field(..., description="Patient gender")
    medical_history: str = Field(
        ..., min_length=1, max_length=2000,
        description="Existing medical conditions or past illnesses"
    )
    current_symptoms: str = Field(
        ..., min_length=3, max_length=2000,
        description="Symptoms the patient is currently experiencing"
    )
    duration: str = Field(
        ..., min_length=1, max_length=200,
        description="How long the symptoms have been present"
    )
    severity: Literal["Mild", "Moderate", "Severe"] = Field(
        ..., description="Self-assessed severity level"
    )
    current_medicines: str = Field(
        default="None",
        max_length=1000,
        description="Medications currently being taken"
    )

    @field_validator("medical_history", "current_symptoms", "duration", "current_medicines", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Remove leading/trailing whitespace from all string fields."""
        return v.strip() if isinstance(v, str) else v


class SymptomResponse(BaseModel):
    """Structured response from symptom analysis."""

    result: str
    disclaimer: str = (
        "This AI assistant is for educational purposes only and is not a substitute "
        "for professional medical advice, diagnosis, or treatment."
    )
