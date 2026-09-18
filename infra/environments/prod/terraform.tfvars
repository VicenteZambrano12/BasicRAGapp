project_id = "basicrahgapp"
region     = "europe-southwest1"

# Qdrant server: europe-southwest1 = Madrid region.
qdrant_zone = "europe-southwest1-a"

# qdrant_allowed_source_ranges defaults to [] (no extra direct external access;
# the app already reaches qdrant via the VPC connector firewall rule). Set it
# via TF_VAR_qdrant_allowed_source_ranges only if you need direct access from
# specific external IPs, e.g. your own machine for debugging.
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
