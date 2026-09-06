# Module: gcs_bucket_object
# Purpose: Upload a map of local files to named objects in a Cloud Storage bucket.
# Usage:
#   module "documents" {
#     source = "./modules/gcs_bucket_object"
#     bucket_name = module.bucket.name
#     files = { "docs/readme.txt" = "${path.module}/readme.txt" }
#   }
resource "google_storage_bucket_object" "this" {
  for_each = var.files

  name   = each.key
  bucket = var.bucket_name
  source = each.value
}
