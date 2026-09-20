resource "google_cloud_run_v2_service" "backend" {
  name     = "basicragapp-backend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  labels = merge(var.common_labels, { component = "backend" })

  template {
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      env {
        name  = "QDRANT_HOST"
        value = var.qdrant_internal_ip
      }

      env {
        name  = "QDRANT_PORT"
        value = "6333"
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
