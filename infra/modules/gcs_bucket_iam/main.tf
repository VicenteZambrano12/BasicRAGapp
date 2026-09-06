# Bucket-scoped binding only, to keep service account permissions least-privilege.
resource "google_storage_bucket_iam_member" "this" {
  bucket = var.bucket_name
  role   = var.role
  member = var.member
}
