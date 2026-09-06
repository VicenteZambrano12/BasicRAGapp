# Module: vpc
# Purpose: Look up an existing VPC network and create managed subnets in it.
# Usage:
#   module "vpc" {
#     source     = "./modules/vpc"
#     project_id = var.project_id
#     name       = "portfolio-demo-vpc"
#     subnets    = [{ name = "app-subnet", ip_cidr_range = "10.0.0.0/24", region = "us-central1" }]
#   }
#
# The VPC is intentionally not managed by this module; only its subnets are created here.
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
  labels = merge(var.labels, {
    name = "${lookup(var.labels, "project", var.project_id)}_${each.value.name}"
  })
}
