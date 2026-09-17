"""Loads the subject/community-specific system prompt from prompts/<Community>/*.txt."""

import logging
from pathlib import Path

from src.utils.create_system.community_resolver import community_folder

logger = logging.getLogger(__name__)

PROMPTS_ROOT = Path(__file__).resolve().parents[3] / "prompts"

# Qdrant collection name (from es/en config subject_map) -> prompt file prefix.
_PROMPT_FILE_PREFIXES = {
    "arthistory": "artHistory",
    "biology": "biology",
    "chemistry": "chemistry",
    "economy": "economy",
    "english": "english",
    "history": "history",
    "language": "language",
    "philosofy": "philosofy",
    "physics": "physics",
    "scientistmath": "scientistMath",
    "socialsmath": "socialsMath",
}


def load_system_prompt(subject: str, community: str, collection: str) -> str:
    """Return the tutor system prompt for a subject/community pair."""
    folder = community_folder(community)
    prefix = _PROMPT_FILE_PREFIXES.get(collection, collection)
    prompt_file = PROMPTS_ROOT / folder / f"{prefix}_{folder.lower()}.txt"

    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")

    logger.warning(f"[CREATE_SYSTEM] Prompt file not found: {prompt_file}; using a generic prompt")
    return (
        f"Eres un tutor experto en {subject} para el examen PAU en {community}. "
        "Responde basándote únicamente en el contexto proporcionado."
    )
