# Module: gcs_bucket
# Purpose: Create a private Google Cloud Storage bucket with uniform access, versioning, and optional labels.
# Usage:
#   module "bucket" {
#     source = "./modules/gcs_bucket"
#     project_id = var.project_id
#     bucket_name = "example-docs"
#     location = "us-central1"
#   }
resource "google_storage_bucket" "this" {
  name                        = var.bucket_name
  project                     = var.project_id
  location                    = var.location
  storage_class               = var.storage_class
  uniform_bucket_level_access = true
  force_destroy               = var.force_destroy
  public_access_prevention    = var.public_access_prevention
  labels = merge(var.labels, {
    name = "${lookup(var.labels, "project", var.project_id)}_${var.bucket_name}"
  })

  versioning {
    enabled = var.versioning_enabled
  }
}
