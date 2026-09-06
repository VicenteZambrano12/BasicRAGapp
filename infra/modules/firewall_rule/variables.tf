variable "project_id" {
  description = "GCP project ID"
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "project_id must be a 6-30 character lowercase Google Cloud project ID."
  }
}

variable "name" {
  description = "Name of the firewall rule"
  type        = string

  validation {
    condition     = can(regex("^[a-z]([-a-z0-9]{0,61}[a-z0-9])?$", var.name))
    error_message = "name must be a 1-63 character lowercase firewall rule name."
  }
}

variable "network" {
  description = "Network the rule applies to"
  type        = string
  default     = "default"
}

variable "direction" {
  description = "Direction of traffic, INGRESS or EGRESS"
  type        = string
  default     = "INGRESS"

  validation {
    condition     = contains(["INGRESS", "EGRESS"], var.direction)
    error_message = "direction must be either INGRESS or EGRESS."
  }
}

variable "target_tags" {
  description = "Instance tags this rule applies to, scoping it instead of the whole network"
  type        = list(string)
  default     = []
}

variable "source_ranges" {
  description = "CIDR ranges allowed as traffic source (required for INGRESS); keep as narrow as possible"
  type        = list(string)
  default     = []

  validation {
    condition     = alltrue([for range in var.source_ranges : can(cidrhost(range, 0))])
    error_message = "source_ranges must contain valid CIDR ranges."
  }
}

variable "allowed" {
  description = "List of allowed protocol/port objects, e.g. [{ protocol = \"tcp\", ports = [\"6333\"] }]"
  type = list(object({
    protocol = string
    ports    = list(string)
  }))

  validation {
    condition = alltrue([
      for rule in var.allowed : contains(["ah", "esp", "icmp", "ipip", "sctp", "tcp", "udp"], lower(rule.protocol)) &&
      alltrue([for port in rule.ports : can(regex("^[0-9]+(-[0-9]+)?$", port))])
    ])
    error_message = "allowed must use supported lowercase protocols and numeric ports or port ranges."
  }
}
