variable "project_id" {
  description = "GCP project ID that owns the VPC"
  type        = string
}

variable "name" {
  description = "Name of the existing VPC network to look up"
  type        = string
}

variable "subnets" {
  description = "Subnets to create in this existing VPC"
  type = list(object({
    name          = string
    ip_cidr_range = string
    region        = string
  }))
  default = []
}
