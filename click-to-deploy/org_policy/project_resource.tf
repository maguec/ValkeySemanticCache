###################################################################################################################
# CRITICAL: DO NOT MODIFY THIS FILE                                                                               #
# This file contains the logic to apply organization policies and enable APIs based on the project_config.json.   #
# Users should ONLY edit 'project_config.json' to customize their demo prerequisites.                             #
###################################################################################################################

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 6.0.0"
    }
  }
}

variable "project_id" {
  description = "project id in which demo deploy"
}

// --- Data Source: Read Configuration ---
locals {
  // Reads the data from the user-defined config.json file
  config = jsondecode(file("project_config.json"))
}

// --- Resource 1: Organization Policies ---
resource "google_org_policy_policy" "dynamic_constraints" {
  // Iterates over the "constraints" array from config.json
  for_each = { for item in local.config.constraints : item.constraint => item }
  parent   = "projects/${var.project_id}"
  name     = "projects/${var.project_id}/policies/${replace(each.value.constraint, "constraints/", "")}"

  depends_on = [
    google_project_service.cloudresourcemanager,
    google_project_service.enabled_apis
  ]

  spec {
    // List constraint rules
    dynamic "rules" {
      for_each = each.value.policy_type == "list" && lookup(each.value, "allow_all", false) == true ? [each.value] : []
      content {
        allow_all = "TRUE"
      }
    }

    dynamic "rules" {
      for_each = each.value.policy_type == "list" && lookup(each.value, "deny_all", false) == true ? [each.value] : []
      content {
        deny_all = "TRUE"
      }
    }

    dynamic "rules" {
      for_each = each.value.policy_type == "list" && (length(lookup(each.value, "allowed_values", [])) > 0 || length(lookup(each.value, "denied_values", [])) > 0) ? [each.value] : []
      content {
        values {
          allowed_values = lookup(each.value, "allowed_values", [])
          denied_values  = lookup(each.value, "denied_values", [])
        }
      }
    }

    // Boolean constraint rule
    dynamic "rules" {
      for_each = each.value.policy_type == "boolean" ? [each.value] : []
      content {
        enforce = lookup(each.value, "enforced", false) == true ? "TRUE" : "FALSE"
      }
    }
  }
}

// --- Resource 2a: Prerequisite API Service (Cloud Resource Manager) ---
resource "google_project_service" "cloudresourcemanager" {
  project = var.project_id
  service = "cloudresourcemanager.googleapis.com"

  disable_on_destroy         = false
  disable_dependent_services = false
}

// --- Resource 2b: Remaining API Services ---
resource "google_project_service" "enabled_apis" {
  for_each = toset([
    for api in local.config.apis_to_enable : api if api != "" && api != null && api != "cloudresourcemanager.googleapis.com"
  ])

  project = var.project_id
  service = each.key

  disable_on_destroy         = false
  disable_dependent_services = false

  depends_on = [google_project_service.cloudresourcemanager]
}


