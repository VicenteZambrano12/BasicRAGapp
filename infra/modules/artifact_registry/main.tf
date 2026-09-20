resource "google_artifact_registry_repository" "default" {
  project       = var.project_id
  location      = var.location
  repository_id = var.repository_id
  format        = "DOCKER"
  description   = "Repositorio Docker principal gestionado por Terraform"
}