"""
One-off migration: move existing GCS objects into the `docs/` folder so the
bucket layout matches what vector_db/ingest.py now writes (docs/<subject>/<file>.pdf).

Safe to re-run: objects already under `docs/` are left untouched, so a second
run is a no-op. Run this BEFORE re-running ingestion, so the copy preserves the
original `source_sha256` metadata and ingestion can skip re-uploading unchanged
files.

Usage: uv run python -m vector_db.migrate_to_docs_prefix
"""
import logging
import os

from dotenv import load_dotenv
from google.cloud import storage

load_dotenv(override=True)

from src.config.config_loader import config
from src.utils.observability.logger import configure_logging
from vector_db.ingest import GCS_DOCS_PREFIX

logger = logging.getLogger(__name__)


def migrate(bucket: "storage.Bucket") -> None:
    to_migrate = [b for b in bucket.list_blobs() if not b.name.startswith(f"{GCS_DOCS_PREFIX}/")]

    if not to_migrate:
        logger.info(
            "Nothing to migrate, all objects already use the target prefix",
            extra={"event": "migration_skipped", "prefix": GCS_DOCS_PREFIX},
        )
        return

    logger.info(
        "Starting GCS prefix migration",
        extra={
            "event": "migration_started",
            "prefix": GCS_DOCS_PREFIX,
            "object_count": len(to_migrate),
        },
    )

    for blob in to_migrate:
        new_name = f"{GCS_DOCS_PREFIX}/{blob.name}"
        logger.info(
            "Moving GCS object",
            extra={"event": "object_moved", "source": blob.name, "destination": new_name},
        )
        bucket.copy_blob(blob, bucket, new_name)
        bucket.delete_blob(blob.name)

    logger.info(
        "GCS prefix migration completed",
        extra={
            "event": "migration_completed",
            "prefix": GCS_DOCS_PREFIX,
            "object_count": len(to_migrate),
        },
    )


if __name__ == "__main__":
    configure_logging()
    bucket_name = config("GCS_BUCKET_NAME")
    storage_client = storage.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))
    gcs_bucket = storage_client.bucket(bucket_name)
    migrate(gcs_bucket)
