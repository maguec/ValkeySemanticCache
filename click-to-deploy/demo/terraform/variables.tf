# Required Click-to-Deploy Platform Variables

variable "project_id" {
  type        = string
  description = "The Google Cloud project ID where resources are deployed."
  default     = ""
}

variable "gcp_project_id" {
  type        = string
  description = "The Google Cloud project ID (alternative parameter name)."
  default     = ""
}

variable "project_name" {
  type        = string
  description = "The display name of the demo project."
  default     = "Valkey Semantic Cache Demo"
}

variable "project_number" {
  type        = string
  description = "The numeric ID of the demo project."
  default     = ""
}

variable "org_id" {
  type        = string
  description = "The Organization ID where the project resides."
  default     = ""
}

variable "gcp_account_name" {
  type        = string
  description = "The Argolis user email (admin@<ldap>.altostrat.com) receiving permissions."
  default     = ""
}

variable "deployment_service_account_name" {
  type        = string
  description = "The identity used by the runner pipeline to deploy resources."
  default     = ""
}

variable "data_location" {
  type        = string
  description = "Path to central storage buckets for large demo assets."
  default     = ""
}

variable "secret_stored_project" {
  type        = string
  description = "Project housing demo-specific secrets (passwords, keys)."
  default     = ""
}

# Memorystore Valkey Configuration Variables

variable "gcp_zone" {
  type        = string
  description = "GCP zone for Memorystore Valkey deployment."
  default     = "us-central1-a"
}

variable "valkey_version" {
  type        = string
  description = "Memorystore Valkey engine version."
  default     = "VALKEY_9_0"
}

variable "enable_redis" {
  type        = bool
  description = "Whether to use Redis engine instead of Valkey."
  default     = false
}

variable "valkey_mode" {
  type        = string
  description = "Valkey cluster mode (e.g. CLUSTER_DISABLED or CLUSTER)."
  default     = "CLUSTER_DISABLED"
}

variable "cluster_nodes" {
  type        = number
  description = "Number of cluster nodes or replicas."
  default     = 1
}

# Cloud Run & Valkey Semantic Cache Application Variables

variable "region" {
  type        = string
  description = "GCP region for Cloud Run deployment."
  default     = "us-central1"
}

variable "service_name" {
  type        = string
  description = "Name of the Cloud Run service and Valkey instance."
  default     = "valkey-semantic-cache"
}

variable "container_image" {
  type        = string
  description = "Container image URI for the Valkey Semantic Cache application. Leave empty to automatically build and push the ValkeySemanticCache source code using Cloud Build."
  default     = ""
}

variable "valkey_url" {
  type        = string
  description = "Explicit connection URL for Valkey / Redis (if set, overrides auto-discovered URL)."
  default     = ""
  sensitive   = true
}

variable "valkey_host" {
  type        = string
  description = "Fallback Valkey host IP/hostname if auto-discovery is not used."
  default     = "localhost"
}

variable "valkey_port" {
  type        = number
  description = "Valkey / Redis port."
  default     = 6379
}

variable "valkey_password" {
  type        = string
  description = "Valkey / Redis auth password if required."
  default     = ""
  sensitive   = true
}

variable "valkey_ssl" {
  type        = bool
  description = "Whether to use SSL/TLS for Valkey connection."
  default     = false
}

variable "vertexai_model" {
  type        = string
  description = "Vertex AI Gemini LLM model name."
  default     = "gemini-2.5-flash"
}

variable "vertexai_embedding_model" {
  type        = string
  description = "Vertex AI Embedding model name."
  default     = "text-embedding-004"
}

variable "semantic_cache_distance_threshold" {
  type        = string
  description = "Cosine distance threshold for semantic cache hits (0.0 to 1.0)."
  default     = "0.20"
}

variable "semantic_cache_ttl" {
  type        = number
  description = "Cache entry TTL in seconds."
  default     = 3600
}

variable "semantic_cache_index_name" {
  type        = string
  description = "Vector search index name in Valkey."
  default     = "support_concierge_cache"
}

variable "semantic_cache_prefix" {
  type        = string
  description = "Key prefix for cache entries in Valkey."
  default     = "support_concierge"
}

variable "vpc_connector" {
  type        = string
  description = "Optional Serverless VPC Access Connector ID or name if using VPC Access connector instead of Direct VPC egress."
  default     = ""
}
