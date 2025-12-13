terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.51.0"
    }
  }
}

variable "project_id" { description = "GCP Project ID" }
variable "region" { default = "us-central1" }

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable APIs
resource "google_project_service" "run_api" {
  service = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifact_registry" {
  service = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

# Cloud Run Service
resource "google_cloud_run_service" "default" {
  name     = "event-processor"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/event-processor:latest"
        env {
            name = "TARGET"
            value = "PubSub"
        }
      }
    }
  }

  traffic {
    percent = 100
    latest_revision = true
  }

  depends_on = [google_project_service.run_api]
}

# Allow unauthenticated invocations (for demo purposes)
resource "google_cloud_run_service_iam_member" "noauth" {
  service  = google_cloud_run_service.default.name
  location = google_cloud_run_service.default.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "url" {
  value = google_cloud_run_service.default.status[0].url
}
