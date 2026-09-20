resource "google_secret_manager_secret" "app_secrets" {
  secret_id = "basicragapp-secrets"
  labels    = var.common_labels

  replication {
    auto {}
  }
}
