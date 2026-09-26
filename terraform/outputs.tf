# terraform/outputs.tf

output "agent_service_account_email" {
  value       = google_service_account.agent_sa.email
  description = "The email of the provisioned service account to attach to the Agent Runtime."
}
