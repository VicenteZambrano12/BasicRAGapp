variable "bucket_name" {
  description = "Name of the GCS bucket to grant access on"
  type        = string
}

variable "role" {
  description = "IAM role to grant, scoped only to this bucket (not project-wide)"
  type        = string
}

variable "member" {
  description = "IAM member to grant the role to, e.g. serviceAccount:<email>"
  type        = string
}
