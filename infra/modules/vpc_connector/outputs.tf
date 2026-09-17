output "id" {
  description = "Fully qualified connector ID, usable as Cloud Run's vpc_access.connector"
  value       = google_vpc_access_connector.this.id
}

output "self_link" {
  description = "Self link of the connector"
  value       = google_vpc_access_connector.this.self_link
}
