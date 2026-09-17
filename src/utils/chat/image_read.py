"""Vision helper that produces a short text description of a user-provided image."""

import logging

from src.utils.chat.gemini_vision import gemini_image_read
from src.utils.chat.vertex_vision_endpoint import is_configured, vertex_image_read

logger = logging.getLogger(__name__)


def image_read(image_url: str) -> str:
    """Return a short natural-language description of the given image URL/data URL.

    Uses the self-deployed Vertex AI vision endpoint (VERTEX_VISION_ENDPOINT_ID/
    VERTEX_VISION_PROJECT_NUMBER) when configured, falling back to Gemini otherwise
    (or if the self-deployed endpoint call fails).
    """
    if is_configured():
        try:
            return vertex_image_read(image_url)
        except Exception as exc:
            logger.warning(f"[VISION] Self-deployed endpoint failed, falling back to Gemini: {exc}")

    return gemini_image_read(image_url)
