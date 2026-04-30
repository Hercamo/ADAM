# ══════════════════════════════════════════════════════════════════════════════
# ADAM AGT Light — Terraform Module Specification
# Infrastructure-as-Code outline for AGT Light deployment on Azure
# ══════════════════════════════════════════════════════════════════════════════
# This file is a SPECIFICATION OUTLINE, not a production-ready Terraform module.
# It documents the infrastructure resources that must exist before deploying
# the AGT Light Helm chart (agt-light-helm-values.yaml).
#
# Resource groups listed here are ADDITIONS to the existing ADAM infrastructure.
# The full ADAM infrastructure is defined in the main ADAM Deployment Specification
# (ADAM - AGT Light Deployment Specification.docx, Section 2).
#
# To use: Replace all placeholder values in <angle_brackets> before applying.
# Run: terraform init && terraform plan && terraform apply
#
# Version 1.1 | April 2026 | Aligned with ADAM book v1.4 (BOSS v3.2;
# 81+ Agent Mesh reference count 81 across seven canonical classes)
# ADAM AGT Light Plugin
# ══════════════════════════════════════════════════════════════════════════════

terraform {
  required_version = ">= 1.7.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
    azapi = {
      source  = "azure/azapi"
      version = "~> 1.13"
    }
  }

  # Remote state — use existing ADAM Terraform state backend
  backend "azurerm" {
    resource_group_name  = "<ADAM_TF_STATE_RG>"
    storage_account_name = "<ADAM_TF_STATE_STORAGE>"
    container_name       = "tfstate"
    key                  = "adam-agt-light.terraform.tfstate"
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy    = false
      recover_soft_deleted_key_vaults = true
    }
  }
  subscription_id = var.subscription_id
}

# ── VARIABLES ──────────────────────────────────────────────────────────────────

variable "subscription_id" {
  type        = string
  description = "Azure subscription ID for ADAM deployment"
}

variable "resource_group_name" {
  type        = string
  description = "Existing ADAM resource group name"
  default     = "rg-adam-governance"
}

variable "location" {
  type        = string
  description = "Azure region for all resources"
  default     = "eastus2"
}

variable "aks_cluster_name" {
  type        = string
  description = "Name of existing ADAM AKS cluster"
  default     = "aks-adam-governance"
}

variable "key_vault_name" {
  type        = string
  description = "Name of existing ADAM Azure Key Vault"
  default     = "kv-adam-governance"
}

variable "managed_hsm_name" {
  type        = string
  description = "Name of existing ADAM Azure Managed HSM"
  default     = "mhsm-adam-fr-signer"
}

variable "acr_name" {
  type        = string
  description = "Name of existing ADAM Azure Container Registry"
  default     = "acradamgovernance"
}

variable "agt_namespace" {
  type        = string
  description = "Kubernetes namespace for AGT Light deployment"
  default     = "adam-agt"
}

variable "environment" {
  type        = string
  description = "Deployment environment: dev | staging | production"
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "environment must be dev, staging, or production"
  }
}

variable "organization_name" {
  type        = string
  description = "Organization name used in resource naming and tagging"
}

# ── DATA SOURCES — EXISTING ADAM RESOURCES ────────────────────────────────────

data "azurerm_resource_group" "adam" {
  name = var.resource_group_name
}

data "azurerm_kubernetes_cluster" "adam" {
  name                = var.aks_cluster_name
  resource_group_name = data.azurerm_resource_group.adam.name
}

data "azurerm_key_vault" "adam" {
  name                = var.key_vault_name
  resource_group_name = data.azurerm_resource_group.adam.name
}

data "azurerm_container_registry" "adam" {
  name                = var.acr_name
  resource_group_name = data.azurerm_resource_group.adam.name
}

# ── AKS NODE POOL: AGT SERVICES ───────────────────────────────────────────────
# AGT Light deploys Agent OS sidecars across all agent pools.
# This dedicated pool hosts the AGT shared services (non-sidecar components):
# Agent Mesh, Agent Compliance, Agent Marketplace, Agent SRE, RGI-04 Adapter.
#
# Note: Agent OS is a sidecar injected into all existing agent pools.
# Only shared services need dedicated compute.

resource "azurerm_kubernetes_cluster_node_pool" "agt_services" {
  name                  = "agtservices"
  kubernetes_cluster_id = data.azurerm_kubernetes_cluster.adam.id

  # Node pool specification
  vm_size               = "Standard_D4s_v5"     # 4 vCPU, 16 GB RAM
  node_count            = 2
  min_count             = 2
  max_count             = 6
  enable_auto_scaling   = true
  os_disk_size_gb       = 128
  os_sku                = "Ubuntu"

  # Workload isolation
  node_taints = ["agt-services=true:NoSchedule"]
  node_labels = {
    "adam-node-pool"     = "agt-services"
    "adam-ring"          = "shared-services"
    "agt-os-injection"   = "enabled"             # Agent OS sidecar injected in this pool
  }

  # Availability zones for HA
  zones = ["1", "2", "3"]

  # Network configuration (inherits from cluster)
  vnet_subnet_id = data.azurerm_kubernetes_cluster.adam.default_node_pool[0].vnet_subnet_id

  tags = local.common_tags

  lifecycle {
    ignore_changes = [node_count]  # Allow autoscaler to manage node count
  }
}

