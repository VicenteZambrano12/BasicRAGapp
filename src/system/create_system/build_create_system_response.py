"""Create-system helper to build the endpoint response payload."""

from typing import Dict

from src.i18n import translate


def build_create_system_response(subject: str, language: str = "ES") -> Dict[str, str]:
    """Return the user-facing greeting after system initialization."""
    return {"response": translate("welcome", language, subject=subject)}
