# Module: compute_instance_lookup
# Purpose: Read the attributes of an existing Google Compute Engine VM without managing it.
# Usage:
#   module "existing_vm" {
#     source = "./modules/compute_instance_lookup"
#     project_id = var.project_id
#     instance_name = "existing-vm"
#     zone = "us-central1-a"
#   }
data "google_compute_instance" "this" {
  name    = var.instance_name
  zone    = var.zone
  project = var.project_id
}
