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

# Qdrant vector database server: e2-micro / Debian, running the qdrant/qdrant
# Docker image via startup script, secured with an API key.
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

  service_account_email = module.qdrant_vm_sa.email
  service_account_scopes = [
    "https://www.googleapis.com/auth/logging.write",
    "https://www.googleapis.com/auth/monitoring.write",
  ]

  metadata_startup_script = <<-EOT
    #!/bin/bash
    set -euo pipefail
    apt-get update
    apt-get install -y docker.io
    systemctl enable --now docker
    docker rm -f qdrant || true
    docker run -d --name qdrant --restart unless-stopped \
      -p 6333:6333 -p 6334:6334 \
      -e QDRANT__SERVICE__API_KEY="${var.qdrant_api_key}" \
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

# New GCS bucket for application docs.
module "docs_bucket" {
  source = "../../modules/gcs_bucket"

  project_id  = var.project_id
  bucket_name = var.docs_bucket_name
  location    = var.region
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
