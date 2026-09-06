variable "bucket_name" {
  description = "Name of the GCS bucket to grant access on"
  type        = string

  validation {
    condition     = trimspace(var.bucket_name) != ""
    error_message = "bucket_name must not be empty."
  }
}

variable "role" {
  description = "IAM role to grant, scoped only to this bucket (not project-wide)"
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
    condition = contains(["allAuthenticatedUsers", "allUsers"], var.member) ||
      can(regex("^(serviceAccount|user|group|domain):[^[:space:]]+$", var.member))
    error_message = "member must be a supported IAM principal such as serviceAccount:<email>, user:<email>, or allUsers."
  }
}
