resource "google_compute_address" "qdrant_ip" {
  project      = var.project_id
  name         = "qdrant-ip"
  address_type = "INTERNAL"
  region       = var.region
  subnetwork   = var.subnet_id
}

resource "google_compute_disk" "qdrant_data" {
  project = var.project_id
  name    = "qdrant-data"
  type    = "pd-ssd"
  zone    = var.zone
  size    = 50
  labels  = merge(var.common_labels, { component = "database" })
}

resource "google_compute_instance" "qdrant_vm" {
  project      = var.project_id
  name         = "qdrant-vm"
  machine_type = "e2-medium"
  zone         = var.zone
  tags         = ["qdrant-vm"] # matches our firewall rule
  labels       = merge(var.common_labels, { component = "database" })

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
    }
  }

  attached_disk {
    source      = google_compute_disk.qdrant_data.id
    device_name = "qdrant-data"
  }

  network_interface {
    subnetwork = var.subnet_id
    network_ip = google_compute_address.qdrant_ip.address
  }

  metadata = {
    startup-script = <<-EOT
      #!/bin/bash
      set -e

      DISK_ID="/dev/disk/by-id/google-qdrant-data"
      MOUNT_POINT="/mnt/qdrant_data"

      if ! blkid "$DISK_ID"; then
        mkfs.ext4 -m 0 -F -E lazy_itable_init=0,lazy_journal_init=0,discard "$DISK_ID"
      fi

      mkdir -p "$MOUNT_POINT"
      mount -o discard,defaults "$DISK_ID" "$MOUNT_POINT"
      chmod a+w "$MOUNT_POINT"

      apt-get update
      apt-get install -y docker.io

      docker run -d \
        --name qdrant \
        -p 6333:6333 \
        -p 6334:6334 \
        -v "$MOUNT_POINT:/qdrant/storage" \
        --restart always \
        qdrant/qdrant
    EOT
  }
}
