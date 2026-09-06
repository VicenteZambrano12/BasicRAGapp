variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "basicrahgapp"
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "europe-southwest1"
}

variable "qdrant_zone" {
  description = "Zone (Madrid region) to deploy the qdrant-server VM in"
  type        = string
  default     = "europe-southwest1-a"
}

variable "vpc_subnet_cidr" {
  description = "CIDR range for the basic-rag-app-subnet created inside the existing portfolio-demo-vpc; must not overlap other subnets in that VPC"
  type        = string
  default     = "10.10.0.0/24"
}

variable "qdrant_image" {
  description = "Boot disk source image/family for the qdrant-server VM; debian-11 was removed from the public catalog (EOL), so this defaults to the current Debian LTS"
  type        = string
  default     = "debian-cloud/debian-12"
}

variable "qdrant_sa_id" {
  description = "Account ID (short name) for the least-privilege service account used by the qdrant VM"
  type        = string
  default     = "qdrant-server"
}

variable "qdrant_api_key" {
  description = "API key used to secure access to the qdrant server"
  type        = string
  sensitive   = true
}

variable "qdrant_allowed_source_ranges" {
  description = "CIDR ranges allowed to reach the qdrant server ports; keep as narrow as possible"
  type        = list(string)
}

variable "docs_bucket_name" {
  description = "Globally unique name for the new application docs GCS bucket"
  type        = string
}

variable "asset_uploader_sa_id" {
  description = "Account ID (short name) for the least-privilege service account used to upload assets"
  type        = string
  default     = "asset-uploader"
}

# Placeholder: map of object keys to local file paths to upload into the docs bucket.
variable "local_doc_files" {
  description = "Map of destination object names to local doc file paths to upload"
  type        = map(string)
  default     = {}
}
