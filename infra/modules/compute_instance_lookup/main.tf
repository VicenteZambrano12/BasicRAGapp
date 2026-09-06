# Read-only reference to a VM this config does not manage.
data "google_compute_instance" "this" {
  name    = var.instance_name
  zone    = var.zone
  project = var.project_id
}
