# Module: compute_instance
# Purpose: Create a Google Compute Engine VM with optional networking, metadata, labels, and a dedicated service account.
# Usage:
#   module "vm" {
#     source = "./modules/compute_instance"
#     name = "app-vm"
#     project_id = var.project_id
#     zone = "us-central1-a"
#     machine_type = "e2-micro"
#     image = "debian-cloud/debian-12"
#   }
resource "google_compute_instance" "this" {
  name         = var.name
  project      = var.project_id
  zone         = var.zone
  machine_type = var.machine_type
  tags         = var.tags
  labels = merge(var.labels, {
    name = "${lookup(var.labels, "project", var.project_id)}_${var.name}"
  })

  boot_disk {
    initialize_params {
      image = var.image
      size  = var.boot_disk_size_gb
      type  = var.boot_disk_type
    }
  }

  network_interface {
    network    = var.network
    subnetwork = var.subnetwork

    dynamic "access_config" {
      for_each = var.assign_external_ip ? [1] : []
      content {}
    }
  }

  metadata                = var.metadata
  metadata_startup_script = var.metadata_startup_script

  # Dedicated least-privilege service account instead of the project default one.
  service_account {
    email  = var.service_account_email
    scopes = var.service_account_scopes
  }

  allow_stopping_for_update = true
}
