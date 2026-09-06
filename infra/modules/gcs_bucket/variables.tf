variable "project_id" {
  description = "GCP project ID that owns the bucket"
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "project_id must be a 6-30 character lowercase Google Cloud project ID."
  }
}

variable "bucket_name" {
  description = "Globally unique name for the GCS bucket"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9._-]{1,61}[a-z0-9]$", var.bucket_name))
    error_message = "bucket_name must be 3-63 characters, use lowercase letters, numbers, dots, underscores, or hyphens, and not start or end with a separator."
  }
}

variable "location" {
  description = "Location/region for the bucket"
  type        = string

  validation {
    condition     = trimspace(var.location) != ""
    error_message = "location must not be empty."
  }
}

variable "storage_class" {
  description = "Storage class for the bucket"
  type        = string
  default     = "STANDARD"

  validation {
    condition     = contains(["STANDARD", "NEARLINE", "COLDLINE", "ARCHIVE"], var.storage_class)
    error_message = "storage_class must be STANDARD, NEARLINE, COLDLINE, or ARCHIVE."
  }
}

variable "versioning_enabled" {
  description = "Whether object versioning is enabled"
  type        = bool
  default     = true
}

variable "force_destroy" {
  description = "Whether to allow Terraform to destroy the bucket even if it contains objects"
  type        = bool
  default     = false
}

variable "public_access_prevention" {
  description = "Public access prevention setting (enforced or inherited)"
  type        = string
  default     = "enforced"
}

variable "labels" {
  description = "GCP labels applied to the bucket; the module adds a generated name label"
  type        = map(string)
  default     = {}

  validation {
    condition = alltrue([
      for key, value in var.labels :
      can(regex("^[a-z][a-z0-9_-]{0,62}$", key)) &&
      (value == "" || can(regex("^[a-z0-9][a-z0-9_-]{0,62}$", value)))
    ])
    error_message = "labels must use lowercase GCP-compatible keys and values no longer than 63 characters."
  }
}
