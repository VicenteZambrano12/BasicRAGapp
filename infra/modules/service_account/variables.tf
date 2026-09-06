variable "project_id" {
  description = "GCP project ID that owns the service account"
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "project_id must be a 6-30 character lowercase Google Cloud project ID."
  }
}

variable "account_id" {
  description = "Account ID (short name) for the service account"
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.account_id))
    error_message = "account_id must be a 6-30 character lowercase service account ID."
  }
}

variable "display_name" {
  description = "Human-readable display name for the service account"
  type        = string

  validation {
    condition     = trimspace(var.display_name) != ""
    error_message = "display_name must not be empty."
  }
}
