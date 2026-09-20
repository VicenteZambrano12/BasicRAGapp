variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "serverless_subnet_id" {
  type = string
}

variable "qdrant_internal_ip" {
  type = string
}

variable "common_labels" {
  type = map(string)
}
