# Cloud Run Service Deployment

resource "google_cloud_run_v2_service" "valkey_semantic_cache" {
  name                = var.service_name
  location            = var.region
  project             = var.project_id
  deletion_protection = false

  template {
    service_account = var.service_account_email

    containers {
      image = var.container_image

      ports {
        container_port = 8080
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }
      env {
        name  = "VALKEY_URL"
        value = var.valkey_url
      }
      env {
        name  = "VALKEY_HOST"
        value = var.valkey_host
      }
      env {
        name  = "VALKEY_PORT"
        value = tostring(var.valkey_port)
      }
      env {
        name  = "VALKEY_PASSWORD"
        value = var.valkey_password
      }
      env {
        name  = "VALKEY_SSL"
        value = tostring(var.valkey_ssl)
      }
      env {
        name  = "VERTEXAI_MODEL"
        value = var.vertexai_model
      }
      env {
        name  = "VERTEXAI_EMBEDDING_MODEL"
        value = var.vertexai_embedding_model
      }
      env {
        name  = "SEMANTIC_CACHE_DISTANCE_THRESHOLD"
        value = var.semantic_cache_distance_threshold
      }
      env {
        name  = "SEMANTIC_CACHE_TTL"
        value = tostring(var.semantic_cache_ttl)
      }
      env {
        name  = "SEMANTIC_CACHE_INDEX_NAME"
        value = var.semantic_cache_index_name
      }
      env {
        name  = "SEMANTIC_CACHE_PREFIX"
        value = var.semantic_cache_prefix
      }
    }

    # Direct VPC Egress into Valkey VPC Subnet
    vpc_access {
      network_interfaces {
        network    = var.network_name
        subnetwork = var.subnet_name
      }
      egress = "ALL_TRAFFIC"
    }
  }
}

# Grant public unauthenticated access to the Cloud Run service (if enabled)
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  count    = var.enable_public_invoker ? 1 : 0
  project  = var.project_id
  location = google_cloud_run_v2_service.valkey_semantic_cache.location
  name     = google_cloud_run_v2_service.valkey_semantic_cache.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Grant invoking user invoker permissions to call service
resource "google_cloud_run_v2_service_iam_member" "demo_invoker_access" {
  count    = var.gcp_account_name != "" ? 1 : 0
  project  = var.project_id
  location = google_cloud_run_v2_service.valkey_semantic_cache.location
  name     = google_cloud_run_v2_service.valkey_semantic_cache.name
  role     = "roles/run.invoker"
  member   = "user:${var.gcp_account_name}"
}

# Grant invoking admin user permissions to manage service (if set)
resource "google_cloud_run_v2_service_iam_member" "demo_admin_access" {
  count    = var.gcp_account_name != "" ? 1 : 0
  project  = var.project_id
  location = google_cloud_run_v2_service.valkey_semantic_cache.location
  name     = google_cloud_run_v2_service.valkey_semantic_cache.name
  role     = "roles/run.admin"
  member   = "user:${var.gcp_account_name}"
}

