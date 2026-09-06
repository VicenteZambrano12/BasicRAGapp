variable "project_id" {
  description = "GCP project ID that owns the instance"
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "project_id must be a 6-30 character lowercase Google Cloud project ID."
  }
}

variable "name" {
  description = "Name of the VM instance"
  type        = string

  validation {
    condition     = can(regex("^[a-z]([-a-z0-9]{0,61}[a-z0-9])?$", var.name))
    error_message = "name must be a 1-63 character lowercase Compute Engine instance name."
  }
}

variable "zone" {
  description = "Zone to deploy the instance in"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]*[a-z0-9]$", var.zone))
    error_message = "zone must be a non-empty Google Cloud zone name."
  }
}

variable "machine_type" {
  description = "Machine type, e.g. e2-micro"
  type        = string

  validation {
    condition     = trimspace(var.machine_type) != ""
    error_message = "machine_type must not be empty."
  }
}

variable "image" {
  description = "Boot disk source image, e.g. debian-cloud/debian-11"
  type        = string

  validation {
    condition     = trimspace(var.image) != ""
    error_message = "image must not be empty."
  }
}

variable "boot_disk_size_gb" {
  description = "Boot disk size in GB"
  type        = number
  default     = 10

  validation {
    condition     = var.boot_disk_size_gb > 0
    error_message = "boot_disk_size_gb must be greater than zero."
  }
}

variable "boot_disk_type" {
  description = "Boot disk type"
  type        = string
  default     = "pd-balanced"
}

variable "network" {
  description = "Network to attach the default network interface to"
  type        = string
  default     = "default"
}

variable "subnetwork" {
  description = "Subnetwork to attach the default network interface to"
  type        = string
  default     = null
}

variable "assign_external_ip" {
  description = "Whether to assign an ephemeral external IP via the default network interface"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Network tags applied to the instance, used to scope firewall rules"
  type        = list(string)
  default     = []
}

variable "labels" {
  description = "GCP labels applied to the instance"
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

variable "metadata" {
  description = "Metadata key/value pairs for the instance"
  type        = map(string)
  default     = {}
}

variable "metadata_startup_script" {
  description = "Startup script to run on boot"
  type        = string
  default     = null
}

variable "service_account_email" {
  description = "Email of the least-privilege service account to attach to the instance"
  type        = string
}

variable "service_account_scopes" {
  description = "OAuth scopes granted to the attached service account"
  type        = list(string)
  default     = ["https://www.googleapis.com/auth/cloud-platform"]
}
