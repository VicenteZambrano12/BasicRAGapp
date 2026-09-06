resource "google_compute_firewall" "this" {
  name      = var.name
  project   = var.project_id
  network   = var.network
  direction = var.direction

  target_tags   = var.target_tags
  source_ranges = var.direction == "INGRESS" ? var.source_ranges : null

  dynamic "allow" {
    for_each = var.allowed
    content {
      protocol = allow.value.protocol
      ports    = allow.value.ports
    }
  }
}
