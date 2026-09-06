output "self_link" {
  description = "Self link of the referenced VM instance"
  value       = data.google_compute_instance.this.self_link
}

output "network_interfaces" {
  description = "Network interfaces of the referenced VM instance"
  value       = data.google_compute_instance.this.network_interface
}
