# Artifact Registry Docker Repository Configuration

resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = "${var.service_name}-repo"
  description   = "Docker repository for ${var.service_name} in ${var.region}"
  format        = "DOCKER"
  project       = var.project_id
}
