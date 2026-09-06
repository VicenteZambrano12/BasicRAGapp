# The VPC already exists and is not managed by this config; only subnets are created here.
data "google_compute_network" "this" {
  name    = var.name
  project = var.project_id
}

resource "google_compute_subnetwork" "this" {
  for_each = { for s in var.subnets : s.name => s }

  name          = each.value.name
  project       = var.project_id
  region        = each.value.region
  network       = data.google_compute_network.this.self_link
  ip_cidr_range = each.value.ip_cidr_range
}
