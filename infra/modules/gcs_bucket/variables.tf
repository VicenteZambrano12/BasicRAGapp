variable "project_id" {
  description = "GCP project ID that owns the bucket"
  type        = string
}

variable "bucket_name" {
  description = "Globally unique name for the GCS bucket"
  type        = string
}

variable "location" {
  description = "Location/region for the bucket"
  type        = string
}

variable "storage_class" {
  description = "Storage class for the bucket"
  type        = string
  default     = "STANDARD"
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
