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

output "app_service_url" {
  description = "Public URL of the deployed Cloud Run application"
  value       = module.app_service.uri
}

output "app_images_repository" {
  description = "Fully qualified name of the Artifact Registry repository for app images"
  value       = module.app_images.name
}

