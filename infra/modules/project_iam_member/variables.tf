variable "project_id" {
  description = "GCP project ID"
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "project_id must be a 6-30 character lowercase Google Cloud project ID."
  }
}

variable "role" {
  description = "IAM role to grant at the project level; prefer narrowly-scoped predefined roles"
  type        = string

  validation {
    condition     = can(regex("^(roles|projects|organizations)/.+$", var.role))
    error_message = "role must be a valid predefined or custom IAM role reference."
  }
}

variable "member" {
  description = "IAM member to grant the role to, e.g. serviceAccount:<email>"
  type        = string

  validation {
    condition = (
      contains(["allAuthenticatedUsers", "allUsers"], var.member) ||
      can(regex("^(serviceAccount|user|group|domain):[^[:space:]]+$", var.member))
    )
    error_message = "member must be a supported IAM principal such as serviceAccount:<email>, user:<email>, or allUsers."
  }
}
