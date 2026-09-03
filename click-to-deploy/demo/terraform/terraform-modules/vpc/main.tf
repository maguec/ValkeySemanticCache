# VPC Network Configuration

resource "google_compute_network" "valkey_vpc" {
  name                    = "${var.service_name}-vpc"
  auto_create_subnetworks = false
  project                 = var.project_id
}

resource "google_compute_subnetwork" "valkey_subnet" {
  name                     = "${var.service_name}-subnet"
  ip_cidr_range            = "10.0.0.0/24"
  region                   = var.region
  network                  = google_compute_network.valkey_vpc.id
  project                  = var.project_id
  private_ip_google_access = true
}

resource "google_network_connectivity_service_connection_policy" "memorystore_policy" {
  name          = "${var.service_name}-scp"
  location      = var.region
  service_class = "gcp-memorystore"
  network       = google_compute_network.valkey_vpc.id
  project       = var.project_id

  psc_config {
    subnetworks = [google_compute_subnetwork.valkey_subnet.id]
  }
}
