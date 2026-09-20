module "artifact_registry" {
  source        = "../../modules/artifact_registry"
  project_id    = "basicrahgapp"
  location      = "europe-southwest1"
  repository_id = "portfolio-repo"
}

import {
  id = "projects/basicrahgapp/locations/europe-southwest1/repositories/portfolio-repo"
  to = module.artifact_registry.google_artifact_registry_repository.default
}