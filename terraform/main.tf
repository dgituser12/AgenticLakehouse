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

# --- 1. IDENTITY & ACCESS (Control Plane) ---

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

# Grant read access to BigQuery
resource "google_project_iam_member" "bq_data_viewer" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}


# --- 2. GOOGLE CLOUD LAKEHOUSE INFRASTRUCTURE (Data Plane) ---

# Provision the REST-based Lakehouse Runtime Catalog (GA as of April 2026)
resource "google_bigquery_connection" "lakehouse_rest_catalog" {
  connection_id = "swiftroute-rest-catalog"
  location      = var.region
  friendly_name = "REST-based Lakehouse Runtime Catalog Connection"
  
  # Establishes the connection as an open Apache Iceberg REST catalog interface
  aws {
    # Stub config, configured as local GCS Iceberg endpoint on GCP
    iam_role_id = "arn:aws:iam::123456789012:role/IcebergRESTCatalogRole"
  }
}


# --- 3. GOVERNANCE POLICIES (Central Governance & Security) ---

# Provision the Dataplex Taxonomy for the Knowledge Catalog
resource "google_dataplex_taxonomy" "governance_taxonomy" {
  project      = var.project_id
  location     = var.region
  display_name = "SwiftRoute Security Classification"
  description  = "Taxonomy for governing logistics and customer data"
}

# Provision a Policy Tag for Column-Level security (e.g., masking customer_id)
resource "google_dataplex_policy_tag" "pii_tag" {
  taxonomy     = google_dataplex_taxonomy.governance_taxonomy.id
  display_name = "PII_HIGH"
  description  = "Policy tag representing highly sensitive customer identifiers"
}
