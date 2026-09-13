"""Fallback vision backend: Gemini multimodal chat model."""

import logging
from typing import Optional

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from src.config.config_loader import config

logger = logging.getLogger(__name__)

_IMAGE_PROMPT = (
    "Describe brevemente el contenido relevante de esta imagen para un asistente de estudio "
    "(texto, ejercicios, diagramas, etc.). Responde en una o dos frases, en español."
)

_vision_model: Optional[ChatGoogleGenerativeAI] = None


def _get_vision_model() -> ChatGoogleGenerativeAI:
    global _vision_model
    if _vision_model is None:
        model_name = config("LLM_MODEL", default="gemini-2.5-flash-lite")
        _vision_model = ChatGoogleGenerativeAI(
            model=model_name, google_api_key=config("GCP_API_KEY", default=None)
        )
    return _vision_model


def gemini_image_read(image_url: str) -> str:
    """Return a short natural-language description of the given image via Gemini."""
    model = _get_vision_model()
    message = HumanMessage(
        content=[
            {"type": "text", "text": _IMAGE_PROMPT},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]
    )
    response = model.invoke([message])
    return response.content
