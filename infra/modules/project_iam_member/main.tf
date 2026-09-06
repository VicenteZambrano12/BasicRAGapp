# Project-level binding: only use for roles that cannot be scoped to a single resource.
resource "google_project_iam_member" "this" {
  project = var.project_id
  role    = var.role
  member  = var.member
}
