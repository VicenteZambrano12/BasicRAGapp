variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "location" {
  description = "Region for the Artifact Registry repository"
  type        = string
}

variable "repository_id" {
  description = "Repository ID (short name)"
  type        = string
}

variable "description" {
  description = "Human-readable description of the repository"
  type        = string
  default     = "Application container images"
}

variable "labels" {
  description = "Labels to apply to the repository"
  type        = map(string)
  default     = {}
}

variable "keep_version_count" {
  description = "Number of most recent image versions to retain; older ones are deleted by the repository's cleanup policy"
  type        = number
  default     = 2
}
