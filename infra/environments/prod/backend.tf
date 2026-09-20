terraform {
  backend "gcs" {
    bucket = "terraform_bucket_portfolio"
    prefix = "basic_rag_app_tfstate"
  }
}
