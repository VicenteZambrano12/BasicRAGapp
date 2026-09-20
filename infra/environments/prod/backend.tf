# NOTE: This GCS bucket was provisioned manually via gcloud (not managed by Terraform).
terraform {
  backend "gcs" {
    bucket = "terraform-bucket-portfolio"
    prefix = "basic_rag_app_tfstate"
  }
}
