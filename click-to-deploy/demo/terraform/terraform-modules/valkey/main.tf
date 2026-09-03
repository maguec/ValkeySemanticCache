# Memorystore for Valkey Instance Creation

resource "google_memorystore_instance" "valkey_instance" {
  instance_id = var.service_name
  project     = var.project_id
  location    = var.region

  engine_version = var.valkey_version
  mode           = var.valkey_mode
  node_type      = "SHARED_CORE_NANO"
  shard_count    = 1

  replica_count = var.cluster_nodes > 1 ? var.cluster_nodes - 1 : 0

  desired_auto_created_endpoints {
    network    = var.network_id
    project_id = var.project_id
  }

  persistence_config {
    mode = "DISABLED"
  }
}

locals {
  # Flatten all PSC connections (both auto and user created)
  all_connections = flatten([
    for ep in google_memorystore_instance.valkey_instance.endpoints : [
      for conn in ep.connections : concat(
        [for psc in conn.psc_auto_connection : psc],
        [for psc in conn.psc_connection : psc]
      )
    ]
  ])

  primary_connections = [
    for conn in local.all_connections : conn
    if conn.connection_type == "CONNECTION_TYPE_PRIMARY"
  ]

  discovery_connections = [
    for conn in local.all_connections : conn
    if conn.connection_type == "CONNECTION_TYPE_DISCOVERY"
  ]

  endpoint_ip = length(local.primary_connections) > 0 ? local.primary_connections[0].ip_address : (
    length(local.discovery_connections) > 0 ? local.discovery_connections[0].ip_address : ""
  )

  endpoint_port = length(local.primary_connections) > 0 ? local.primary_connections[0].port : (
    length(local.discovery_connections) > 0 ? local.discovery_connections[0].port : 6379
  )

  auto_valkey_url      = local.endpoint_ip != "" ? "redis://${local.endpoint_ip}:${local.endpoint_port}/0" : ""
  effective_valkey_url = var.explicit_valkey_url != "" ? var.explicit_valkey_url : local.auto_valkey_url
}


