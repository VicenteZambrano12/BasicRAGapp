resource "google_cloud_run_v2_service" "backend" {
  name                = "basicragapp-backend"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  labels = merge(var.common_labels, { component = "backend" })

  template {
    service_account = var.service_account_email

    containers {
      image = var.app_container_image

      env {
        name  = "QDRANT_HOST"
        value = var.qdrant_internal_ip
      }

      env {
        name  = "QDRANT_PORT"
        value = "6333"
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }

      # I/O-bound app; cap worker count so N processes don't each duplicate the ML/genai import footprint.
      env {
        name  = "MAX_WORKERS"
        value = "2"
      }

      env {
        name = "APP_SECRETS_JSON"
        value_source {
          secret_key_ref {
            secret  = var.secret_id
            version = "latest"
          }
        }
      }

      # Default 512Mi was getting OOM-killed by the ML/genai import stack across gunicorn workers.
      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }
    }

    vpc_access {
      network_interfaces {
        subnetwork = var.serverless_subnet_id
      }
      egress = "PRIVATE_RANGES_ONLY"
    }
  }
}

resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.backend.location
  project  = var.project_id
  service  = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
