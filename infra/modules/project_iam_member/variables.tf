variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "role" {
  description = "IAM role to grant at the project level; prefer narrowly-scoped predefined roles"
  type        = string
}

variable "member" {
  description = "IAM member to grant the role to, e.g. serviceAccount:<email>"
  type        = string
}
