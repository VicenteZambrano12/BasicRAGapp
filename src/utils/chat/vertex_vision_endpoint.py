"""Calls a self-deployed Vertex AI custom-model endpoint (e.g. a Model Garden
one-click-deploy endpoint) for chat/image completions, using its raw vLLM-style
`{"instances": [{"prompt", "multi_modal_data", "max_tokens"}]}` predict schema.
"""

import logging
from typing import Any, Optional

import google.auth
import requests
from google.auth.transport.requests import Request

from src.config.config_loader import config

logger = logging.getLogger(__name__)

_DEFAULT_PROMPT = (
    "Describe brevemente el contenido relevante de esta imagen "
    "para un asistente de estudio, en una o dos frases, en español."
)

_credentials = None


def is_configured() -> bool:
    """Whether the self-deployed endpoint's env vars are set."""
    return bool(
        (config("VERTEX_VISION_ENDPOINT_ID", default="") or "").strip()
        and (config("VERTEX_VISION_PROJECT_NUMBER", default="") or "").strip()
        and (config("VERTEX_VISION_DEDICATED_DNS", default="") or "").strip()
    )


def _get_access_token() -> str:
    global _credentials
    if _credentials is None:
        _credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    _credentials.refresh(Request())
    return _credentials.token


def _predict_url() -> str:
    endpoint_id = config("VERTEX_VISION_ENDPOINT_ID")
    project_number = config("VERTEX_VISION_PROJECT_NUMBER")
    # The deployed endpoint's region can differ from GOOGLE_CLOUD_LOCATION (used
    # elsewhere for embeddings/Qdrant), so it's configured independently here.
    location = config("VERTEX_VISION_LOCATION", default=config("GOOGLE_CLOUD_LOCATION", default="us-central1"))
    # The dedicated endpoint's DNS domain embeds its own routing number, which is
    # NOT the same as the project number required in the URL path below (confirmed
    # via `gcloud ai endpoints describe`), so both must be configured independently.
    domain = config("VERTEX_VISION_DEDICATED_DNS")
    return f"https://{domain}/v1/projects/{project_number}/locations/{location}/endpoints/{endpoint_id}:predict"


def _extract_text(prediction: Any) -> str:
    if isinstance(prediction, dict):
        for key in ("generated_text", "text", "content", "output"):
            value = prediction.get(key)
            if value:
                return str(value).strip()
        prediction = str(prediction)

    if isinstance(prediction, str):
        # This vLLM deployment echoes "Prompt:\n<prompt>\nOutput:\n<answer>"; keep only the answer.
        _, _, answer = prediction.partition("Output:")
        text = (answer or prediction).strip()
        # Qwen3's thinking-mode reasoning trace isn't meant to reach the end user.
        _, _, after_think = text.partition("</think>")
        return (after_think if "</think>" in text else text).strip()

    return str(prediction)


def vertex_generate(prompt: str, image_url: Optional[str] = None, max_tokens: int = 256) -> str:
    """Call the self-deployed endpoint's raw predict schema with a text (+ optional image) prompt."""
    instance = {"prompt": prompt, "max_tokens": max_tokens}
    if image_url:
        instance["multi_modal_data"] = {"image": image_url}

    response = requests.post(
        _predict_url(),
        headers={
            "Authorization": f"Bearer {_get_access_token()}",
            "Content-Type": "application/json",
        },
        json={"instances": [instance]},
        timeout=180,  # self-deployed models can cold-start slowly
    )
    response.raise_for_status()

    predictions = response.json().get("predictions", [])
    if not predictions:
        logger.warning("[VERTEX] Self-deployed endpoint returned no predictions")
        return ""

    return _extract_text(predictions[0]).strip()


def vertex_image_read(image_url: str, prompt: Optional[str] = None) -> str:
    """Return a short description of the given image using the self-deployed endpoint (if vision-capable)."""
    return vertex_generate(prompt or _DEFAULT_PROMPT, image_url=image_url, max_tokens=100)
