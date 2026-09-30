"""
validators.py
-------------
Utility functions for input sanitization and validation used across all routes.
"""

import re
from typing import Any


# Maximum allowed characters for free-text fields
MAX_TEXT_LENGTH: int = 4000
MAX_SHORT_LENGTH: int = 500


def sanitize_text(value: str) -> str:
    """
    Strip leading/trailing whitespace and collapse multiple internal spaces.
    Removes potentially dangerous HTML/script tags.

    Args:
        value: Raw input string from the user.

    Returns:
        Cleaned string.
    """
    value = value.strip()
    # Remove HTML tags
    value = re.sub(r"<[^>]+>", "", value)
    # Collapse whitespace
    value = re.sub(r"\s+", " ", value)
    return value


def validate_age(age: Any) -> int:
    """
    Validate that age is a positive integer in a reasonable human range.

    Args:
        age: Value to validate (may be int, str, or float).

    Returns:
        Validated integer age.

    Raises:
        ValueError: When age is out of expected bounds.
    """
    try:
        age_int = int(age)
    except (TypeError, ValueError):
        raise ValueError("Age must be a whole number.")

    if age_int < 0 or age_int > 120:
        raise ValueError("Age must be between 0 and 120.")
    return age_int


def validate_text_length(value: str, field_name: str, max_len: int = MAX_TEXT_LENGTH) -> str:
    """
    Ensure a text field is non-empty and within the allowed length.

    Args:
        value:      The text to validate.
        field_name: Human-readable field name for error messages.
        max_len:    Maximum allowed character count.

    Returns:
        The original string if valid.

    Raises:
        ValueError: When the text is empty or too long.
    """
    if not value or not value.strip():
        raise ValueError(f"'{field_name}' cannot be empty.")
    if len(value) > max_len:
        raise ValueError(
            f"'{field_name}' exceeds the maximum allowed length of {max_len} characters."
        )
    return value


def validate_required_field(value: Any, field_name: str) -> Any:
    """
    Ensure a required field is provided and not None/empty.

    Args:
        value:      The field value.
        field_name: Human-readable field name.

    Returns:
        The original value if valid.

    Raises:
        ValueError: When the value is None or an empty string.
    """
    if value is None:
        raise ValueError(f"'{field_name}' is required.")
    if isinstance(value, str) and not value.strip():
        raise ValueError(f"'{field_name}' cannot be blank.")
    return value
