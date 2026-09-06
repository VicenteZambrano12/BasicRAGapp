variable "project_id" {
  description = "GCP project ID that owns the service account"
  type        = string
}

variable "account_id" {
  description = "Account ID (short name) for the service account"
  type        = string
}

variable "display_name" {
  description = "Human-readable display name for the service account"
  type        = string
}
