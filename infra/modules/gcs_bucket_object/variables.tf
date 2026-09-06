variable "bucket_name" {
  description = "Name of the GCS bucket to upload objects into"
  type        = string

  validation {
    condition     = trimspace(var.bucket_name) != ""
    error_message = "bucket_name must not be empty."
  }
}

variable "files" {
  description = "Map of destination object names to local file paths to upload"
  type        = map(string)
  default     = {}

  validation {
    condition = alltrue([
      for object_name, local_path in var.files :
      trimspace(object_name) != "" && trimspace(local_path) != "" && fileexists(local_path)
    ])
    error_message = "files must map non-empty object names to existing local files."
  }
}
