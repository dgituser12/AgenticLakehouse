# terraform/main.tf

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Create the dedicated Service Account for the Agent Runtime
resource "google_service_account" "agent_sa" {
  account_id   = "swiftroute-agent-identity"
  display_name = "SwiftRoute Agent SPIFFE Workload Identity"
}

# Grant the agent permission to use the Knowledge Catalog for data discovery
resource "google_project_iam_member" "catalog_viewer" {
  project = var.project_id
  role    = "roles/dataplex.catalogViewer"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}

# Grant the agent permission to submit serverless Spark jobs
resource "google_project_iam_member" "spark_developer" {
  project = var.project_id
  role    = "roles/dataproc.developer"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}

# Grant the agent query and job execution permissions on BigQuery
resource "google_project_iam_member" "bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}

# Grant read access to the specific Lakehouse dataset containing our Iceberg tables
resource "google_project_iam_member" "bq_data_viewer" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}

# Grant read/write permissions to the Spark Job GCS bucket
resource "google_storage_bucket_iam_member" "spark_bucket_writer" {
  bucket = var.spark_jobs_bucket
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.agent_sa.email}"
}
