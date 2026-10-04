variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "zone" {
  type = string
}

variable "subnet_id" {
  type = string
}

variable "common_labels" {
  type = map(string)
}

variable "qdrant_port" {
  type        = number
  description = "TCP port Qdrant listens on."
  default     = 6333
}

variable "idle_shutdown_minutes" {
  type        = number
  description = "Minutes of continuous idle (no active TCP connections on qdrant_port) before the VM shuts itself down via /usr/local/bin/check_idle.sh."
  default     = 30
}

variable "check_interval_minutes" {
  type        = number
  description = "How often (minutes) the root cron job in /etc/cron.d/qdrant-idle-shutdown runs check_idle.sh."
  default     = 5
}
