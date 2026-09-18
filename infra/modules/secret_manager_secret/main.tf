# Module: secret_manager_secret
# Purpose: Create a Secret Manager secret container (automatic replication) without any version.
# The secret value is populated manually via `gcloud secrets versions add`, never through Terraform,
# so plaintext secret material never touches the Terraform state file.
# Usage:
#   module "secret" {
#     source     = "./modules/secret_manager_secret"
#     project_id = var.project_id
#     secret_id  = "demo-app-api-key"
#     labels     = local.resource_labels
#   }
resource "google_secret_manager_secret" "this" {
  project   = var.project_id
  secret_id = var.secret_id
  labels    = var.labels

  replication {
    auto {}
  }
}
