variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "basicrahgapp"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "project_id must be a 6-30 character lowercase Google Cloud project ID."
  }
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "europe-southwest1"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]*[a-z0-9]$", var.region))
    error_message = "region must be a non-empty Google Cloud region name."
  }
}

variable "qdrant_zone" {
  description = "Zone (Madrid region) to deploy the qdrant-server VM in"
  type        = string
  default     = "europe-southwest1-a"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]*[a-z0-9]$", var.qdrant_zone))
    error_message = "qdrant_zone must be a non-empty Google Cloud zone name."
  }
}

variable "vpc_subnet_cidr" {
  description = "CIDR range for the basic-rag-app-subnet created inside the existing portfolio-demo-vpc; must not overlap other subnets in that VPC"
  type        = string
  default     = "10.10.0.0/24"

  validation {
    condition     = can(cidrhost(var.vpc_subnet_cidr, 0))
    error_message = "vpc_subnet_cidr must be a valid CIDR range."
  }
}

variable "qdrant_image" {
  description = "Boot disk source image/family for the qdrant-server VM; debian-11 was removed from the public catalog (EOL), so this defaults to the current Debian LTS"
  type        = string
  default     = "debian-cloud/debian-12"

  validation {
    condition     = trimspace(var.qdrant_image) != ""
    error_message = "qdrant_image must not be empty."
  }
}

variable "qdrant_sa_id" {
  description = "Account ID (short name) for the least-privilege service account used by the qdrant VM"
  type        = string
  default     = "qdrant-server"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.qdrant_sa_id))
    error_message = "qdrant_sa_id must be a 6-30 character lowercase service account ID."
  }
}

variable "qdrant_api_key" {
  description = "API key used to secure access to the qdrant server"
  type        = string
  sensitive   = true

  validation {
    condition     = trimspace(var.qdrant_api_key) != ""
    error_message = "qdrant_api_key must not be empty."
  }
}

variable "qdrant_allowed_source_ranges" {
  description = "CIDR ranges allowed to reach the qdrant server ports; keep as narrow as possible"
  type        = list(string)

  validation {
    condition     = length(var.qdrant_allowed_source_ranges) > 0 && alltrue([for range in var.qdrant_allowed_source_ranges : can(cidrhost(range, 0))])
    error_message = "qdrant_allowed_source_ranges must contain at least one valid CIDR range."
  }
}

variable "docs_bucket_name" {
  description = "Globally unique name for the new application docs GCS bucket"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9._-]{1,61}[a-z0-9]$", var.docs_bucket_name))
    error_message = "docs_bucket_name must be 3-63 characters and use only lowercase letters, numbers, dots, underscores, or hyphens."
  }
}

variable "asset_uploader_sa_id" {
  description = "Account ID (short name) for the least-privilege service account used to upload assets"
  type        = string
  default     = "asset-uploader"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.asset_uploader_sa_id))
    error_message = "asset_uploader_sa_id must be a 6-30 character lowercase service account ID."
  }
}

variable "local_doc_files" {
  description = "Map of destination object names to local doc file paths to upload"
  type        = map(string)
  default     = {}

  validation {
    condition = alltrue([
      for object_name, local_path in var.local_doc_files :
      trimspace(object_name) != "" && trimspace(local_path) != "" && fileexists(local_path)
    ])
    error_message = "local_doc_files must map non-empty object names to existing local files."
  }
}
