output "object_names" {
  description = "Names of the uploaded objects"
  value       = [for o in google_storage_bucket_object.this : o.name]
}
