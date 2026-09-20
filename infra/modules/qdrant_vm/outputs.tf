output "qdrant_internal_ip" {
  value = google_compute_address.qdrant_ip.address
}
