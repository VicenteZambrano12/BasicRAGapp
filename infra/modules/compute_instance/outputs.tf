output "self_link" {
  description = "Self link of the instance"
  value       = google_compute_instance.this.self_link
}

output "name" {
  description = "Name of the instance"
  value       = google_compute_instance.this.name
}

output "network_interfaces" {
  description = "Network interfaces of the instance"
  value       = google_compute_instance.this.network_interface
}
