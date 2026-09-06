variable "project_id" {
  description = "GCP project ID that owns the VM instance"
  type        = string
}

variable "instance_name" {
  description = "Name of the existing Compute Engine VM instance"
  type        = string
}

variable "zone" {
  description = "Zone of the existing Compute Engine VM instance"
  type        = string
}
