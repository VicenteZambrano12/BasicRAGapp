terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Existing GCS bucket must already exist; this backend does not create it.
  backend "gcs" {
    bucket = "terraform_bucket_portfolio"
    prefix = "basic_rag_app_tfstate"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
