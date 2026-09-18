variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "name" {
  description = "Name of the VPC Access connector"
  type        = string
}

variable "region" {
  description = "Region to deploy the connector in; must match the VPC subnet's region"
  type        = string
}

variable "network" {
  description = "Name (not self-link) of the existing VPC network to attach the connector to"
  type        = string
}

variable "ip_cidr_range" {
  description = "Unused /28 CIDR range, distinct from all other subnets in the VPC, reserved for the connector"
  type        = string

  validation {
    condition     = can(cidrhost(var.ip_cidr_range, 0))
    error_message = "ip_cidr_range must be a valid CIDR range."
  }
}

variable "min_instances" {
  description = "Minimum number of connector instances"
  type        = number
  default     = 2
}

variable "max_instances" {
  description = "Maximum number of connector instances"
  type        = number
  default     = 3
}

variable "machine_type" {
  description = "Machine type backing the connector instances"
  type        = string
  default     = "e2-micro"
}
