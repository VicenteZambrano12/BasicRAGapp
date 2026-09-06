output "self_link" {
  description = "Self link of the firewall rule"
  value       = google_compute_firewall.this.self_link
}
