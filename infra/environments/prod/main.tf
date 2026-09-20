module "artifact_registry" {
  source        = "../../modules/artifact_registry"
  project_id    = "basicrahgapp"
  location      = "europe-southwest1"
  repository_id = "portfolio-repo"
  common_labels = var.common_labels
}
module "networking" {
  source                 = "../../modules/networking"
  project_id             = var.project_id
  region                 = var.region
  vpc_name               = "portfolio-demo-vpc"
  serverless_subnet_cidr = "10.0.2.0/24"
  common_labels          = var.common_labels
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

module "qdrant_vm" {
  source        = "../../modules/qdrant_vm"
  project_id    = var.project_id
  region        = var.region
  zone          = var.zone
  subnet_id     = module.networking.qdrant_subnet_id
  common_labels = var.common_labels
}

module "cloudrun" {
  source               = "../../modules/cloudrun"
  project_id           = var.project_id
  region               = var.region
  serverless_subnet_id = module.networking.serverless_subnet_id
  qdrant_internal_ip   = module.qdrant_vm.qdrant_internal_ip
  common_labels        = var.common_labels
}
import {
  id = "projects/basicrahgapp/locations/europe-southwest1/repositories/portfolio-repo"
  to = module.artifact_registry.google_artifact_registry_repository.default
}