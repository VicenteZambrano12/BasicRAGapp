resource "google_secret_manager_secret" "app_secrets" {
  secret_id = "basicragapp-secrets"
  labels    = merge(var.common_labels, { component = "secrets" })

  replication {
    auto {}
  }
}
