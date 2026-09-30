"""Loads the subject/community-specific system prompt from gs://<GCS_BUCKET_NAME>/prompts/<Community>/*.txt."""

import logging

from google.cloud import storage
from google.cloud.exceptions import NotFound

from src.config.config_loader import config
from src.utils.create_system.community_resolver import community_folder

logger = logging.getLogger(__name__)

# Prompt files live under this folder in the GCS bucket, mirroring the local prompts/ structure.
GCS_PROMPTS_PREFIX = "prompts"

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

_storage_client: storage.Client | None = None


def _get_storage_client() -> storage.Client:
    """Lazily create a single Storage client for reading prompt blobs."""
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client()
    return _storage_client


def load_system_prompt(subject: str, community: str, collection: str) -> str:
    """Return the tutor system prompt for a subject/community pair."""
    folder = community_folder(community)
    prefix = _PROMPT_FILE_PREFIXES.get(collection, collection)
    object_name = f"{GCS_PROMPTS_PREFIX}/{folder}/{prefix}_{folder.lower()}.txt"
    bucket_name = config("GCS_BUCKET_NAME")

    try:
        blob = _get_storage_client().bucket(bucket_name).blob(object_name)
        return blob.download_as_text(encoding="utf-8")
    except NotFound:
        logger.warning(
            "Prompt object not found in GCS, using a generic prompt",
            extra={
                "event": "prompt_not_found",
                "bucket_name": bucket_name,
                "object_name": object_name,
                "subject": subject,
                "community": community,
            },
        )
    except Exception:
        logger.error(
            "Failed to load prompt from GCS, using a generic prompt",
            exc_info=True,
            extra={
                "event": "prompt_load_failed",
                "bucket_name": bucket_name,
                "object_name": object_name,
                "subject": subject,
                "community": community,
            },
        )

    return (
        f"Eres un tutor experto en {subject} para el examen PAU en {community}. "
        "Responde basándote únicamente en el contexto proporcionado."
    )