# ── KEY VAULT: AGT IDENTITY KEYS ──────────────────────────────────────────────
# Ed25519 keys for AGT Agent Mesh DID identity.
# One key per agent class (not per individual agent — per-agent keys managed by Agent Mesh).
# Key operations are performed inside Key Vault — keys never exported.

resource "azurerm_key_vault_key" "agt_mesh_ed25519" {
  for_each = toset([
    "meta-governance",
    "governor-agent",
    "orchestration",
    "human-interface",
    "ai-centric-division",
    "digital-twin",
    "work-group"
  ])

  name         = "agt-mesh-${each.key}-ed25519"
  key_vault_id = data.azurerm_key_vault.adam.id
  key_type     = "EC"
  key_size     = null                 # Not applicable for Ed25519

  # Ed25519 uses curve OKP (Octet Key Pair) — represented as EC with P-256 approximation
  # in Azure Key Vault. Actual Ed25519 operations use the key via the Agent Mesh service.
  curve = "P-256K"                    # Closest available; Agent Mesh manages actual Ed25519

  key_opts = ["sign", "verify"]

  # Key rotation policy
  rotation_policy {
    automatic {
      time_before_expiry = "P30D"     # Rotate 30 days before expiry
    }
    expire_after         = "P365D"    # Keys expire annually
    notify_before_expiry = "P60D"
  }

  tags = merge(local.common_tags, {
    "adam-component"  = "agt-agent-mesh"
    "agent-class"     = each.key
    "rgi-domain"      = "RGI-02"
  })
}

# ── KEY VAULT: FLIGHT RECORDER HSM SIGNING KEY ────────────────────────────────
# This key is used by the RGI-04 adapter to sign all Flight Recorder events.
# Must be in Azure Managed HSM (not standard Key Vault) for HSM-backed signing.
# The Managed HSM itself is ADAM-sovereign infrastructure — this adds the AGT FR key.

resource "azurerm_key_vault_key" "adam_fr_signer_agt" {
  name         = "adam-fr-signer-agt-rgi04"
  key_vault_id = data.azurerm_key_vault.adam.id
  key_type     = "EC"
  curve        = "P-256"

  key_opts = ["sign", "verify"]

  # This key signs Flight Recorder events produced by the RGI-04 adapter.
  # The main FR signing key (adam-fr-signer) is managed by the core ADAM infrastructure.
  # This key is specific to AGT-bridged events to allow independent audit.

  tags = merge(local.common_tags, {
    "adam-component"  = "rgi-04-adapter"
    "adam-sovereign"  = "true"
    "rgi-domain"      = "RGI-04"
  })
}

# ── SERVICE BUS: AGT ESCALATION TOPICS ────────────────────────────────────────
# Service Bus topics for AGT-triggered BOSS escalation events.
# These supplement (do not replace) the existing ADAM escalation infrastructure.

resource "azurerm_servicebus_topic" "agt_ring_violation" {
  name         = "agt-ring-violation-events"
  namespace_id = data.azurerm_servicebus_namespace.adam.id   # Reference existing ADAM Service Bus

  # Ring violation events are high priority — short TTL, immediate consumption
  default_message_ttl              = "PT1H"   # 1 hour TTL
  max_size_in_megabytes            = 1024
  enable_batched_operations        = true
  support_ordering                 = true     # Preserve event ordering

  lifecycle {
    prevent_destroy = true
  }
}

resource "azurerm_servicebus_topic" "agt_identity_verification_failure" {
  name         = "agt-identity-verification-failures"
  namespace_id = data.azurerm_servicebus_namespace.adam.id

  default_message_ttl              = "PT4H"
  max_size_in_megabytes            = 1024
  enable_batched_operations        = true
}

resource "azurerm_servicebus_topic" "agt_unsigned_tool_attempt" {
  name         = "agt-unsigned-tool-attempts"
  namespace_id = data.azurerm_servicebus_namespace.adam.id

  default_message_ttl              = "PT4H"
  max_size_in_megabytes            = 1024
  enable_batched_operations        = true
}

# ── MONITORING: LOG ANALYTICS WORKSPACE TABLES ────────────────────────────────
# Custom tables in the existing ADAM Log Analytics workspace for AGT telemetry.
# These are addition-only — they do not replace existing ADAM tables.

