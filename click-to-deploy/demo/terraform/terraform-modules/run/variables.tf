variable "project_id" {
  type        = string
  description = "Google Cloud project ID."
}

variable "region" {
  type        = string
  description = "GCP region."
}

variable "service_name" {
  type        = string
  description = "Name of the Cloud Run service."
}

variable "service_account_email" {
  type        = string
  description = "Service account email for Cloud Run."
}

variable "container_image" {
  type        = string
  description = "Container image URI for application."
}

variable "valkey_url" {
  type        = string
  description = "Redis/Valkey connection URL."
}

variable "valkey_host" {
  type        = string
  description = "Valkey host IP/hostname."
}

variable "valkey_port" {
  type        = number
  description = "Valkey port."
  default     = 6379
}

variable "valkey_password" {
  type        = string
  description = "Valkey password."
  default     = ""
  sensitive   = true
}

variable "valkey_ssl" {
  type        = bool
  description = "Valkey SSL flag."
  default     = false
}

variable "vertexai_model" {
  type        = string
  description = "Vertex AI Gemini model."
  default     = "gemini-2.5-flash"
}

variable "vertexai_embedding_model" {
  type        = string
  description = "Vertex AI Embedding model."
  default     = "text-embedding-004"
}

variable "semantic_cache_distance_threshold" {
  type        = string
  description = "Semantic cache distance threshold."
  default     = "0.20"
}

variable "semantic_cache_ttl" {
  type        = number
  description = "Semantic cache TTL in seconds."
  default     = 3600
}

variable "semantic_cache_index_name" {
  type        = string
  description = "Cache index name."
  default     = "support_concierge_cache"
}

variable "semantic_cache_prefix" {
  type        = string
  description = "Cache key prefix."
  default     = "support_concierge"
}

variable "network_name" {
  type        = string
  description = "VPC network name for Direct VPC Egress."
}

variable "subnet_name" {
  type        = string
  description = "VPC subnetwork name for Direct VPC Egress."
}

variable "gcp_account_name" {
  type        = string
  description = "Admin user account email receiving permissions."
  default     = ""
}

variable "enable_public_invoker" {
  type        = bool
  description = "Whether to allow unauthenticated public access (allUsers)."
  default     = true
}


