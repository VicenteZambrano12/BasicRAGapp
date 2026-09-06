output "self_link" {
  description = "Self link of the existing VPC network"
  value       = data.google_compute_network.this.self_link
}

output "name" {
  description = "Name of the existing VPC network"
  value       = data.google_compute_network.this.name
}

output "subnet_self_links" {
  description = "Map of subnet name to self link"
  value       = { for k, s in google_compute_subnetwork.this : k => s.self_link }
}
