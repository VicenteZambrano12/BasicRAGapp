variable "project_id" {
  description = "GCP project ID that owns the VM instance"
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "project_id must be a 6-30 character lowercase Google Cloud project ID."
  }
}

variable "instance_name" {
  description = "Name of the existing Compute Engine VM instance"
  type        = string

  validation {
    condition     = can(regex("^[a-z]([-a-z0-9]{0,61}[a-z0-9])?$", var.instance_name))
    error_message = "instance_name must be a 1-63 character lowercase Compute Engine instance name."
  }
}

variable "zone" {
  description = "Zone of the existing Compute Engine VM instance"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]*[a-z0-9]$", var.zone))
    error_message = "zone must be a non-empty Google Cloud zone name."
  }
}
