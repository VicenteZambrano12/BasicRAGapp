output "uri" {
  description = "Public URL of the Cloud Run service"
  value       = google_cloud_run_v2_service.this.uri
}

output "name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_v2_service.this.name
}
