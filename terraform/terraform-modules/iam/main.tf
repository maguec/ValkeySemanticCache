# Identity & IAM Configuration

resource "google_service_account" "cloud_run_sa" {
  account_id   = "${var.service_name}-sa"
  display_name = "Service Account for Valkey Semantic Cache Cloud Run"
  project      = var.project_id
}

# Grant Vertex AI User role to Cloud Run Service Account
resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Allow all policy member domains (unauthenticated allUsers) at project level
resource "google_project_organization_policy" "allowed_policy_member_domains" {
  project    = var.project_id
  constraint = "constraints/iam.allowedPolicyMemberDomains"

  list_policy {
    allow {
      all = true
    }
  }
}
# Fetch project metadata for project number
data "google_project" "project" {
  project_id = var.project_id
}

# Grant Storage Object Viewer to Cloud Build and Compute default SAs for staging source tarballs
resource "google_project_iam_member" "compute_storage_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_storage_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}

# Grant Artifact Registry Writer to Cloud Build and Compute default SAs
resource "google_project_iam_member" "compute_ar_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_ar_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}

# Grant Cloud Build Editor and Storage Admin to gcp_account_name if specified
resource "google_project_iam_member" "user_cloudbuild_editor" {
  count   = var.gcp_account_name != "" ? 1 : 0
  project = var.project_id
  role    = "roles/cloudbuild.builds.editor"
  member  = "user:${var.gcp_account_name}"
}

resource "google_project_iam_member" "user_storage_admin" {
  count   = var.gcp_account_name != "" ? 1 : 0
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "user:${var.gcp_account_name}"
}
