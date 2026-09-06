variable "project_id" {
  description = "GCP project ID that owns the instance"
  type        = string
}

variable "name" {
  description = "Name of the VM instance"
  type        = string
}

variable "zone" {
  description = "Zone to deploy the instance in"
  type        = string
}

variable "machine_type" {
  description = "Machine type, e.g. e2-micro"
  type        = string
}

variable "image" {
  description = "Boot disk source image, e.g. debian-cloud/debian-11"
  type        = string
}

variable "boot_disk_size_gb" {
  description = "Boot disk size in GB"
  type        = number
  default     = 10
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
