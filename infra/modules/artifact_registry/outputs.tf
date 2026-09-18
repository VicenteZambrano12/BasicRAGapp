output "repository_id" {
  description = "Repository ID"
  value       = google_artifact_registry_repository.this.repository_id
}

output "name" {
  description = "Fully qualified repository resource name"
  value       = google_artifact_registry_repository.this.name
}
