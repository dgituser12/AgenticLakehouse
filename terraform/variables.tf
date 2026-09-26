# terraform/variables.tf

variable "project_id" {
  type        = string
  description = "The GCP Project ID where resources will be provisioned."
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "The target GCP region."
}

variable "spark_jobs_bucket" {
  type        = string
  description = "The name of the GCS bucket where agent-generated PySpark scripts will be stored."
}
