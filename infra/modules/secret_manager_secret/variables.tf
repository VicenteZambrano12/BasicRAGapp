variable "project_id" {
  description = "GCP project ID that owns the secret"
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "project_id must be a 6-30 character lowercase Google Cloud project ID."
  }
}

variable "secret_id" {
  description = "ID of the Secret Manager secret to create"
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9_-]{1,255}$", var.secret_id))
    error_message = "secret_id must be 1-255 characters of letters, digits, underscores, or hyphens."
  }
}

variable "labels" {
  description = "Labels applied to the secret"
  type        = map(string)
  default     = {}
}
