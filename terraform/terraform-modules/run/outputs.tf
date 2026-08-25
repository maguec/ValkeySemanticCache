output "service_url" {
  description = "The URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.valkey_semantic_cache.uri
}

output "service_name" {
  description = "The name of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.valkey_semantic_cache.name
}
