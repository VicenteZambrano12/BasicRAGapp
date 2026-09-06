output "email" {
  description = "Email of the created service account"
  value       = google_service_account.this.email
}

output "name" {
  description = "Fully qualified resource name of the created service account"
  value       = google_service_account.this.name
}
