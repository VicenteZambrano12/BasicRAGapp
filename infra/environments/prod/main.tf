module "artifact_registry" {
  source        = "../../modules/artifact_registry"
  project_id    = "basicrahgapp"
  location      = "europe-southwest1"
  repository_id = "portfolio-repo"
  common_labels = var.common_labels
}
module "networking" {
  source        = "../../modules/networking"
  project_id    = var.project_id
  region        = var.region
  vpc_name      = "portfolio-demo-vpc"
  common_labels = var.common_labels
}
module "storage" {
  source        = "../../modules/storage"
  project_id    = var.project_id
  region        = var.region
  common_labels = var.common_labels
}

module "secrets" {
  source        = "../../modules/secrets"
  project_id    = var.project_id
  region        = var.region
  common_labels = var.common_labels
}
import {
  id = "projects/basicrahgapp/locations/europe-southwest1/repositories/portfolio-repo"
  to = module.artifact_registry.google_artifact_registry_repository.default
}