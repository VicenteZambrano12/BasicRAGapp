# Module: artifact_registry
# Purpose: Create an Artifact Registry Docker repository for application container images.
# Usage:
#   module "app_images" {
#     source        = "./modules/artifact_registry"
#     project_id    = var.project_id
#     location      = var.region
#     repository_id = "basicragapp"
#   }
resource "google_artifact_registry_repository" "this" {
  project       = var.project_id
  location      = var.location
  repository_id = var.repository_id
  description   = var.description
  format        = "DOCKER"
  labels        = var.labels

  cleanup_policy_dry_run = false

  # Keep only the most recent N images; everything else is eligible for deletion.
  cleanup_policies {
    id     = "keep-minimum-versions"
    action = "KEEP"
    most_recent_versions {
      keep_count = var.keep_version_count
    }
  }

  cleanup_policies {
    id     = "delete-old-versions"
    action = "DELETE"
    condition {
      tag_state = "ANY"
    }
  }
}
