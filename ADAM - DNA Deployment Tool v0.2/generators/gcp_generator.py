"""
Google Cloud Deployment Generator for ADAM DNA Specification.
Generates Terraform templates for GCP deployment.
"""

from typing import Dict, Any
from .base_generator import BaseGenerator

class GCPGenerator(BaseGenerator):
    PLATFORM_NAME = "gcp"
    PLATFORM_DISPLAY = "Google Cloud Platform"

    def generate_iac(self) -> Dict[str, str]:
        files = {}
        files[self.write_file("terraform/main.tf", self._terraform_main())] = "Terraform root module"
        files[self.write_file("terraform/variables.tf", self._terraform_variables())] = "Terraform variables"
        files[self.write_file("terraform/modules/gke/main.tf", self._tf_gke())] = "GKE cluster module"
        files[self.write_file("terraform/modules/spanner/main.tf", self._tf_spanner())] = "Spanner (CORE Graph)"
        files[self.write_file("terraform/modules/gcs-evidence/main.tf", self._tf_gcs_evidence())] = "GCS Flight Recorder"
        files[self.write_file("terraform/modules/vertex-ai/main.tf", self._tf_vertex_ai())] = "Vertex AI services"
        return files

    def generate_configs(self) -> Dict[str, str]:
        files = {}
        files[self.write_json("config/adam-gcp-config.json", self._gcp_config())] = "GCP deployment config"
        files[self.write_yaml("config/adam-gcp-values.yaml", self._gcp_values())] = "GCP Helm values"
        return files

    def _terraform_main(self) -> str:
        return f'''{self.header_comment("#")}

terraform {{
  required_version = ">= 1.5.0"
  required_providers {{
    google = {{
      source  = "hashicorp/google"
      version = "~> 5.10"
    }}
    google-beta = {{
      source  = "hashicorp/google-beta"
      version = "~> 5.10"
    }}
  }}
  backend "gcs" {{
    bucket = "adam-tfstate-{self.company_slug}"
    prefix = "terraform/state"
  }}
}}

provider "google" {{
  project = var.project_id
  region  = var.primary_region
}}

provider "google-beta" {{
  project = var.project_id
  region  = var.primary_region
}}

# ============================================================
# VPC Network - ADAM sovereignty boundaries
# ============================================================
resource "google_compute_network" "adam" {{
  name                    = "adam-vpc-{self.company_slug}"
  auto_create_subnetworks = false
  project                 = var.project_id
}}

resource "google_compute_subnetwork" "governance" {{
  name          = "adam-governance-subnet"
  ip_cidr_range = "10.1.0.0/16"
  region        = var.primary_region
  network       = google_compute_network.adam.id
  private_ip_google_access = true
}}

resource "google_compute_subnetwork" "agents" {{
  name          = "adam-agents-subnet"
  ip_cidr_range = "10.2.0.0/16"
  region        = var.primary_region
  network       = google_compute_network.adam.id

  secondary_ip_range {{
    range_name    = "gke-pods"
    ip_cidr_range = "10.10.0.0/14"
  }}
  secondary_ip_range {{
    range_name    = "gke-services"
    ip_cidr_range = "10.20.0.0/16"
  }}
}}

# ============================================================
# Modules
# ============================================================
module "gke" {{
  source       = "./modules/gke"
  project_id   = var.project_id
  region       = var.primary_region
  company_slug = "{self.company_slug}"
  network      = google_compute_network.adam.name
  subnetwork   = google_compute_subnetwork.agents.name
}}

module "spanner" {{
  source       = "./modules/spanner"
  project_id   = var.project_id
  company_slug = "{self.company_slug}"
}}

module "gcs_evidence" {{
  source       = "./modules/gcs-evidence"
  project_id   = var.project_id
  region       = var.primary_region
  company_slug = "{self.company_slug}"
}}

module "vertex_ai" {{
  source       = "./modules/vertex-ai"
  project_id   = var.project_id
  region       = var.primary_region
  company_slug = "{self.company_slug}"
}}
'''

    def _terraform_variables(self) -> str:
        return f'''{self.header_comment("#")}

variable "project_id" {{
  description = "GCP Project ID for ADAM deployment"
  type        = string
}}

variable "primary_region" {{
  description = "Primary GCP region"
  type        = string
  default     = "europe-west1"
}}

variable "environment" {{
  description = "Deployment environment"
  type        = string
  default     = "production"
}}
'''

    def _tf_gke(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM GKE Module - Container orchestration for agent mesh

variable "project_id" {{ type = string }}
variable "region" {{ type = string }}
variable "company_slug" {{ type = string }}
variable "network" {{ type = string }}
variable "subnetwork" {{ type = string }}

resource "google_container_cluster" "adam" {{
  name     = "gke-adam-${{var.company_slug}}"
  location = var.region
  project  = var.project_id

  remove_default_node_pool = true
  initial_node_count       = 1

  network    = var.network
  subnetwork = var.subnetwork

  ip_allocation_policy {{
    cluster_secondary_range_name  = "gke-pods"
    services_secondary_range_name = "gke-services"
  }}

  private_cluster_config {{
    enable_private_nodes    = true
    enable_private_endpoint = true
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }}

  workload_identity_config {{
    workload_pool = "${{var.project_id}}.svc.id.goog"
  }}

  release_channel {{
    channel = "STABLE"
  }}
}}

# Governance Node Pool
resource "google_container_node_pool" "governance" {{
  name       = "adam-governance"
  cluster    = google_container_cluster.adam.name
  location   = var.region
  project    = var.project_id

  autoscaling {{
    min_node_count = 3
    max_node_count = 10
  }}

  node_config {{
    machine_type = "n2-standard-16"
    disk_size_gb = 256
    disk_type    = "pd-ssd"

    labels = {{
      "adam/plane" = "governance"
      "adam/tier"  = "sovereign"
    }}

    workload_metadata_config {{
      mode = "GKE_METADATA"
    }}
  }}
}}

# Agent Mesh Node Pool
resource "google_container_node_pool" "agents" {{
  name       = "adam-agents"
  cluster    = google_container_cluster.adam.name
  location   = var.region
  project    = var.project_id

  autoscaling {{
    min_node_count = 5
    max_node_count = 50
  }}

  node_config {{
    machine_type = "n2-standard-32"
    disk_size_gb = 512
    labels = {{ "adam/plane" = "execution" }}
  }}
}}

# GPU Node Pool
resource "google_container_node_pool" "gpu" {{
  name       = "adam-gpu"
  cluster    = google_container_cluster.adam.name
  location   = var.region
  project    = var.project_id

  autoscaling {{
    min_node_count = 2
    max_node_count = 20
  }}

  node_config {{
    machine_type = "a2-highgpu-4g"
    disk_size_gb = 1024

    guest_accelerator {{
      type  = "nvidia-tesla-a100"
      count = 4
    }}

    labels = {{ "adam/plane" = "execution", "adam/agent-type" = "gpu" }}
  }}
}}
'''

    def _tf_spanner(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM Spanner - CORE Graph (distributed, strongly consistent)

variable "project_id" {{ type = string }}
variable "company_slug" {{ type = string }}

resource "google_spanner_instance" "adam_core" {{
  name         = "adam-core-${{var.company_slug}}"
  project      = var.project_id
  config       = "regional-europe-west1"
  display_name = "ADAM CORE Engine - ${{var.company_slug}}"
  num_nodes    = 3

  labels = {{
    "adam-component" = "core-graph"
    "adam-tier"      = "sovereign"
  }}
}}

resource "google_spanner_database" "core_graph" {{
  instance = google_spanner_instance.adam_core.name
  name     = "adam-core-graph"
  project  = var.project_id

  ddl = [
    "CREATE TABLE Doctrine (id STRING(36) NOT NULL, type STRING(100), content JSON, version INT64, created_at TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true)) PRIMARY KEY (id)",
    "CREATE TABLE Culture (id STRING(36) NOT NULL, dimension STRING(100), value JSON, priority INT64) PRIMARY KEY (id)",
    "CREATE TABLE Objectives (id STRING(36) NOT NULL, type STRING(50), description STRING(MAX), target JSON, owner STRING(100)) PRIMARY KEY (id)",
    "CREATE TABLE Rules (id STRING(36) NOT NULL, type STRING(50), severity STRING(20), description STRING(MAX), enforcement JSON) PRIMARY KEY (id)",
    "CREATE TABLE Expectations (id STRING(36) NOT NULL, behavior STRING(MAX), exception_tolerance FLOAT64, exception_count INT64) PRIMARY KEY (id)",
    "CREATE TABLE IntentObjects (id STRING(36) NOT NULL, source JSON, desired_outcomes JSON, constraints JSON, boss_score FLOAT64, status STRING(50), created_at TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true)) PRIMARY KEY (id)",
    "CREATE TABLE BOSSScores (id STRING(36) NOT NULL, intent_id STRING(36), dimensions JSON, composite_score FLOAT64, routing_tier STRING(20), scored_at TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true)) PRIMARY KEY (id)",
    "CREATE TABLE FlightRecorder (id STRING(36) NOT NULL, action_id STRING(36), evidence JSON, hash_chain STRING(MAX), created_at TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true)) PRIMARY KEY (id)",
  ]

  deletion_protection = true
}}
'''

    def _tf_gcs_evidence(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM GCS - Flight Recorder (versioned, retention-locked)

variable "project_id" {{ type = string }}
variable "region" {{ type = string }}
variable "company_slug" {{ type = string }}

resource "google_storage_bucket" "flight_recorder" {{
  name          = "adam-flight-recorder-${{var.company_slug}}"
  location      = upper(var.region)
  project       = var.project_id
  storage_class = "STANDARD"
  force_destroy = false

  versioning {{ enabled = true }}

  retention_policy {{
    retention_period = 220752000  # 7 years in seconds
    is_locked        = true
  }}

  uniform_bucket_level_access = true

  encryption {{
    default_kms_key_name = google_kms_crypto_key.evidence.id
  }}
}}

resource "google_kms_key_ring" "adam" {{
  name     = "adam-keyring-${{var.company_slug}}"
  location = var.region
  project  = var.project_id
}}

resource "google_kms_crypto_key" "evidence" {{
  name     = "adam-evidence-key"
  key_ring = google_kms_key_ring.adam.id
  rotation_period = "7776000s"  # 90 days
}}
'''

    def _tf_vertex_ai(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM Vertex AI - Agent reasoning services

variable "project_id" {{ type = string }}
variable "region" {{ type = string }}
variable "company_slug" {{ type = string }}

resource "google_vertex_ai_endpoint" "adam_reasoning" {{
  name         = "adam-reasoning-${{var.company_slug}}"
  display_name = "ADAM Reasoning Endpoint"
  location     = var.region
  project      = var.project_id
}}
'''

    def _gcp_config(self) -> Dict[str, Any]:
        return {
            "adam_deployment": {
                "platform": "gcp",
                "company": self.company_name,
                "version": "1.1",
                "generated": self.timestamp,
            },
            "governance_plane": {
                "core_engine": {"database": "spanner", "nodes": 3, "config": "regional"},
                "flight_recorder": {"storage": "gcs-retention-locked", "retention_years": 7},
                "crypto_vault": {"service": "cloud-kms"},
            },
            "agent_mesh": {
                "orchestration": "gke",
                "total_agents": self.total_agents(),
                "node_pools": {
                    "governance": {"machine_type": "n2-standard-16", "min": 3, "max": 10},
                    "agents": {"machine_type": "n2-standard-32", "min": 5, "max": 50},
                    "gpu": {"machine_type": "a2-highgpu-4g", "min": 2, "max": 20},
                },
            },
            "ai_services": {
                "provider": "vertex-ai",
                "models": {
                    "reasoning": "gemini-2.0-pro",
                    "execution": "gemini-2.0-flash",
                    "deep_reasoning": "gemini-2.0-pro",
                },
            },
            "boss_config": {
                "dimensions": self.get_boss_dimensions(),
                "thresholds": self.get_boss_thresholds(),
            },
        }

    def _gcp_values(self) -> Dict[str, Any]:
        return {
            "global": {"company": self.company_name, "platform": "gcp"},
            "coreEngine": {"spanner": {"enabled": True, "nodes": 3}},
            "bossScoring": {"dimensions": self.get_boss_dimensions(), "thresholds": self.get_boss_thresholds()},
            "agentMesh": {"replicaCount": 3},
        }
