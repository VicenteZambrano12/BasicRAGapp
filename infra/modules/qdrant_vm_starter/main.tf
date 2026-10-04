# --- 1. Runtime identity for the startup Cloud Function ---
# No service account is created here. The function runs as the existing
# portfolio-repo-sa (var.service_account_email) — the same identity used
# for Cloud Run deployments across this repo, and the identity Terraform/CI
# itself runs as. IAM bindings (compute.instanceAdmin.v1 on the project,
# run.invoker for allUsers on the function) are intentionally NOT managed
# here — see infra/scripts/grant_vm_starter_permissions.sh for the
# equivalent gcloud commands.

# --- 2. Source code packaging & Cloud Storage ---
resource "google_storage_bucket" "function_source" {
  project                     = var.project_id
  name                        = "${var.project_id}-qdrant-vm-starter-src"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = true
  labels                      = merge(var.common_labels, { component = "qdrant-vm-starter" })
}

data "archive_file" "start_vm_source" {
  type        = "zip"
  source_dir  = "${path.module}/functions/start_vm"
  output_path = "${path.module}/.build/start_vm.zip"
}

resource "google_storage_bucket_object" "start_vm_source" {
  name   = "start_vm-${data.archive_file.start_vm_source.output_md5}.zip"
  bucket = google_storage_bucket.function_source.name
  source = data.archive_file.start_vm_source.output_path
}

# --- 3. Cloud Function (2nd gen) ---
resource "google_cloudfunctions2_function" "start_vm" {
  project  = var.project_id
  name     = var.function_name
  location = var.region

  build_config {
    runtime     = "python312"
    entry_point = "start_demo_vm"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.start_vm_source.name
      }
    }
  }

  service_config {
    max_instance_count             = 3
    min_instance_count             = 0
    available_memory               = "256M"
    timeout_seconds                = 60
    ingress_settings               = "ALLOW_ALL"
    all_traffic_on_latest_revision = true
    service_account_email          = var.service_account_email

    environment_variables = {
      PROJECT_ID = var.project_id
      VM_ZONE    = var.zone
      VM_NAME    = var.vm_name
    }
  }

  labels = merge(var.common_labels, { component = "qdrant-vm-starter" })
}
