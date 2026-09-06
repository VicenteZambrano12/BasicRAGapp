output "assets_bucket_url" {
  description = "URL of the application assets bucket"
  value       = module.app_assets_bucket.url
}

output "docs_bucket_url" {
  description = "URL of the application docs bucket"
  value       = module.docs_bucket.url
}

output "asset_uploader_service_account_email" {
  description = "Email of the least-privilege asset uploader service account"
  value       = module.asset_uploader_sa.email
}

output "qdrant_server_self_link" {
  description = "Self link of the qdrant-server VM instance"
  value       = module.qdrant_server.self_link
}

output "qdrant_server_network_interfaces" {
  description = "Network interfaces of the qdrant-server VM instance"
  value       = module.qdrant_server.network_interfaces
}
