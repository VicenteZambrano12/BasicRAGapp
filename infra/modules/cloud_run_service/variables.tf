variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "name" {
  description = "Name of the Cloud Run service"
  type        = string
}

variable "location" {
  description = "Region to deploy the Cloud Run service in"
  type        = string
}

variable "image" {
  description = "Fully qualified container image reference (registry/repo:tag)"
  type        = string
}

variable "service_account_email" {
  description = "Email of the least-privilege service account the container runs as"
  type        = string
}

variable "vpc_connector_id" {
  description = "Fully qualified ID of the Serverless VPC Access connector to attach"
  type        = string
}

variable "vpc_egress" {
  description = "Which egress traffic is routed through the VPC connector"
  type        = string
  default     = "PRIVATE_RANGES_ONLY"
}

variable "container_port" {
  description = "Port the container listens on"
  type        = number
  default     = 8080
}

variable "cpu" {
  description = "CPU limit per container instance"
  type        = string
  default     = "1"
}

variable "memory" {
  description = "Memory limit per container instance"
  type        = string
  default     = "1Gi"
}

variable "min_instance_count" {
  description = "Minimum number of running instances (0 allows scale-to-zero)"
  type        = number
  default     = 0
}

variable "max_instance_count" {
  description = "Maximum number of running instances"
  type        = number
  default     = 3
}

variable "env" {
  description = "Plain (non-secret) environment variables for the container"
  type        = map(string)
  default     = {}
}

variable "secret_env" {
  description = "Environment variables sourced from Secret Manager: { NAME = { secret = \"secret-id\", version = \"latest\" } }"
  type = map(object({
    secret  = string
    version = string
  }))
  default = {}
}

variable "ingress" {
  description = "Ingress traffic setting for the service"
  type        = string
  default     = "INGRESS_TRAFFIC_ALL"
}

variable "allow_unauthenticated" {
  description = "Whether to allow unauthenticated public invocations"
  type        = bool
  default     = true
}
