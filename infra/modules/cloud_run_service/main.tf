# Module: cloud_run_service
# Purpose: Deploy a Cloud Run v2 service wired to a VPC connector (for
# private access to VPC-only resources, e.g. the Qdrant VM) and a dedicated
# least-privilege runtime service account.
# Usage:
#   module "app" {
#     source                = "./modules/cloud_run_service"
#     project_id            = var.project_id
#     name                  = "basicragapp-app"
#     location              = var.region
#     image                 = "europe-southwest1-docker.pkg.dev/.../app:latest"
#     service_account_email = module.app_sa.email
#     vpc_connector_id      = module.connector.id
#     env                   = { QDRANT_HOST = "10.10.0.5" }
#   }
resource "google_cloud_run_v2_service" "this" {
  project  = var.project_id
  name     = var.name
  location = var.location
  ingress  = var.ingress

  template {
    service_account = var.service_account_email

    scaling {
      min_instance_count = var.min_instance_count
      max_instance_count = var.max_instance_count
    }

    vpc_access {
      connector = var.vpc_connector_id
      egress    = var.vpc_egress
    }

    containers {
      image = var.image

      ports {
        container_port = var.container_port
      }

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }

      dynamic "env" {
        for_each = var.env
        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = var.secret_env
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value.secret
              version = env.value.version
            }
          }
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  count    = var.allow_unauthenticated ? 1 : 0
  project  = var.project_id
  location = var.location
  name     = google_cloud_run_v2_service.this.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
