# Module: vpc_connector
# Purpose: Create a Serverless VPC Access connector so Cloud Run (or other
# serverless products) can reach resources by internal IP inside an existing VPC.
# Usage:
#   module "connector" {
#     source     = "./modules/vpc_connector"
#     project_id = var.project_id
#     name       = "run-to-vpc"
#     region     = var.region
#     network    = module.vpc.name
#     ip_cidr_range = "10.10.1.0/28"
#   }
resource "google_vpc_access_connector" "this" {
  project       = var.project_id
  name          = var.name
  region        = var.region
  network       = var.network
  ip_cidr_range = var.ip_cidr_range
  min_instances = var.min_instances
  max_instances = var.max_instances
  machine_type  = var.machine_type
}