resource "azapi_resource" "agt_policy_evaluations_table" {
  type      = "Microsoft.OperationalInsights/workspaces/tables@2022-10-01"
  name      = "AgtPolicyEvaluations_CL"
  parent_id = data.azurerm_log_analytics_workspace.adam.id

  body = jsonencode({
    properties = {
      schema = {
        name = "AgtPolicyEvaluations_CL"
        columns = [
          { name = "TimeGenerated",             type = "DateTime" },
          { name = "AgentId",                   type = "String" },
          { name = "IntentId",                  type = "String" },
          { name = "ActionType",                type = "String" },
          { name = "PolicyVersion",             type = "String" },
          { name = "EvaluationLatencyMs",       type = "Real" },
          { name = "RulesEvaluated",            type = "Int" },
          { name = "RulesTriggered",            type = "Int" },
          { name = "Outcome",                   type = "String" },
          { name = "BossCompositeScore",        type = "Real" },
          { name = "RoutingDecision",           type = "String" },
          { name = "ExecutionRing",             type = "Int" },
          { name = "TrustScore",                type = "Int" },
          { name = "TrustTier",                 type = "String" }
        ]
      }
      retentionInDays = 90
    }
  })
}

resource "azapi_resource" "agt_trust_events_table" {
  type      = "Microsoft.OperationalInsights/workspaces/tables@2022-10-01"
  name      = "AgtTrustEvents_CL"
  parent_id = data.azurerm_log_analytics_workspace.adam.id

  body = jsonencode({
    properties = {
      schema = {
        name = "AgtTrustEvents_CL"
        columns = [
          { name = "TimeGenerated",             type = "DateTime" },
          { name = "AgentId",                   type = "String" },
          { name = "AgentDid",                  type = "String" },
          { name = "PreviousTrustScore",        type = "Int" },
          { name = "NewTrustScore",             type = "Int" },
          { name = "TrustScoreDelta",           type = "Int" },
          { name = "TrustTier",                 type = "String" },
          { name = "AssessmentTrigger",         type = "String" },
          { name = "SuspensionTriggered",       type = "Boolean" },
          { name = "BossAdjustmentApplied",     type = "Real" }
        ]
      }
      retentionInDays = 365
    }
  })
}

# ── WORKLOAD IDENTITY: AGT COMPONENTS ─────────────────────────────────────────
# Managed Identity for each AGT component. Follows ADAM's zero-credential principle:
# no service account tokens, no stored secrets — all identity via Workload Identity.

resource "azurerm_user_assigned_identity" "agt_components" {
  for_each = toset([
    "agent-os",
    "agent-mesh",
    "agent-runtime",
    "agent-sre",
    "agent-compliance",
    "agent-marketplace",
    "rgi-adapter"
  ])

  name                = "id-agt-${each.key}-${var.environment}"
  resource_group_name = data.azurerm_resource_group.adam.name
  location            = var.location

  tags = merge(local.common_tags, {
    "agt-component" = each.key
  })
}

# Key Vault access for AGT components that need it
resource "azurerm_key_vault_access_policy" "agt_mesh_key_access" {
  key_vault_id = data.azurerm_key_vault.adam.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_user_assigned_identity.agt_components["agent-mesh"].principal_id

  key_permissions = ["Get", "Sign", "Verify"]
}

resource "azurerm_key_vault_access_policy" "rgi_adapter_key_access" {
  key_vault_id = data.azurerm_key_vault.adam.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_user_assigned_identity.agt_components["rgi-adapter"].principal_id

  key_permissions = ["Get", "Sign"]
}

# ── LOCALS ────────────────────────────────────────────────────────────────────
locals {
  common_tags = {
    "adam-framework"   = "true"
    "adam-component"   = "agt-light"
    "environment"      = var.environment
    "organization"     = var.organization_name
    "managed-by"       = "terraform"
    "version"          = "1.1"
  }
}

# ── DATA SOURCES: EXISTING ADAM INFRASTRUCTURE ────────────────────────────────
# These reference existing ADAM resources — they must be deployed before this module.

data "azurerm_client_config" "current" {}

data "azurerm_servicebus_namespace" "adam" {
  name                = "sb-adam-governance-${var.environment}"
  resource_group_name = data.azurerm_resource_group.adam.name
}

data "azurerm_log_analytics_workspace" "adam" {
  name                = "law-adam-governance-${var.environment}"
  resource_group_name = data.azurerm_resource_group.adam.name
}

# ── OUTPUTS ───────────────────────────────────────────────────────────────────

output "agt_node_pool_name" {
  value       = azurerm_kubernetes_cluster_node_pool.agt_services.name
  description = "AKS node pool name for AGT shared services"
}

output "agt_mesh_ed25519_key_ids" {
  value       = { for k, v in azurerm_key_vault_key.agt_mesh_ed25519 : k => v.id }
  description = "Key Vault key IDs for AGT Agent Mesh Ed25519 keys, by agent class"
  sensitive   = true
}

output "rgi_adapter_identity_client_id" {
  value       = azurerm_user_assigned_identity.agt_components["rgi-adapter"].client_id
  description = "Client ID for RGI-04 adapter Managed Identity — use in Helm values: rgiAdapter.workloadIdentityClientId"
}

output "agt_service_principal_ids" {
  value       = { for k, v in azurerm_user_assigned_identity.agt_components : k => v.principal_id }
  description = "Principal IDs for all AGT component managed identities"
  sensitive   = true
}
