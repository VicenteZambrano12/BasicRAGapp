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

locals {
  # Kept as its own heredoc (rather than nested inside the startup-script
  # one below) so bash heredoc terminators never get re-indented by
  # Terraform's dedent logic, which only looks at the outer EOT marker.
  check_idle_script = <<-EOT
    #!/bin/bash
    set -euo pipefail

    STATE_FILE="/var/run/qdrant_idle_minutes"
    PORT="${var.qdrant_port}"
    CHECK_INTERVAL_MINUTES="${var.check_interval_minutes}"
    IDLE_THRESHOLD_MINUTES="${var.idle_shutdown_minutes}"

    if [ ! -f "$STATE_FILE" ]; then
      echo 0 > "$STATE_FILE"
    fi

    ACTIVE_CONNECTIONS=$(ss -Htn state established "( sport = :$PORT or dport = :$PORT )" 2>/dev/null | wc -l)

    if [ "$ACTIVE_CONNECTIONS" -gt 0 ]; then
      echo 0 > "$STATE_FILE"
      logger -t check_idle "Qdrant has $ACTIVE_CONNECTIONS active connection(s) on port $PORT; idle timer reset."
      exit 0
    fi

    IDLE_MINUTES=$(cat "$STATE_FILE")
    IDLE_MINUTES=$((IDLE_MINUTES + CHECK_INTERVAL_MINUTES))
    echo "$IDLE_MINUTES" > "$STATE_FILE"
    logger -t check_idle "No active connections on port $PORT. Idle for $IDLE_MINUTES/$IDLE_THRESHOLD_MINUTES minute(s)."

    if [ "$IDLE_MINUTES" -ge "$IDLE_THRESHOLD_MINUTES" ]; then
      logger -t check_idle "Idle threshold of $IDLE_THRESHOLD_MINUTES minutes reached. Shutting down."
      sudo shutdown -h now
    fi
  EOT
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

      # --- On-demand start/stop: idle auto-shutdown watchdog ---
      # Installed here (rather than pushed externally via `gcloud compute
      # instances add-metadata`) so it lives in the same Terraform-owned
      # metadata map as the rest of the startup script and never gets
      # reverted/overwritten by a future `terraform apply` in this repo.
      # Base64-encoded so bash never has to parse a nested heredoc that
      # Terraform's own heredoc dedenting could otherwise mis-indent.
      # The public "start VM" Cloud Function (owned by the portfolio repo)
      # is the only way the VM comes back up once this shuts it down.
      echo "${base64encode(local.check_idle_script)}" | base64 -d > /usr/local/bin/check_idle.sh
      chmod +x /usr/local/bin/check_idle.sh
      echo '*/5 * * * * root /usr/local/bin/check_idle.sh >> /var/log/qdrant-idle-shutdown.log 2>&1' > /etc/cron.d/qdrant-idle-shutdown
      chmod 0644 /etc/cron.d/qdrant-idle-shutdown
    EOT
  }
}
