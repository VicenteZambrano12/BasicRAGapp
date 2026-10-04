"""HTTP Cloud Function that starts the Qdrant demo VM on demand.

Triggered directly (unauthenticated, via allUsers run.invoker — see
infra/scripts/grant_vm_starter_permissions.sh) from the public React
frontend so it can wake the Qdrant Compute Engine instance up before
calling the Cloud Run backend that depends on it.
"""

import os

import functions_framework
from google.cloud import compute_v1

_CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


@functions_framework.http
def start_demo_vm(request):
    """Entry point configured on the google_cloudfunctions2_function resource."""

    # Respond to the browser's CORS preflight request.
    if request.method == "OPTIONS":
        return ("", 204, {**_CORS_HEADERS, "Access-Control-Max-Age": "3600"})

    project_id = os.environ["PROJECT_ID"]
    zone = os.environ["VM_ZONE"]
    vm_name = os.environ["VM_NAME"]

    instances_client = compute_v1.InstancesClient()

    try:
        instance = instances_client.get(project=project_id, zone=zone, instance=vm_name)
    except Exception as exc:  # noqa: BLE001 - surfaced to the caller as a 500
        return ({"error": f"Unable to read VM status: {exc}"}, 500, _CORS_HEADERS)

    status = instance.status

    if status == "RUNNING":
        return ({"status": "already_running"}, 200, _CORS_HEADERS)

    if status in ("STOPPING", "SUSPENDING", "PROVISIONING", "STAGING"):
        return (
            {"status": status.lower(), "message": "VM is mid-transition; retry in a few seconds."},
            202,
            _CORS_HEADERS,
        )

    operation = instances_client.start(project=project_id, zone=zone, instance=vm_name)

    return (
        {"status": "starting", "operation": operation.name},
        202,
        _CORS_HEADERS,
    )
