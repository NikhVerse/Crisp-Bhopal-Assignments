"""
models/prescription.py
----------------------
Pydantic models for the Prescription Explainer endpoint.
"""

from pydantic import BaseModel, Field, field_validator


class PrescriptionRequest(BaseModel):
    """Input payload for the prescription explainer endpoint."""

    medicines: str = Field(
        ..., min_length=2, max_length=1000,
        description="Comma-separated list of medicine names (e.g., Metformin, Lisinopril)"
    )

    @field_validator("medicines", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip leading/trailing whitespace."""
        return v.strip() if isinstance(v, str) else v


class PrescriptionResponse(BaseModel):
    """Structured response from the prescription explainer."""

    result: str
    disclaimer: str = (
        "This AI assistant is for educational purposes only and is not a substitute "
        "for professional medical advice, diagnosis, or treatment."
    )
