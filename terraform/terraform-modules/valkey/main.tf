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

  desired_psc_auto_connections {
    network    = var.network_id
    project_id = var.project_id
  }

  persistence_config {
    mode = "DISABLED"
  }
}

locals {
  # Flatten PSC auto connections to find the primary IP
  primary_connections = flatten([
    for ep in google_memorystore_instance.valkey_instance.endpoints : [
      for conn in ep.connections : [
        for psc in conn.psc_auto_connection : psc
        if psc.connection_type == "CONNECTION_TYPE_PRIMARY"
      ]
    ]
  ])

  endpoint_ip = length(local.primary_connections) > 0 ? local.primary_connections[0].ip_address : (
    length(google_memorystore_instance.valkey_instance.discovery_endpoints) > 0 ? google_memorystore_instance.valkey_instance.discovery_endpoints[0].address : ""
  )

  endpoint_port = length(local.primary_connections) > 0 ? local.primary_connections[0].port : (
    length(google_memorystore_instance.valkey_instance.discovery_endpoints) > 0 ? google_memorystore_instance.valkey_instance.discovery_endpoints[0].port : 6379
  )

  auto_valkey_url      = local.endpoint_ip != "" ? "redis://${local.endpoint_ip}:${local.endpoint_port}/0" : ""
  effective_valkey_url = var.explicit_valkey_url != "" ? var.explicit_valkey_url : local.auto_valkey_url
}

