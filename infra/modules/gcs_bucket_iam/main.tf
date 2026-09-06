# Module: gcs_bucket_iam
# Purpose: Grant one IAM role to one member on a specific Cloud Storage bucket.
# Usage:
#   module "bucket_access" {
#     source = "./modules/gcs_bucket_iam"
#     bucket_name = module.bucket.name
#     role = "roles/storage.objectAdmin"
#     member = "serviceAccount:example@example.iam.gserviceaccount.com"
#   }
# Bucket-scoped binding keeps service account permissions least-privilege.
resource "google_storage_bucket_iam_member" "this" {
  bucket = var.bucket_name
  role   = var.role
  member = var.member
}
