"""
models/report_summary.py
------------------------
Pydantic models for the Medical Report Summarizer endpoint.
"""

from pydantic import BaseModel, Field, field_validator


class ReportSummaryRequest(BaseModel):
    """Input payload for the medical report summarizer endpoint."""

    report_text: str = Field(
        ..., min_length=20, max_length=4000,
        description="Full text of the medical report to be summarized"
    )

    @field_validator("report_text", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip leading/trailing whitespace."""
        return v.strip() if isinstance(v, str) else v


class ReportSummaryResponse(BaseModel):
    """Structured response from the medical report summarizer."""

    result: str
    disclaimer: str = (
        "This AI assistant is for educational purposes only and is not a substitute "
        "for professional medical advice, diagnosis, or treatment."
    )
