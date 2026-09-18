# Module: prod
# Purpose: Deploy the production networking, Qdrant VM, IAM identities, storage, and document objects for BasicRAGapp.
# Usage:
#   terraform -chdir=infra/environments/prod init
#   terraform -chdir=infra/environments/prod plan
locals {
  resource_labels = {
    managedby = "terraform"
    portfolio = "yes"
    project   = "basicragapp"
    env       = "prod"
  }
}

module "vpc" {
  source = "../../modules/vpc"

  project_id = var.project_id
  name       = "portfolio-demo-vpc"

  subnets = [
    {
      name          = "basic-rag-app-subnet"
      ip_cidr_range = var.vpc_subnet_cidr
      region        = var.region
    }
  ]
}

# Secret containers only - values are populated manually via gcloud/config/populate_demo_secret.py,
# never through Terraform, so they never enter the state file.
module "qdrant_api_key_secret" {
  source = "../../modules/secret_manager_secret"

  project_id = var.project_id
  secret_id  = "basicragapp-qdrant-api-key"
  labels     = local.resource_labels
}

module "gemini_api_key_secret" {
  source = "../../modules/secret_manager_secret"

  project_id = var.project_id
  secret_id  = "basicragapp-gemini-api-key"
  labels     = local.resource_labels
}

# Least-privilege service account for the qdrant VM: only logging/monitoring
# write access, no broad Compute or project-wide roles.
module "qdrant_vm_sa" {
  source = "../../modules/service_account"

  project_id   = var.project_id
  account_id   = var.qdrant_sa_id
  display_name = "Qdrant server (least privilege)"
}

module "qdrant_vm_logging" {
  source = "../../modules/project_iam_member"

  project_id = var.project_id
  role       = "roles/logging.logWriter"
  member     = "serviceAccount:${module.qdrant_vm_sa.email}"
}

module "qdrant_vm_monitoring" {
  source = "../../modules/project_iam_member"

  project_id = var.project_id
  role       = "roles/monitoring.metricWriter"
  member     = "serviceAccount:${module.qdrant_vm_sa.email}"
}

# Scoped only to the qdrant API key secret, not project-wide.
module "qdrant_vm_secret_access" {
  source = "../../modules/secret_manager_secret_iam"

  secret_id = module.qdrant_api_key_secret.name
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${module.qdrant_vm_sa.email}"
}

# Qdrant vector database server: e2-micro / Debian, running the qdrant/qdrant
# Docker image via startup script, secured with an API key fetched from Secret
# Manager at boot (never embedded in metadata or Terraform state).
module "qdrant_server" {
  source = "../../modules/compute_instance"

  project_id   = var.project_id
  name         = "qdrant-server"
  zone         = var.qdrant_zone
  machine_type = "e2-micro"
  image        = var.qdrant_image
  network      = module.vpc.self_link
  subnetwork   = module.vpc.subnet_self_links["basic-rag-app-subnet"]
  tags         = ["qdrant-server"]
  labels       = local.resource_labels

  service_account_email = module.qdrant_vm_sa.email
  service_account_scopes = [
    "https://www.googleapis.com/auth/logging.write",
    "https://www.googleapis.com/auth/monitoring.write",
    "https://www.googleapis.com/auth/cloud-platform", # required to call the Secret Manager API; IAM roles above still gate what it can actually do
  ]

  metadata_startup_script = <<-EOT
    #!/bin/bash
    set -euo pipefail
    apt-get update
    apt-get install -y docker.io curl
    systemctl enable --now docker
    ACCESS_TOKEN=$$(curl -s -H "Metadata-Flavor: Google" "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    API_KEY=$$(curl -s -H "Authorization: Bearer $${ACCESS_TOKEN}" \
      "https://secretmanager.googleapis.com/v1/${module.qdrant_api_key_secret.name}/versions/latest:access" \
      | grep -o '"data":"[^"]*' | cut -d'"' -f4 | base64 -d)
    docker rm -f qdrant || true
    docker run -d --name qdrant --restart unless-stopped \
      -p 6333:6333 -p 6334:6334 \
      -e QDRANT__SERVICE__API_KEY="$${API_KEY}" \
      qdrant/qdrant
  EOT
}

# Only allow qdrant traffic from explicitly approved source ranges, not the open internet.
module "qdrant_firewall" {
  source = "../../modules/firewall_rule"

  project_id    = var.project_id
  name          = "allow-qdrant-server"
  network       = module.vpc.self_link
  target_tags   = ["qdrant-server"]
  source_ranges = var.qdrant_allowed_source_ranges

  allowed = [
    {
      protocol = "tcp"
      ports    = ["6333", "6334"]
    }
  ]
}

module "docs_bucket" {
  source = "../../modules/gcs_bucket"

  project_id  = var.project_id
  bucket_name = var.docs_bucket_name
  location    = var.region
  labels      = local.resource_labels
}

# Least-privilege service account dedicated to uploading assets, instead of
# reusing broad project-level credentials.
module "asset_uploader_sa" {
  source = "../../modules/service_account"

  project_id   = var.project_id
  account_id   = var.asset_uploader_sa_id
  display_name = "Asset uploader (least privilege)"
}

# Grant object-admin scoped only to the docs bucket, not project-wide storage roles.
module "asset_uploader_docs_object_admin" {
  source = "../../modules/gcs_bucket_iam"

