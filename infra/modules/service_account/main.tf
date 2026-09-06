# Module: service_account
# Purpose: Create a Google Cloud service account with a project-scoped identity.
# Usage:
#   module "service_account" {
#     source = "./modules/service_account"
#     project_id = var.project_id
#     account_id = "app-runtime"
#     display_name = "Application runtime"
#   }
resource "google_service_account" "this" {
  project      = var.project_id
  account_id   = var.account_id
  display_name = var.display_name
}
