variable "project_id" {
  type        = string
  description = "Google Cloud project ID."
}

variable "region" {
  type        = string
  description = "GCP region for Memorystore Valkey instance."
}

variable "service_name" {
  type        = string
  description = "Base service name for Valkey instance ID."
}

variable "valkey_version" {
  type        = string
  description = "Memorystore Valkey engine version."
  default     = "VALKEY_9_0"
}

variable "valkey_mode" {
  type        = string
  description = "Valkey cluster mode."
  default     = "CLUSTER_DISABLED"
}

variable "cluster_nodes" {
  type        = number
  description = "Number of cluster nodes or replicas."
  default     = 1
}

variable "network_id" {
  type        = string
  description = "ID of the VPC network where PSC connections will attach."
}

variable "service_connection_policy_id" {
  type        = string
  description = "Optional ID of the Service Connection Policy to ensure dependency ordering."
  default     = ""
}

variable "explicit_valkey_url" {
  type        = string
  description = "Explicit Valkey URL override (optional)."
  default     = ""
}
