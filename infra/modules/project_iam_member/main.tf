# Module: project_iam_member
# Purpose: Grant one IAM role to one member at the Google Cloud project level.
# Usage:
#   module "project_access" {
#     source = "./modules/project_iam_member"
#     project_id = var.project_id
#     role = "roles/logging.logWriter"
#     member = "serviceAccount:example@example.iam.gserviceaccount.com"
#   }
# Use project-level bindings only when the role cannot be scoped to a specific resource.
resource "google_project_iam_member" "this" {
  project = var.project_id
  role    = var.role
  member  = var.member
}
