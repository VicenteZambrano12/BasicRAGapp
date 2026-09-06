# BasicRAGapp Infrastructure

This directory contains the reusable Terraform modules and production environment configuration for BasicRAGapp on Google Cloud.

## Structure

- `modules/` contains reusable modules for networking, Compute Engine, Cloud Storage, IAM, and service accounts.
- `environments/prod/` composes those modules into the production deployment and uses a remote GCS backend for state.

## Requirements

- Terraform `>= 1.5.0`
- Google provider `~> 5.0`
- Google Cloud credentials configured for the target project
- Terraform installed and available on `PATH`

## Deployment

```powershell
terraform -chdir=infra/environments/prod init
terraform -chdir=infra/environments/prod validate
terraform -chdir=infra/environments/prod plan -var-file=terraform.tfvars
terraform -chdir=infra/environments/prod apply -var-file=terraform.tfvars
```

Terraform modules are documented through their variable and output descriptions; this file is the single infrastructure-level guide.
