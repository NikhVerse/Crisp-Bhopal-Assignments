"""
models/health_tips.py
---------------------
Pydantic models for the Health Tips Generator endpoint.
"""

from typing import Literal
from pydantic import BaseModel, Field


VALID_CATEGORIES = Literal[
    "Weight Loss",
    "Diabetes",
    "Heart Health",
    "Mental Health",
    "Nutrition",
    "Sleep",
    "Exercise",
]


class HealthTipsRequest(BaseModel):
    """Input payload for the health tips generator endpoint."""

    category: VALID_CATEGORIES = Field(
        ..., description="Health topic category for generating personalised tips"
    )


class HealthTipsResponse(BaseModel):
    """Structured response from the health tips generator."""

    result: str
    disclaimer: str = (
        "This AI assistant is for educational purposes only and is not a substitute "
        "for professional medical advice, diagnosis, or treatment."
    )
