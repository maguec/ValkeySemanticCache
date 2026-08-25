# Local Variable Mapping for Guaranteed Regional Consistency
locals {
  target_project_id = var.gcp_project_id != "" ? var.gcp_project_id : var.project_id

  # Target region prioritizes var.region if specified, otherwise derives from var.gcp_zone
  target_region = var.region != "" ? var.region : (var.gcp_zone != "" ? join("-", slice(split("-", var.gcp_zone), 0, 2)) : "europe-west8")

  default_container_image = "${local.target_region}-docker.pkg.dev/${local.target_project_id}/${var.service_name}-repo/${var.service_name}:latest"

  app_container_image = (var.container_image != "" && var.container_image != "us-docker.pkg.dev/cloudrun/container/hello") ? var.container_image : local.default_container_image
}

# 0. Enable Required GCP APIs
resource "google_project_service" "gcp_services" {
  for_each = toset([
    "run.googleapis.com",
    "aiplatform.googleapis.com",
    "redis.googleapis.com",
    "memorystore.googleapis.com",
    "vpcaccess.googleapis.com",
    "compute.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "cloudbuild.googleapis.com",
    "networkconnectivity.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "orgpolicy.googleapis.com"
  ])

  project = local.target_project_id
  service = each.key

  disable_on_destroy         = false
  disable_dependent_services = false
}

# 1. VPC Network Configuration (Region: local.target_region)
module "vpc" {
  source       = "./terraform-modules/vpc"
  project_id   = local.target_project_id
  region       = local.target_region
  service_name = var.service_name

  depends_on = [google_project_service.gcp_services]
}

# 2. Memorystore for Valkey Instance Creation (Region: local.target_region)
module "valkey" {
  source                       = "./terraform-modules/valkey"
  project_id                   = local.target_project_id
  region                       = local.target_region
  service_name                 = var.service_name
  valkey_version               = var.valkey_version
  valkey_mode                  = var.valkey_mode
  cluster_nodes                = var.cluster_nodes
  network_id                   = module.vpc.network_id
  service_connection_policy_id = module.vpc.service_connection_policy_id
  explicit_valkey_url          = var.valkey_url
}

# 3. Artifact Registry Repository (Region: local.target_region)
module "artifact_registry" {
  source       = "./terraform-modules/artifact_registry"
  project_id   = local.target_project_id
  region       = local.target_region
  service_name = var.service_name

  depends_on = [google_project_service.gcp_services]
}

# 4. Identity & IAM
module "iam" {
  source           = "./terraform-modules/iam"
  project_id       = local.target_project_id
  service_name     = var.service_name
  gcp_account_name = var.gcp_account_name

  depends_on = [google_project_service.gcp_services]
}

# 5. Build and Push Application Container Image using Cloud Build
resource "terraform_data" "build_container_image" {
  count = (var.container_image == "" || var.container_image == "us-docker.pkg.dev/cloudrun/container/hello") ? 1 : 0

  triggers_replace = [
    module.artifact_registry.repository_url,
    fileexists("${path.module}/../Dockerfile") ? filesha256("${path.module}/../Dockerfile") : filesha256("${path.module}/../../../ValkeySemanticCache/Dockerfile"),
    filesha256("${path.module}/../pyproject.toml"),
    filesha256("${path.module}/../main.py"),
    filesha256("${path.module}/../cache_service.py"),
    filesha256("${path.module}/../config.py")
  ]

  provisioner "local-exec" {
    command = "cp -n ${path.module}/../../../ValkeySemanticCache/Dockerfile ${path.module}/../Dockerfile 2>/dev/null || true; gcloud builds submit ${path.module}/.. --tag ${local.default_container_image} --project=${local.target_project_id}"
  }

  depends_on = [
    module.artifact_registry,
    module.iam
  ]
}

# 6. Cloud Run Service Deployment (Region: local.target_region)
module "run" {
  source                            = "./terraform-modules/run"
  project_id                        = local.target_project_id
  region                            = local.target_region
  service_name                      = var.service_name
  service_account_email             = module.iam.service_account_email
  container_image                   = local.app_container_image
  valkey_url                        = module.valkey.valkey_url
  valkey_host                       = module.valkey.endpoint_ip != "" ? module.valkey.endpoint_ip : var.valkey_host
  valkey_port                       = module.valkey.endpoint_port
  valkey_password                   = var.valkey_password
  valkey_ssl                        = var.valkey_ssl
  vertexai_model                    = var.vertexai_model
  vertexai_embedding_model          = var.vertexai_embedding_model
  semantic_cache_distance_threshold = var.semantic_cache_distance_threshold
  semantic_cache_ttl                = var.semantic_cache_ttl
  semantic_cache_index_name         = var.semantic_cache_index_name
  semantic_cache_prefix             = var.semantic_cache_prefix
  network_name                      = module.vpc.network_name
  subnet_name                       = module.vpc.subnet_name
  gcp_account_name                  = var.gcp_account_name

  depends_on = [
    module.valkey,
    module.artifact_registry,
    terraform_data.build_container_image
  ]
}
