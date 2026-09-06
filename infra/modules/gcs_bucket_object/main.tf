resource "google_storage_bucket_object" "this" {
  for_each = var.files

  name   = each.key
  bucket = var.bucket_name
  source = each.value
}
