"""Builds the list of source documents to surface alongside a chat response."""

import logging
from datetime import timedelta
from typing import List, Optional

from google.cloud import storage

from src.api.DataClasses.chat_response import SourceDoc
from src.utils.gcs_signing import sign_gcs_url

logger = logging.getLogger(__name__)

SIGNED_URL_EXPIRY = timedelta(minutes=15)

_storage_client: Optional[storage.Client] = None


def _get_storage_client() -> storage.Client:
    """Lazily create a single Storage client for signing URLs."""
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client()
    return _storage_client


def _sign_url(bucket_name: str, object_name: str) -> str:
    """Generate a short-lived v4 signed URL for a private GCS object."""
    bucket = _get_storage_client().bucket(bucket_name)
    return sign_gcs_url(bucket, object_name, SIGNED_URL_EXPIRY)


def build_sources(documents: list) -> List[SourceDoc]:
    """
    Deduplicate retrieved chunks into one entry per source document.

    Keeps the page of the first (most relevant) chunk seen for each document,
    per doc_id, and signs a short-lived URL to open it directly from GCS.
    """
    sources: List[SourceDoc] = []
    seen_doc_ids = set()

    for doc in documents:
        metadata = doc.metadata
        doc_id = metadata.get("relative_path")
        bucket_name = metadata.get("bucket_name")
        object_name = metadata.get("object_name")
        if not doc_id or not bucket_name or not object_name or doc_id in seen_doc_ids:
            continue
        seen_doc_ids.add(doc_id)

        try:
            url = _sign_url(bucket_name, object_name)
        except Exception as exc:
            logger.warning(f"[SOURCES] Failed to sign URL for '{doc_id}': {exc}")
            continue

        sources.append(
            SourceDoc(
                doc_id=doc_id,
                file_name=metadata.get("file_name", doc_id),
                page=metadata.get("page_number"),
                url=url,
            )
        )

    return sources
