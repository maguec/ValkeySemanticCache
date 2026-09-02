output "instance_id" {
  description = "ID of the deployed Memorystore Valkey instance"
  value       = google_memorystore_instance.valkey_instance.instance_id
}

output "endpoint_ip" {
  description = "Endpoint IP address of the Valkey instance"
  value       = local.endpoint_ip
}

output "endpoint_port" {
  description = "Endpoint port of the Valkey instance"
  value       = local.endpoint_port
}

output "valkey_url" {
  description = "Derived Redis/Valkey connection URL"
  value       = local.effective_valkey_url
}
