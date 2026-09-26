# SwiftRoute Agentic Lakehouse Pipeline

A production-grade, secure, multi-engine agentic AI blueprint designed to orchestrate SQL, PySpark, and unstructured Object Table operations directly over Apache Iceberg tables in Google Cloud Lakehouse.

## Repository Structure

- `/terraform`: Provisions IAM Service Accounts and Lakehouse-specific permission bindings.
- `/data_setup`: DDL SQL scripts to seed the mock Iceberg telemetry dataset in BigQuery.
- `/agent`: ADK 2.0 application containing the core agent reasoning instructions and custom multi-engine tools.

## Setup & Deployment

### 1. Initialize the Lakehouse Dataset
Copy the SQL contents of `/data_setup/initialize_lakehouse.sql` and run them directly inside the Google Cloud Console BigQuery Editor.

### 2. Apply Infrastructure-as-Code
Navigate to `/terraform` and run Terraform to provision the security principal and grant the required IAM permissions:
```bash
cd terraform
terraform init
terraform apply -var="project_id=<YOUR_PROJECT_ID>" -var="spark_jobs_bucket=<YOUR_GCS_SPARK_BUCKET>"
