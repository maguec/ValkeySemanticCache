output "service_url" {
  description = "The URL of the deployed Cloud Run service"
  value       = module.run.service_url
}

output "service_name" {
  description = "The name of the deployed Cloud Run service"
  value       = module.run.service_name
}

output "valkey_instance_id" {
  description = "The ID of the deployed Memorystore Valkey instance"
  value       = module.valkey.instance_id
}

output "valkey_endpoint_ip" {
  description = "The Endpoint IP address of the deployed Memorystore Valkey instance"
  value       = module.valkey.endpoint_ip
}

output "valkey_url" {
  description = "The Redis/Valkey connection URL injected into Cloud Run"
  value       = module.valkey.valkey_url
  sensitive   = true
}

output "artifact_registry_url" {
  description = "The base URL for the regional Artifact Registry Docker repository"
  value       = module.artifact_registry.repository_url
}

output "service_account_email" {
  description = "The email of the Cloud Run service account"
  value       = module.iam.service_account_email
}
