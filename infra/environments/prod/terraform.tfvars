project_id = "basicrahgapp"
region     = "europe-southwest1"

# Qdrant server: europe-southwest1 = Madrid region.
qdrant_zone = "europe-southwest1-a"

# qdrant_api_key and qdrant_allowed_source_ranges are intentionally not set here.
# Supply them via TF_VAR_qdrant_api_key / TF_VAR_qdrant_allowed_source_ranges
# (CI: GitHub secrets QDRANT_API_KEY / QDRANT_ALLOWED_SOURCE_RANGES; local: shell env).

docs_bucket_name = "basic_rag_app_docs"

# Placeholder values only; replace with actual local file paths before applying.
local_doc_files = {
  # "reports/example.pdf" = "REPLACE_WITH_LOCAL_FILE_PATH"
}
