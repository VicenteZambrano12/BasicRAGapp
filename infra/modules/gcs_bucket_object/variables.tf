variable "bucket_name" {
  description = "Name of the GCS bucket to upload objects into"
  type        = string
}

variable "files" {
  description = "Map of destination object names to local file paths to upload"
  type        = map(string)
  default     = {}
}
