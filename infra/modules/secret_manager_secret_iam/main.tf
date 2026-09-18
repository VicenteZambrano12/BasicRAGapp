# Module: secret_manager_secret_iam
# Purpose: Grant one IAM role to one member on a specific Secret Manager secret.
# Usage:
#   module "secret_access" {
#     source    = "./modules/secret_manager_secret_iam"
#     secret_id = module.secret.name
#     role      = "roles/secretmanager.secretAccessor"
#     member    = "serviceAccount:example@example.iam.gserviceaccount.com"
#   }
# Secret-scoped binding keeps service account permissions least-privilege.
resource "google_secret_manager_secret_iam_member" "this" {
  secret_id = var.secret_id
  role      = var.role
  member    = var.member
}
