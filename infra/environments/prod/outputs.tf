output "cloud_run_url" {
  value = module.cloudrun.cloud_run_url
}

output "qdrant_vm_starter_function_url" {
  description = "HTTPS trigger URL the public React frontend calls to start the Qdrant VM."
  value       = module.qdrant_vm_starter.cloud_function_url
}

output "qdrant_vm_starter_service_account_email" {
  description = "Email of the service account the Cloud Function runs as (for the gcloud IAM grant script)."
  value       = module.qdrant_vm_starter.service_account_email
}
