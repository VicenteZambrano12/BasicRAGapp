"""Endpoint for redirecting to static documents (e.g. the How It Works PDF) stored in GCS."""

import logging
from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from google.cloud import storage

from src.config.config_loader import config
from src.utils.gcs_signing import sign_gcs_url

logger = logging.getLogger(__name__)

router = APIRouter()

SIGNED_URL_EXPIRY = timedelta(minutes=15)

# Static documents live under this folder in the GCS bucket (uploaded via vector_db/upload_prompts.py).
GCS_DOCUMENTS_PREFIX = "documents"

_HOW_IT_WORKS_OBJECT_BY_LANGUAGE = {
    "ES": f"{GCS_DOCUMENTS_PREFIX}/how-it-works-es.pdf",
    "EN": f"{GCS_DOCUMENTS_PREFIX}/how-it-works-en.pdf",
}

_storage_client: storage.Client | None = None


def _get_storage_client() -> storage.Client:
    """Lazily create a single Storage client for signing URLs."""
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client()
    return _storage_client


@router.get(
    "/docs/how-it-works",
    summary="Redirect to the localized How It Works PDF",
    description="Signs a short-lived URL for the requested language's PDF stored in GCS and redirects to it.",
)
async def get_how_it_works_pdf(language: Literal["ES", "EN"] = "ES") -> RedirectResponse:
    """Redirect to a short-lived signed URL for the localized How It Works PDF."""

    object_name = _HOW_IT_WORKS_OBJECT_BY_LANGUAGE[language]
    bucket_name = config("GCS_BUCKET_NAME")

    try:
        bucket = _get_storage_client().bucket(bucket_name)
        url = sign_gcs_url(bucket, object_name, SIGNED_URL_EXPIRY)
    except Exception as exc:
        logger.error(
            "Failed to sign document URL",
            exc_info=True,
            extra={
                "event": "document_signing_failed",
                "object_name": object_name,
                "bucket_name": bucket_name,
                "language": language,
            },
        )
        raise HTTPException(status_code=502, detail="Unable to retrieve the requested document.") from exc

    return RedirectResponse(url=url, status_code=307)
