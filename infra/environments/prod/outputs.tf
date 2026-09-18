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

output "demo_secret_id" {
  description = "Secret ID of the demo application secret (populate its value manually via gcloud)"
  value       = module.demo_secret.secret_id
}

output "demo_app_service_account_email" {
  description = "Email of the least-privilege service account granted secretAccessor on the demo secret"
  value       = module.demo_app_sa.email
}

output "qdrant_api_key_secret_id" {
  description = "Secret ID of the qdrant API key secret (populate its value manually via gcloud/populate_demo_secret.py)"
  value       = module.qdrant_api_key_secret.secret_id
}

output "gemini_api_key_secret_id" {
  description = "Secret ID of the Gemini API key secret (populate its value manually via gcloud/populate_demo_secret.py)"
  value       = module.gemini_api_key_secret.secret_id
}

