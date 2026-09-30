"""
Upload the local docs/ PDFs to GCS under the "documents" prefix:
  docs/<file>.pdf -> gs://<bucket>/documents/<file>.pdf

This only duplicates the files into the bucket for backup/serving purposes;
it does not touch the vector database. Safe to re-run: files are skipped if
an identical copy (by sha256) is already uploaded.

Usage: uv run python -m vector_db.upload_prompts
"""
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import storage

load_dotenv(override=True)

from src.config.config_loader import config
from src.utils.observability.logger import configure_logging
from vector_db.ingest import upload_to_gcs

logger = logging.getLogger(__name__)

# All uploaded files live under this folder in the GCS bucket, mirroring
# the local docs/... structure (e.g. gs://<bucket>/documents/how-it-works-en.pdf).
GCS_PROMPTS_PREFIX = "documents"


def upload_files(source_dir: str, bucket: "storage.Bucket", pattern: str) -> None:
    base_path = Path(source_dir)
    matched_files = list(base_path.rglob(pattern))

    if not matched_files:
        logger.warning(
            "No matching files found to upload",
            extra={"event": "no_source_files", "source_dir": source_dir, "pattern": pattern},
        )
        return

    logger.info(
        "Starting upload run",
        extra={
            "event": "upload_started",
            "source_dir": source_dir,
            "pattern": pattern,
            "file_count": len(matched_files),
        },
    )

    succeeded = 0
    for file_path in matched_files:
        relative_path = file_path.resolve().relative_to(base_path.resolve()).as_posix()
        object_name = f"{GCS_PROMPTS_PREFIX}/{relative_path}"
        try:
            gcs_location = upload_to_gcs(bucket, str(file_path), object_name)
            succeeded += 1
            logger.info(
                "GCS object ready",
                extra={
                    "event": "gcs_object_ready",
                    "relative_path": relative_path,
                    "gcs_uri": gcs_location["gcs_uri"],
                    "generation": gcs_location["gcs_generation"],
                },
            )
        except Exception:
            logger.error(
                "Failed to upload file",
                exc_info=True,
                extra={"event": "upload_failed", "relative_path": relative_path},
            )

    logger.info(
        "Upload run finished",
        extra={
            "event": "upload_completed",
            "succeeded": succeeded,
            "failed": len(matched_files) - succeeded,
            "file_count": len(matched_files),
        },
    )


if __name__ == "__main__":
    configure_logging()
    DOCS_DIRECTORY = os.getenv("DOCS_DIRECTORY", "./docs")
    bucket_name = config("GCS_BUCKET_NAME")
    storage_client = storage.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))
    gcs_bucket = storage_client.bucket(bucket_name)
    upload_files(DOCS_DIRECTORY, gcs_bucket, "*.pdf")