  bucket_name = module.docs_bucket.name
  role        = "roles/storage.objectAdmin"
  member      = "serviceAccount:${module.asset_uploader_sa.email}"
}

# Upload local files into the docs bucket. Populate var.local_doc_files with
# { "<destination-object-name>" = "<local-file-path>" } entries.
module "docs_files" {
  source = "../../modules/gcs_bucket_object"

  bucket_name = module.docs_bucket.name
  files       = var.local_doc_files
}

# Docker repository for the combined frontend+backend application image.
module "app_images" {
  source = "../../modules/artifact_registry"

  project_id         = var.project_id
  location           = var.region
  repository_id      = var.app_image_repository_id
  description        = "BasicRAGapp application container images"
  labels             = local.resource_labels
  keep_version_count = 2
}

# Serverless VPC Access connector: lets Cloud Run reach the qdrant-server VM
# by internal IP, without exposing qdrant to the public internet.
module "run_vpc_connector" {
  source = "../../modules/vpc_connector"

  project_id    = var.project_id
  name          = "run-to-vpc-connector"
  region        = var.region
  network       = "portfolio-demo-vpc"
  ip_cidr_range = var.vpc_connector_cidr

  depends_on = [module.vpc]
}

# Least-privilege service account for the Cloud Run application: only the
# roles needed to read prompts/docs from GCS and call Vertex AI/Gemini.
module "app_sa" {
  source = "../../modules/service_account"

  project_id   = var.project_id
  account_id   = var.app_sa_id
  display_name = "BasicRAGapp Cloud Run app (least privilege)"
}

module "app_sa_logging" {
  source = "../../modules/project_iam_member"

  project_id = var.project_id
  role       = "roles/logging.logWriter"
  member     = "serviceAccount:${module.app_sa.email}"
}

module "app_sa_vertex_ai" {
  source = "../../modules/project_iam_member"

  project_id = var.project_id
  role       = "roles/aiplatform.user"
  member     = "serviceAccount:${module.app_sa.email}"
}

# Read-only access, scoped only to the docs bucket, not project-wide storage roles.
module "app_sa_docs_object_viewer" {
  source = "../../modules/gcs_bucket_iam"

  bucket_name = module.docs_bucket.name
  role        = "roles/storage.objectViewer"
  member      = "serviceAccount:${module.app_sa.email}"
}

# Scoped only to each secret, not project-wide.
module "app_sa_qdrant_secret_access" {
  source = "../../modules/secret_manager_secret_iam"

  secret_id = module.qdrant_api_key_secret.name
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${module.app_sa.email}"
}

module "app_sa_gemini_secret_access" {
  source = "../../modules/secret_manager_secret_iam"

  secret_id = module.gemini_api_key_secret.name
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${module.app_sa.email}"
}

# Allow the VPC connector's reserved range to reach the qdrant server, in
# addition to any explicitly approved external source ranges.
module "qdrant_firewall_from_connector" {
  source = "../../modules/firewall_rule"

  project_id    = var.project_id
  name          = "allow-qdrant-server-from-run-connector"
  network       = module.vpc.self_link
  target_tags   = ["qdrant-server"]
  source_ranges = [var.vpc_connector_cidr]

  allowed = [
    {
      protocol = "tcp"
      ports    = ["6333", "6334"]
    }
  ]
}

# Combined frontend+backend container, deployed in the same subnet/VPC as
# the qdrant server via the Serverless VPC Access connector.
module "app_service" {
  source = "../../modules/cloud_run_service"

  project_id             = var.project_id
  name                   = var.cloud_run_service_name
  location               = var.region
  image                  = var.app_container_image
  service_account_email  = module.app_sa.email
  vpc_connector_id       = module.run_vpc_connector.id
  allow_unauthenticated  = true

  env = {
    GOOGLE_CLOUD_PROJECT  = var.project_id
    GOOGLE_CLOUD_LOCATION = var.region
    LLM_MODEL             = var.llm_model
    EMBEDDING_MODEL       = var.embedding_model
    VECTOR_DB_TYPE        = "qdrant"
    QDRANT_HOST           = module.qdrant_server.network_interfaces[0].network_ip
    QDRANT_PORT           = "6333"
    GCS_BUCKET_NAME       = module.docs_bucket.name
    MODE                  = "GCP"
  }

  # Resolved from Secret Manager at container start, never as plaintext env vars.
  secret_env = {
    QDRANT_API_KEY = { secret = module.qdrant_api_key_secret.secret_id, version = "latest" }
    GEMINI_API_KEY = { secret = module.gemini_api_key_secret.secret_id, version = "latest" }
  }
}

# Demo service account for the Secret Manager access-only proof of concept.
# Not yet wired into the Cloud Run app - kept separate until explicitly connected.
module "demo_app_sa" {
  source = "../../modules/service_account"

  project_id   = var.project_id
  account_id   = var.demo_app_sa_id
  display_name = "BasicRAGapp demo secret consumer (least privilege)"
}

# Secret container only - no google_secret_manager_secret_version here.
# The secret value is populated manually via gcloud, so it never enters the
# Terraform state file.
module "demo_secret" {
  source = "../../modules/secret_manager_secret"

  project_id = var.project_id
  secret_id  = var.demo_secret_id
  labels     = local.resource_labels
}

# Grant access scoped only to this secret, not project-wide.
module "demo_secret_access" {
  source = "../../modules/secret_manager_secret_iam"

  secret_id = module.demo_secret.name
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${module.demo_app_sa.email}"
}
