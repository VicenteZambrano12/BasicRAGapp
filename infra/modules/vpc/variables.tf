variable "project_id" {
  description = "GCP project ID that owns the VPC"
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "project_id must be a 6-30 character lowercase Google Cloud project ID."
  }
}

variable "name" {
  description = "Name of the existing VPC network to look up"
  type        = string

  validation {
    condition     = can(regex("^[a-z]([a-z0-9-]{0,61}[a-z0-9])?$", var.name))
    error_message = "name must be a 1-63 character lowercase network name that starts with a letter and does not end with a hyphen."
  }
}

variable "subnets" {
  description = "Subnets to create in this existing VPC"
  type = list(object({
    name          = string
    ip_cidr_range = string
    region        = string
  }))
  default = []

  validation {
    condition = alltrue([
      for subnet in var.subnets :
      can(regex("^[a-z]([a-z0-9-]{0,61}[a-z0-9])?$", subnet.name)) &&
      can(cidrhost(subnet.ip_cidr_range, 0)) &&
      trimspace(subnet.region) != ""
    ])
    error_message = "Each subnet must have a valid lowercase name, CIDR range, and non-empty region."
  }
}

variable "labels" {
  description = "GCP labels applied to the subnets; the module adds a generated name label to each subnet"
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
