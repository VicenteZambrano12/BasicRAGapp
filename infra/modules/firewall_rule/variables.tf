variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "name" {
  description = "Name of the firewall rule"
  type        = string
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
}

variable "allowed" {
  description = "List of allowed protocol/port objects, e.g. [{ protocol = \"tcp\", ports = [\"6333\"] }]"
  type = list(object({
    protocol = string
    ports    = list(string)
  }))
}
