variable "project_id" {
  type        = string
  description = "Google Cloud project ID."
}

variable "region" {
  type        = string
  description = "GCP region for Artifact Registry repository."
}

variable "service_name" {
  type        = string
  description = "Base service name for Artifact Registry repository ID."
}
