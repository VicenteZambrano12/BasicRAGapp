"""
Upload the local docs/ PDFs to GCS under the "documents" prefix:
  docs/<file>.pdf -> gs://<bucket>/documents/<file>.pdf

This only duplicates the files into the bucket for backup/serving purposes;
it does not touch the vector database. Safe to re-run: files are skipped if
an identical copy (by sha256) is already uploaded.

Usage: uv run python -m vector_db.upload_prompts
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import storage

load_dotenv(override=True)

from src.config.config_loader import config
from vector_db.ingest import upload_to_gcs

# All uploaded files live under this folder in the GCS bucket, mirroring
# the local docs/... structure (e.g. gs://<bucket>/documents/how-it-works-en.pdf).
GCS_PROMPTS_PREFIX = "documents"


def upload_files(source_dir: str, bucket: "storage.Bucket", pattern: str) -> None:
    base_path = Path(source_dir)
    matched_files = list(base_path.rglob(pattern))

    if not matched_files:
        print(f"No files matching '{pattern}' found inside {source_dir}.")
        return

    for file_path in matched_files:
        relative_path = file_path.resolve().relative_to(base_path.resolve()).as_posix()
        object_name = f"{GCS_PROMPTS_PREFIX}/{relative_path}"
        print(f"\n--- Processing: {relative_path} ---")
        try:
            gcs_location = upload_to_gcs(bucket, str(file_path), object_name)
            print(f"✓ GCS object ready: {gcs_location['gcs_uri']} (generation {gcs_location['gcs_generation']})")
        except Exception as e:
            print(f"❌ ERROR uploading '{relative_path}': {e}")


if __name__ == "__main__":
    DOCS_DIRECTORY = os.getenv("DOCS_DIRECTORY", "./docs")
    bucket_name = config("GCS_BUCKET_NAME")
    storage_client = storage.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))
    gcs_bucket = storage_client.bucket(bucket_name)
    upload_files(DOCS_DIRECTORY, gcs_bucket, "*.pdf")
