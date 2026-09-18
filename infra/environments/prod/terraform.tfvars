project_id = "basicrahgapp"
region     = "europe-southwest1"

# Qdrant server: europe-southwest1 = Madrid region.
qdrant_zone = "europe-southwest1-a"

# qdrant_allowed_source_ranges is intentionally not set here.
# Supply it via TF_VAR_qdrant_allowed_source_ranges
# (CI: GitHub Actions variable QDRANT_ALLOWED_SOURCE_RANGES; local: shell env).
#
# qdrant_api_key / gemini_api_key are no longer Terraform variables: their real
# values live only in Secret Manager (basicragapp-qdrant-api-key,
# basicragapp-gemini-api-key), populated manually via
# config/populate_demo_secret.py or gcloud, never through Terraform/CI.

docs_bucket_name = "basic_rag_app_docs"

# Placeholder values only; replace with actual local file paths before applying.
local_doc_files = {
  # "reports/example.pdf" = "REPLACE_WITH_LOCAL_FILE_PATH"
}
