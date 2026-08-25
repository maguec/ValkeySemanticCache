variable "project_id" {
  type        = string
  description = "Google Cloud project ID."
}

variable "service_name" {
  type        = string
  description = "Base service name for Service Account creation."
}

variable "gcp_account_name" {
  type        = string
  description = "User account name receiving permissions."
  default     = ""
}
