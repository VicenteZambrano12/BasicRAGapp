"""Create-system helper to build the endpoint response payload."""

from typing import Dict


def build_create_system_response(subject: str) -> Dict[str, str]:
    """Return the user-facing greeting after system initialization."""
    return {"response": f"¡Hola! ¿Cómo puedo ayudarte a estudiar tu examen de {subject}?"}
