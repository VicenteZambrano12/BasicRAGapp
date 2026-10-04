#!/usr/bin/env bash
# Grants the IAM permissions the Terraform config in
# infra/environments/prod intentionally does NOT manage:
#
#   a) lets the Cloud Function's runtime SA start/inspect the Qdrant VM
#      (roles/compute.instanceAdmin.v1, or a tighter custom role)
#   b) lets allUsers invoke the (2nd gen) Cloud Function so the public
#      React frontend can call it unauthenticated
#
# No dedicated service account is created for the function — it runs as
# the shared portfolio-repo-sa@basicrahgapp.iam.gserviceaccount.com
# identity, which already has roles/compute.instanceAdmin.v1 (granted
# earlier for a different purpose), so step (a) below is typically a
# no-op here. Run this once after `terraform apply` has created the
# Cloud Function. Requires the gcloud CLI, authenticated as a principal
# with Owner/IAM Admin + Cloud Functions Admin on the project.
#
# NOTE on the three *deploying* identities involved (none of these is the
# function's runtime SA above — they're who/what runs `terraform apply`
# and the build behind it):
#
#   basicragapp-app@basicrahgapp.iam.gserviceaccount.com is this repo's
#   actual Terraform/CI identity (its Workload Identity Federation binding
#   is scoped to the BasicRAGapp GitHub repo — portfolio-repo-sa's WIF
#   binding is scoped to PersonalPortfolioRepo instead, so it can NOT
#   authenticate from here despite being used elsewhere in this project).
#   It was granted (one-time, project-level), in addition to roles it
#   already had (storage.admin, run.admin, compute.admin, etc.):
#     roles/cloudfunctions.admin       (create/update the 2nd-gen function)
#     roles/cloudbuild.builds.editor   (2nd-gen function deploys run a
#                                        Cloud Build job under the hood)
#
#   31049783945-compute@developer.gserviceaccount.com (this project's
#   default Compute Engine SA) is the identity Cloud Build itself actually
#   runs 2nd-gen function builds as (not the legacy
#   31049783945@cloudbuild.gserviceaccount.com SA, which already had
#   cloudbuild.builds.builder and was NOT the problem). It had zero IAM
#   roles, causing "Could not build the function due to a missing
#   permission on the build service account". Granted:
#     roles/cloudbuild.builds.builder
#     roles/logging.logWriter
#
# The cloudfunctions.googleapis.com, cloudbuild.googleapis.com and
# eventarc.googleapis.com APIs were also enabled on the project (they
# were disabled by default and Terraform does not enable them itself).
# Re-run equivalent of:
#   gcloud services enable cloudfunctions.googleapis.com \
#     cloudbuild.googleapis.com eventarc.googleapis.com \
#     --project=basicrahgapp
#   gcloud projects add-iam-policy-binding basicrahgapp \
#     --member="serviceAccount:basicragapp-app@basicrahgapp.iam.gserviceaccount.com" \
#     --role="roles/cloudfunctions.admin" --condition=None
#   gcloud projects add-iam-policy-binding basicrahgapp \
#     --member="serviceAccount:basicragapp-app@basicrahgapp.iam.gserviceaccount.com" \
#     --role="roles/cloudbuild.builds.editor" --condition=None
#   gcloud projects add-iam-policy-binding basicrahgapp \
#     --member="serviceAccount:31049783945-compute@developer.gserviceaccount.com" \
#     --role="roles/cloudbuild.builds.builder" --condition=None
#   gcloud projects add-iam-policy-binding basicrahgapp \
#     --member="serviceAccount:31049783945-compute@developer.gserviceaccount.com" \
#     --role="roles/logging.logWriter" --condition=None
#
# Usage:
#   PROJECT_ID=my-project \
#   FUNCTION_NAME=start-qdrant-vm \
#   REGION=europe-southwest1 \
#   SA_EMAIL=portfolio-repo-sa@my-project.iam.gserviceaccount.com \
#   ./grant_vm_starter_permissions.sh

set -euo pipefail

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID to your GCP project id}"
REGION="${REGION:?Set REGION to the Cloud Function's region}"
FUNCTION_NAME="${FUNCTION_NAME:-start-qdrant-vm}"
# Copy this from Terraform's `qdrant_vm_starter_service_account_email` output
# (defaults to portfolio-repo-sa — the shared SA, not a dedicated one).
SA_EMAIL="${SA_EMAIL:-portfolio-repo-sa@${PROJECT_ID}.iam.gserviceaccount.com}"
USE_CUSTOM_ROLE="${USE_CUSTOM_ROLE:-false}"

echo "== a) Grant ${SA_EMAIL} permission to start/inspect the Qdrant VM =="

if [ "$USE_CUSTOM_ROLE" = "true" ]; then
  CUSTOM_ROLE_ID="qdrantVmStarter"

  # Narrower alternative to roles/compute.instanceAdmin.v1: only what the
  # Cloud Function actually calls (instances.get + instances.start).
  if ! gcloud iam roles describe "$CUSTOM_ROLE_ID" --project="$PROJECT_ID" >/dev/null 2>&1; then
    gcloud iam roles create "$CUSTOM_ROLE_ID" \
      --project="$PROJECT_ID" \
      --title="Qdrant VM Starter" \
      --description="Minimal permissions to start and read status of the Qdrant demo VM" \
      --permissions="compute.instances.start,compute.instances.get" \
      --stage=GA
  else
    gcloud iam roles update "$CUSTOM_ROLE_ID" \
      --project="$PROJECT_ID" \
      --permissions="compute.instances.start,compute.instances.get"
  fi

  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="projects/${PROJECT_ID}/roles/${CUSTOM_ROLE_ID}" \
    --condition=None
else
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/compute.instanceAdmin.v1" \
    --condition=None
fi

echo "== b) Grant allUsers roles/run.invoker on the Cloud Function (public, unauthenticated) =="

# 2nd gen Cloud Functions are backed by Cloud Run, so the invoker binding is
# applied to the underlying Cloud Run service. `gcloud functions` exposes a
# dedicated helper for this; falling back to `gcloud run` works identically.
if gcloud functions add-invoker-policy-binding "$FUNCTION_NAME" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --member="allUsers" 2>/dev/null; then
  :
else
  gcloud run services add-iam-policy-binding "$FUNCTION_NAME" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --member="allUsers" \
    --role="roles/run.invoker"
fi

echo "Done. Public trigger URL:"
gcloud functions describe "$FUNCTION_NAME" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --gen2 \
  --format="value(serviceConfig.uri)"
