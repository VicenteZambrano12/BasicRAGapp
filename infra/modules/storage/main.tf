resource "google_storage_bucket" "app_data" {
  name                        = "${var.project_id}-rag-data"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true
  labels                      = merge(var.common_labels, { component = "storage" })
}
