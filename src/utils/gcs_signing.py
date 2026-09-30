"""Signs short-lived GCS URLs, working both locally (service account key file) and on
Cloud Run/GCE (no private key available, so the IAM signBlob API is used instead via
self-impersonation; the runtime service account needs roles/iam.serviceAccountTokenCreator
on itself for this)."""

from datetime import timedelta

import google.auth
from google.auth.transport import requests as google_auth_requests
from google.cloud import storage


def sign_gcs_url(bucket: "storage.Bucket", object_name: str, expiration: timedelta, method: str = "GET") -> str:
    """Generate a v4 signed URL for a private GCS object."""
    blob = bucket.blob(object_name)
    credentials, _ = google.auth.default()

    # Credentials backed by a service account key file can sign directly.
    if hasattr(credentials, "sign_bytes"):
        return blob.generate_signed_url(version="v4", expiration=expiration, method=method)

    # Attached service accounts (Cloud Run/GCE) have no private key; sign via the IAM API instead.
    credentials.refresh(google_auth_requests.Request())
    return blob.generate_signed_url(
        version="v4",
        expiration=expiration,
        method=method,
        service_account_email=credentials.service_account_email,
        access_token=credentials.token,
    )
