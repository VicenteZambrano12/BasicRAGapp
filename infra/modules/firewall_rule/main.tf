# Module: firewall_rule
# Purpose: Create a Google Compute Engine firewall rule with explicit traffic sources and allowed protocols.
# Usage:
#   module "firewall" {
#     source = "./modules/firewall_rule"
#     project_id = var.project_id
#     name = "allow-app"
#     network = var.network
#     allowed = [{ protocol = "tcp", ports = ["443"] }]
#   }
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
