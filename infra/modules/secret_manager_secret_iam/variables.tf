variable "secret_id" {
  description = "Fully qualified resource name (or secret_id) of the Secret Manager secret to grant access on"
  type        = string

  validation {
    condition     = trimspace(var.secret_id) != ""
    error_message = "secret_id must not be empty."
  }
}

variable "role" {
  description = "IAM role to grant, scoped only to this secret (not project-wide)"
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
