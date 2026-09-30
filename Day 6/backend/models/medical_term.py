"""
models/medical_term.py
----------------------
Pydantic models for the Medical Term Explainer endpoint.
"""

from pydantic import BaseModel, Field, field_validator


class MedicalTermRequest(BaseModel):
    """Input payload for the medical term explainer endpoint."""

    term: str = Field(
        ..., min_length=2, max_length=200,
        description="Medical term, abbreviation, or phrase to explain"
    )

    @field_validator("term", mode="before")
    @classmethod
    def strip_and_validate(cls, v: str) -> str:
        """Strip whitespace and ensure non-empty."""
        return v.strip() if isinstance(v, str) else v


class MedicalTermResponse(BaseModel):
    """Structured response from the medical term explainer."""

    result: str
    disclaimer: str = (
        "This AI assistant is for educational purposes only and is not a substitute "
        "for professional medical advice, diagnosis, or treatment."
    )
