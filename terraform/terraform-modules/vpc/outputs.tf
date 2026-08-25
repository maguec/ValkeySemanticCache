output "network_id" {
  value       = google_compute_network.valkey_vpc.id
  description = "The ID of the VPC network."
}

output "network_name" {
  value       = google_compute_network.valkey_vpc.name
  description = "The name of the VPC network."
}

output "subnet_id" {
  value       = google_compute_subnetwork.valkey_subnet.id
  description = "The ID of the VPC subnetwork."
}

output "subnet_name" {
  value       = google_compute_subnetwork.valkey_subnet.name
  description = "The name of the VPC subnetwork."
}

output "service_connection_policy_id" {
  value       = google_network_connectivity_service_connection_policy.memorystore_policy.id
  description = "The ID of the Service Connection Policy."
}
