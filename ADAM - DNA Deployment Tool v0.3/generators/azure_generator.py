"""
Azure Deployment Generator for ADAM DNA Specification.
Generates Terraform + Bicep templates for Azure deployment.
"""

from typing import Dict, Any
from .base_generator import BaseGenerator

class AzureGenerator(BaseGenerator):
    PLATFORM_NAME = "azure"
    PLATFORM_DISPLAY = "Microsoft Azure (Primary)"

    def generate_iac(self) -> Dict[str, str]:
        files = {}
        files[self.write_file("terraform/main.tf", self._terraform_main())] = "Terraform root module"
        files[self.write_file("terraform/variables.tf", self._terraform_variables())] = "Terraform variables"
        files[self.write_file("terraform/modules/networking/main.tf", self._tf_networking())] = "Networking module"
        files[self.write_file("terraform/modules/identity/main.tf", self._tf_identity())] = "Identity & access module"
        files[self.write_file("terraform/modules/aks/main.tf", self._tf_aks())] = "AKS cluster module"
        files[self.write_file("terraform/modules/cosmosdb/main.tf", self._tf_cosmosdb())] = "Cosmos DB (CORE Graph) module"
        files[self.write_file("terraform/modules/evidence-store/main.tf", self._tf_evidence_store())] = "Flight Recorder evidence store"
        files[self.write_file("terraform/modules/keyvault/main.tf", self._tf_keyvault())] = "Key Vault (Crypto Authorization Vault)"
        files[self.write_file("terraform/modules/servicebus/main.tf", self._tf_servicebus())] = "Service Bus (orchestration messaging)"
        files[self.write_file("terraform/modules/monitoring/main.tf", self._tf_monitoring())] = "Monitoring & observability"
        files[self.write_file("terraform/modules/ai-services/main.tf", self._tf_ai_services())] = "Azure OpenAI & AI services"
        files[self.write_file("terraform/modules/data-explorer/main.tf", self._tf_data_explorer())] = "Data Explorer (BOSS scoring history)"
        files[self.write_file("bicep/main.bicep", self._bicep_main())] = "Bicep deployment template"
        files[self.write_file("bicep/modules/adam-core.bicep", self._bicep_adam_core())] = "Bicep ADAM CORE Engine module"
        return files

    def generate_configs(self) -> Dict[str, str]:
        files = {}
        files[self.write_json("config/adam-azure-config.json", self._azure_config())] = "Azure deployment config"
        files[self.write_yaml("config/adam-azure-values.yaml", self._azure_values())] = "Azure Helm values"
        return files

    def _terraform_main(self) -> str:
        return f'''{self.header_comment("#")}

terraform {{
  required_version = ">= 1.5.0"
  required_providers {{
    azurerm = {{
      source  = "hashicorp/azurerm"
      version = "~> 3.90"
    }}
    azuread = {{
      source  = "hashicorp/azuread"
      version = "~> 2.47"
    }}
  }}
  backend "azurerm" {{
    resource_group_name  = "adam-tfstate-rg"
    storage_account_name = "adamtfstate${{var.environment}}"
    container_name       = "tfstate"
    key                  = "adam-{self.company_slug}.tfstate"
  }}
}}

provider "azurerm" {{
  features {{
    key_vault {{
      purge_soft_delete_on_destroy = false
    }}
  }}
  subscription_id = var.subscription_id
}}

# ============================================================
# Resource Group - ADAM Governance Plane
# ============================================================
resource "azurerm_resource_group" "adam_governance" {{
  name     = "rg-adam-governance-${{var.environment}}"
  location = var.primary_region
  tags     = local.common_tags
}}

# ============================================================
# Resource Group - ADAM Agent Mesh (Execution Plane)
# ============================================================
resource "azurerm_resource_group" "adam_agents" {{
  name     = "rg-adam-agents-${{var.environment}}"
  location = var.primary_region
  tags     = local.common_tags
}}

# ============================================================
# Resource Group - ADAM Data Plane
# ============================================================
resource "azurerm_resource_group" "adam_data" {{
  name     = "rg-adam-data-${{var.environment}}"
  location = var.primary_region
  tags     = local.common_tags
}}

locals {{
  common_tags = {{
    "adam-company"     = "{self.company_name}"
    "adam-platform"    = "azure-primary"
    "managed-by"       = "adam-dna-deployment-tool"
    "environment"      = var.environment
    "cost-center"      = "adam-governance"
    "data-classification" = "confidential"
  }}
}}

# ============================================================
# Module: Networking (Hub-Spoke with sovereignty boundaries)
# ============================================================
module "networking" {{
  source              = "./modules/networking"
  resource_group_name = azurerm_resource_group.adam_governance.name
  location            = var.primary_region
  environment         = var.environment
  company_slug        = "{self.company_slug}"
  address_space       = var.vnet_address_space
  tags                = local.common_tags
}}

# ============================================================
# Module: Identity (Entra ID managed identities, zero-trust)
# ============================================================
module "identity" {{
  source              = "./modules/identity"
  resource_group_name = azurerm_resource_group.adam_governance.name
  location            = var.primary_region
  environment         = var.environment
  agent_count         = {self.total_agents()}
  tags                = local.common_tags
}}

# ============================================================
# Module: AKS (Agent Mesh container orchestration)
# ============================================================
module "aks" {{
  source              = "./modules/aks"
  resource_group_name = azurerm_resource_group.adam_agents.name
  location            = var.primary_region
  environment         = var.environment
  company_slug        = "{self.company_slug}"
  vnet_subnet_id      = module.networking.aks_subnet_id
  identity_id         = module.identity.aks_identity_id
  total_vcpus         = {self.total_vcpus()}
  total_ram_gb        = {self.total_ram_gb()}
  gpu_agent_count     = {self.gpu_agents_count()}
  tags                = local.common_tags
}}

# ============================================================
# Module: Cosmos DB (CORE Graph - Gremlin API)
# ============================================================
module "cosmosdb" {{
  source              = "./modules/cosmosdb"
  resource_group_name = azurerm_resource_group.adam_data.name
  location            = var.primary_region
  environment         = var.environment
  company_slug        = "{self.company_slug}"
  multi_region_writes = true
  secondary_regions   = var.secondary_regions
  tags                = local.common_tags
}}

# ============================================================
# Module: Evidence Store (Flight Recorder - immutable)
# ============================================================
module "evidence_store" {{
  source              = "./modules/evidence-store"
  resource_group_name = azurerm_resource_group.adam_data.name
  location            = var.primary_region
  environment         = var.environment
  company_slug        = "{self.company_slug}"
  retention_days      = 2555  # 7 years
  tags                = local.common_tags
}}

# ============================================================
# Module: Key Vault (Cryptographic Authorization Vault)
# ============================================================
module "keyvault" {{
  source              = "./modules/keyvault"
  resource_group_name = azurerm_resource_group.adam_governance.name
  location            = var.primary_region
  environment         = var.environment
  company_slug        = "{self.company_slug}"
  hsm_enabled         = true
  tags                = local.common_tags
}}

# ============================================================
# Module: Service Bus (Agent Orchestration Messaging)
# ============================================================
module "servicebus" {{
  source              = "./modules/servicebus"
  resource_group_name = azurerm_resource_group.adam_governance.name
  location            = var.primary_region
  environment         = var.environment
  company_slug        = "{self.company_slug}"
  tags                = local.common_tags
}}

# ============================================================
# Module: Monitoring (OpenTelemetry + Grafana)
# ============================================================
module "monitoring" {{
  source              = "./modules/monitoring"
  resource_group_name = azurerm_resource_group.adam_governance.name
  location            = var.primary_region
  environment         = var.environment
  company_slug        = "{self.company_slug}"
  tags                = local.common_tags
}}

# ============================================================
# Module: Azure OpenAI & AI Services
# ============================================================
module "ai_services" {{
  source              = "./modules/ai-services"
  resource_group_name = azurerm_resource_group.adam_agents.name
  location            = var.primary_region
  environment         = var.environment
  company_slug        = "{self.company_slug}"
  tags                = local.common_tags
}}

# ============================================================
# Module: Azure Data Explorer (BOSS Score History)
# ============================================================
module "data_explorer" {{
  source              = "./modules/data-explorer"
  resource_group_name = azurerm_resource_group.adam_data.name
  location            = var.primary_region
  environment         = var.environment
  company_slug        = "{self.company_slug}"
  tags                = local.common_tags
}}

# ============================================================
# Outputs
# ============================================================
output "adam_governance_rg" {{
  value = azurerm_resource_group.adam_governance.name
}}

output "aks_cluster_name" {{
  value = module.aks.cluster_name
}}

output "cosmosdb_endpoint" {{
  value     = module.cosmosdb.endpoint
  sensitive = true
}}

output "evidence_store_endpoint" {{
  value     = module.evidence_store.endpoint
  sensitive = true
}}

output "keyvault_uri" {{
  value     = module.keyvault.vault_uri
  sensitive = true
}}
'''

    def _terraform_variables(self) -> str:
        return f'''{self.header_comment("#")}

variable "subscription_id" {{
  description = "Azure subscription ID for ADAM deployment"
  type        = string
}}

variable "environment" {{
  description = "Deployment environment (dev, staging, production)"
  type        = string
  default     = "production"
}}

variable "primary_region" {{
  description = "Primary Azure region for ADAM governance plane"
  type        = string
  default     = "westeurope"
}}

variable "secondary_regions" {{
  description = "Secondary Azure regions for multi-region deployment"
  type        = list(string)
  default     = ["eastus", "southeastasia"]
}}

variable "vnet_address_space" {{
  description = "VNET address space for ADAM networking"
  type        = list(string)
  default     = ["10.0.0.0/8"]
}}

variable "aks_vm_size_system" {{
  description = "VM size for AKS system node pool"
  type        = string
  default     = "Standard_D8s_v5"
}}

variable "aks_vm_size_gpu" {{
  description = "VM size for AKS GPU node pool (Digital Twins, ML agents)"
  type        = string
  default     = "Standard_NC24ads_A100_v4"
}}

variable "adam_company_name" {{
  description = "Company name from DNA Questionnaire"
  type        = string
  default     = "{self.company_name}"
}}
'''

    def _tf_networking(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM Networking Module - Hub-Spoke with sovereignty boundaries
# Governance components use private endpoints only

variable "resource_group_name" {{ type = string }}
variable "location" {{ type = string }}
variable "environment" {{ type = string }}
variable "company_slug" {{ type = string }}
variable "address_space" {{ type = list(string) }}
variable "tags" {{ type = map(string) }}

resource "azurerm_virtual_network" "adam_hub" {{
  name                = "vnet-adam-hub-${{var.environment}}"
  resource_group_name = var.resource_group_name
  location            = var.location
  address_space       = var.address_space
  tags                = var.tags
}}

# Governance Subnet (CORE Engine, Policy Enforcement, BOSS, Flight Recorder)
resource "azurerm_subnet" "governance" {{
  name                 = "snet-adam-governance"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.adam_hub.name
  address_prefixes     = ["10.1.0.0/16"]
  private_endpoint_network_policies_enabled = true
}}

# Agent Mesh Subnet (AKS cluster for 81+ agents)
resource "azurerm_subnet" "aks" {{
  name                 = "snet-adam-aks"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.adam_hub.name
  address_prefixes     = ["10.2.0.0/16"]
}}

# Data Plane Subnet (Cosmos DB, Storage, Data Explorer)
resource "azurerm_subnet" "data" {{
  name                 = "snet-adam-data"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.adam_hub.name
  address_prefixes     = ["10.3.0.0/16"]
  private_endpoint_network_policies_enabled = true
}}

# Human Interface Subnet (Director Portal, Explain-Back)
resource "azurerm_subnet" "human_interface" {{
  name                 = "snet-adam-human-interface"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.adam_hub.name
  address_prefixes     = ["10.4.0.0/16"]
}}

# NSG: Governance - no public internet exposure
resource "azurerm_network_security_group" "governance" {{
  name                = "nsg-adam-governance-${{var.environment}}"
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = var.tags

  security_rule {{
    name                       = "DenyInternetInbound"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "Internet"
    destination_address_prefix = "*"
  }}

  security_rule {{
    name                       = "AllowVnetInbound"
    priority                   = 200
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "VirtualNetwork"
  }}
}}

output "aks_subnet_id" {{
  value = azurerm_subnet.aks.id
}}

output "governance_subnet_id" {{
  value = azurerm_subnet.governance.id
}}

output "data_subnet_id" {{
  value = azurerm_subnet.data.id
}}
'''

    def _tf_identity(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM Identity Module - Entra ID managed identities for zero-trust agent mesh

variable "resource_group_name" {{ type = string }}
variable "location" {{ type = string }}
variable "environment" {{ type = string }}
variable "agent_count" {{ type = number }}
variable "tags" {{ type = map(string) }}

# AKS Cluster Managed Identity
resource "azurerm_user_assigned_identity" "aks" {{
  name                = "id-adam-aks-${{var.environment}}"
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = var.tags
}}

# CORE Engine Managed Identity (high-privilege, governance plane)
resource "azurerm_user_assigned_identity" "core_engine" {{
  name                = "id-adam-core-engine-${{var.environment}}"
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = var.tags
}}

# Flight Recorder Identity (append-only permissions)
resource "azurerm_user_assigned_identity" "flight_recorder" {{
  name                = "id-adam-flight-recorder-${{var.environment}}"
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = var.tags
}}

# BOSS Scoring Engine Identity
resource "azurerm_user_assigned_identity" "boss_engine" {{
  name                = "id-adam-boss-engine-${{var.environment}}"
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = var.tags
}}

# Agent Mesh Workload Identity (shared by all 81+ agents via federated credentials)
resource "azurerm_user_assigned_identity" "agent_mesh" {{
  name                = "id-adam-agent-mesh-${{var.environment}}"
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = var.tags
}}

output "aks_identity_id" {{
  value = azurerm_user_assigned_identity.aks.id
}}

output "core_engine_identity_id" {{
  value = azurerm_user_assigned_identity.core_engine.id
}}
'''

    def _tf_aks(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM AKS Module - Container orchestration for 81-agent mesh

variable "resource_group_name" {{ type = string }}
variable "location" {{ type = string }}
variable "environment" {{ type = string }}
variable "company_slug" {{ type = string }}
variable "vnet_subnet_id" {{ type = string }}
variable "identity_id" {{ type = string }}
variable "total_vcpus" {{ type = number }}
variable "total_ram_gb" {{ type = number }}
variable "gpu_agent_count" {{ type = number }}
variable "tags" {{ type = map(string) }}

resource "azurerm_kubernetes_cluster" "adam" {{
  name                = "aks-adam-${{var.company_slug}}-${{var.environment}}"
  location            = var.location
  resource_group_name = var.resource_group_name
  dns_prefix          = "adam-${{var.company_slug}}"
  kubernetes_version  = "1.29"
  sku_tier            = "Standard"

  identity {{
    type         = "UserAssigned"
    identity_ids = [var.identity_id]
  }}

  # System Node Pool - ADAM governance components
  default_node_pool {{
    name                = "governance"
    vm_size             = "Standard_D16s_v5"
    min_count           = 3
    max_count           = 10
    enable_auto_scaling = true
    vnet_subnet_id      = var.vnet_subnet_id
    os_disk_size_gb     = 256
    zones               = [1, 2, 3]

    node_labels = {{
      "adam/plane" = "governance"
      "adam/tier"  = "sovereign"
    }}
  }}

  network_profile {{
    network_plugin    = "azure"
    network_policy    = "calico"
    load_balancer_sku = "standard"
    service_cidr      = "172.16.0.0/16"
    dns_service_ip    = "172.16.0.10"
  }}

  azure_active_directory_role_based_access_control {{
    managed            = true
    azure_rbac_enabled = true
  }}

  oms_agent {{
    log_analytics_workspace_id = "" # Set via monitoring module
  }}

  tags = var.tags
}}

# Agent Mesh Node Pool - CPU-intensive agents
resource "azurerm_kubernetes_cluster_node_pool" "agent_mesh" {{
  name                  = "agentmesh"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.adam.id
  vm_size               = "Standard_D32s_v5"
  min_count             = 5
  max_count             = 50
  enable_auto_scaling   = true
  zones                 = [1, 2, 3]
  os_disk_size_gb       = 512

  node_labels = {{
    "adam/plane"      = "execution"
    "adam/agent-type" = "cpu"
  }}

  node_taints = ["adam/plane=execution:NoSchedule"]
  tags        = var.tags
}}

# GPU Node Pool - Digital Twins, ML agents, reasoning agents
resource "azurerm_kubernetes_cluster_node_pool" "gpu" {{
  name                  = "gpuagents"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.adam.id
  vm_size               = "Standard_NC24ads_A100_v4"
  min_count             = 2
  max_count             = 20
  enable_auto_scaling   = true
  zones                 = [1, 2]
  os_disk_size_gb       = 1024

  node_labels = {{
    "adam/plane"      = "execution"
    "adam/agent-type" = "gpu"
    "adam/digital-twin" = "eligible"
  }}

  node_taints = ["nvidia.com/gpu=present:NoSchedule"]
  tags        = var.tags
}}

# Human Interface Node Pool - Director Portal, Trust Gateway
resource "azurerm_kubernetes_cluster_node_pool" "human_interface" {{
  name                  = "humanintf"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.adam.id
  vm_size               = "Standard_D8s_v5"
  min_count             = 2
  max_count             = 10
  enable_auto_scaling   = true
  zones                 = [1, 2, 3]

  node_labels = {{
    "adam/plane"      = "human-interface"
    "adam/agent-type" = "interface"
  }}

  tags = var.tags
}}

output "cluster_name" {{
  value = azurerm_kubernetes_cluster.adam.name
}}

output "cluster_id" {{
  value = azurerm_kubernetes_cluster.adam.id
}}
'''

    def _tf_cosmosdb(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM Cosmos DB Module - CORE Graph (Gremlin API)

variable "resource_group_name" {{ type = string }}
variable "location" {{ type = string }}
variable "environment" {{ type = string }}
variable "company_slug" {{ type = string }}
variable "multi_region_writes" {{ type = bool }}
variable "secondary_regions" {{ type = list(string) }}
variable "tags" {{ type = map(string) }}

resource "azurerm_cosmosdb_account" "adam_core" {{
  name                = "cosmos-adam-core-${{var.company_slug}}-${{var.environment}}"
  location            = var.location
  resource_group_name = var.resource_group_name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  enable_automatic_failover     = true
  enable_multiple_write_locations = var.multi_region_writes

  capabilities {{
    name = "EnableGremlin"
  }}

  consistency_policy {{
    consistency_level       = "BoundedStaleness"
    max_interval_in_seconds = 300
    max_staleness_prefix    = 100000
  }}

  geo_location {{
    location          = var.location
    failover_priority = 0
  }}

  dynamic "geo_location" {{
    for_each = var.secondary_regions
    content {{
      location          = geo_location.value
      failover_priority = geo_location.key + 1
    }}
  }}

  tags = var.tags
}}

# CORE Graph Database
resource "azurerm_cosmosdb_gremlin_database" "core_graph" {{
  name                = "adam-core-graph"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.adam_core.name
  throughput          = 100000  # 100K RU/s for governance-grade performance
}}

# CORE Graph Containers (Vertex Types)
resource "azurerm_cosmosdb_gremlin_graph" "doctrine" {{
  name                = "doctrine"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.adam_core.name
  database_name       = azurerm_cosmosdb_gremlin_database.core_graph.name
  partition_key_path  = "/doctrineType"
  throughput          = 20000

  index_policy {{
    automatic      = true
    indexing_mode  = "consistent"
    included_paths = ["/*"]
  }}
}}

resource "azurerm_cosmosdb_gremlin_graph" "culture" {{
  name                = "culture"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.adam_core.name
  database_name       = azurerm_cosmosdb_gremlin_database.core_graph.name
  partition_key_path  = "/cultureType"
  throughput          = 10000
}}

resource "azurerm_cosmosdb_gremlin_graph" "objectives" {{
  name                = "objectives"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.adam_core.name
  database_name       = azurerm_cosmosdb_gremlin_database.core_graph.name
  partition_key_path  = "/objectiveType"
  throughput          = 10000
}}

resource "azurerm_cosmosdb_gremlin_graph" "rules" {{
  name                = "rules"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.adam_core.name
  database_name       = azurerm_cosmosdb_gremlin_database.core_graph.name
  partition_key_path  = "/ruleType"
  throughput          = 10000
}}

resource "azurerm_cosmosdb_gremlin_graph" "expectations" {{
  name                = "expectations"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.adam_core.name
  database_name       = azurerm_cosmosdb_gremlin_database.core_graph.name
  partition_key_path  = "/expectationType"
  throughput          = 10000
}}

output "endpoint" {{
  value = azurerm_cosmosdb_account.adam_core.endpoint
}}

output "gremlin_endpoint" {{
  value = azurerm_cosmosdb_account.adam_core.endpoint
}}
'''

    def _tf_evidence_store(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM Evidence Store - Flight Recorder (immutable, append-only)

variable "resource_group_name" {{ type = string }}
variable "location" {{ type = string }}
variable "environment" {{ type = string }}
variable "company_slug" {{ type = string }}
variable "retention_days" {{ type = number }}
variable "tags" {{ type = map(string) }}

# Immutable Blob Storage for Flight Recorder
resource "azurerm_storage_account" "flight_recorder" {{
  name                     = "stadamfr${{var.company_slug}}${{var.environment}}"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "GZRS"  # Geo-zone-redundant
  min_tls_version          = "TLS1_2"
  allow_nested_items_to_be_public = false

  blob_properties {{
    versioning_enabled = true
    delete_retention_policy {{
      days = var.retention_days
    }}
    container_delete_retention_policy {{
      days = var.retention_days
    }}
  }}

  immutability_policy {{
    state                         = "Unlocked"
    period_since_creation_in_days = var.retention_days
    allow_protected_append_writes = true  # Append-only
  }}

  tags = var.tags
}}

# Azure Confidential Ledger for cryptographic evidence chains
resource "azurerm_confidential_ledger" "adam_ledger" {{
  name                = "cl-adam-${{var.company_slug}}-${{var.environment}}"
  resource_group_name = var.resource_group_name
  location            = var.location
  ledger_type         = "Private"

  azuread_based_service_principal {{
    principal_id = "" # Set via identity module
    ledger_role_name = "Administrator"
    tenant_id    = ""
  }}

  tags = var.tags
}}

output "endpoint" {{
  value = azurerm_storage_account.flight_recorder.primary_blob_endpoint
}}
'''

    def _tf_keyvault(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM Key Vault - Cryptographic Authorization Vault with HSM

variable "resource_group_name" {{ type = string }}
variable "location" {{ type = string }}
variable "environment" {{ type = string }}
variable "company_slug" {{ type = string }}
variable "hsm_enabled" {{ type = bool }}
variable "tags" {{ type = map(string) }}

data "azurerm_client_config" "current" {{}}

resource "azurerm_key_vault" "adam_vault" {{
  name                = "kv-adam-${{var.company_slug}}-${{var.environment}}"
  location            = var.location
  resource_group_name = var.resource_group_name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = var.hsm_enabled ? "premium" : "standard"

  enabled_for_deployment          = false
  enabled_for_disk_encryption     = false
  enabled_for_template_deployment = false
  enable_rbac_authorization       = true
  purge_protection_enabled        = true
  soft_delete_retention_days      = 90

  network_acls {{
    default_action = "Deny"
    bypass         = "AzureServices"
  }}

  tags = var.tags
}}

output "vault_uri" {{
  value = azurerm_key_vault.adam_vault.vault_uri
}}
'''

    def _tf_servicebus(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM Service Bus - Agent orchestration messaging

variable "resource_group_name" {{ type = string }}
variable "location" {{ type = string }}
variable "environment" {{ type = string }}
variable "company_slug" {{ type = string }}
variable "tags" {{ type = map(string) }}

resource "azurerm_servicebus_namespace" "adam" {{
  name                = "sb-adam-${{var.company_slug}}-${{var.environment}}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "Premium"
  capacity            = 4
  premium_messaging_partitions = 4
  tags                = var.tags
}}

# Intent Pipeline Queue
resource "azurerm_servicebus_queue" "intent_pipeline" {{
  name         = "adam-intent-pipeline"
  namespace_id = azurerm_servicebus_namespace.adam.id
  max_delivery_count = 10
  lock_duration      = "PT5M"
  max_size_in_megabytes = 81920
}}

# Exception Escalation Queue
resource "azurerm_servicebus_queue" "exception_escalation" {{
  name         = "adam-exception-escalation"
  namespace_id = azurerm_servicebus_namespace.adam.id
  max_delivery_count = 3
  lock_duration      = "PT2M"
}}

# BOSS Scoring Topic (fan-out to all governance agents)
resource "azurerm_servicebus_topic" "boss_scoring" {{
  name         = "adam-boss-scoring"
  namespace_id = azurerm_servicebus_namespace.adam.id
  max_size_in_megabytes = 81920
}}

# Evidence Capture Topic
resource "azurerm_servicebus_topic" "evidence_capture" {{
  name         = "adam-evidence-capture"
  namespace_id = azurerm_servicebus_namespace.adam.id
}}
'''

    def _tf_monitoring(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM Monitoring - OpenTelemetry + Grafana + Azure Monitor

variable "resource_group_name" {{ type = string }}
variable "location" {{ type = string }}
variable "environment" {{ type = string }}
variable "company_slug" {{ type = string }}
variable "tags" {{ type = map(string) }}

resource "azurerm_log_analytics_workspace" "adam" {{
  name                = "law-adam-${{var.company_slug}}-${{var.environment}}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = 365
  tags                = var.tags
}}

resource "azurerm_application_insights" "adam" {{
  name                = "appi-adam-${{var.company_slug}}-${{var.environment}}"
  location            = var.location
  resource_group_name = var.resource_group_name
  workspace_id        = azurerm_log_analytics_workspace.adam.id
  application_type    = "other"
  tags                = var.tags
}}

resource "azurerm_dashboard_grafana" "adam" {{
  name                = "grafana-adam-${{var.company_slug}}-${{var.environment}}"
  resource_group_name = var.resource_group_name
  location            = var.location
  grafana_major_version = "10"

  identity {{
    type = "SystemAssigned"
  }}

  tags = var.tags
}}
'''

    def _tf_ai_services(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM AI Services - Azure OpenAI for agent reasoning

variable "resource_group_name" {{ type = string }}
variable "location" {{ type = string }}
variable "environment" {{ type = string }}
variable "company_slug" {{ type = string }}
variable "tags" {{ type = map(string) }}

resource "azurerm_cognitive_account" "adam_openai" {{
  name                = "oai-adam-${{var.company_slug}}-${{var.environment}}"
  location            = var.location
  resource_group_name = var.resource_group_name
  kind                = "OpenAI"
  sku_name            = "S0"

  custom_subdomain_name = "adam-${{var.company_slug}}-${{var.environment}}"

  network_acls {{
    default_action = "Deny"
  }}

  tags = var.tags
}}

# Primary reasoning model (Governor Agents, Domain Governors)
resource "azurerm_cognitive_deployment" "reasoning" {{
  name                 = "adam-reasoning-primary"
  cognitive_account_id = azurerm_cognitive_account.adam_openai.id

  model {{
    format  = "OpenAI"
    name    = "gpt-4o"
    version = "2024-11-20"
  }}

  sku {{
    name     = "GlobalStandard"
    capacity = 450  # 450K TPM
  }}
}}

# Fast execution model (Work Group agents, routine operations)
resource "azurerm_cognitive_deployment" "execution" {{
  name                 = "adam-execution-fast"
  cognitive_account_id = azurerm_cognitive_account.adam_openai.id

  model {{
    format  = "OpenAI"
    name    = "gpt-4o-mini"
    version = "2024-07-18"
  }}

  sku {{
    name     = "GlobalStandard"
    capacity = 1000  # 1M TPM
  }}
}}

# Deep reasoning model (Digital Twins, Risk analysis)
resource "azurerm_cognitive_deployment" "deep_reasoning" {{
  name                 = "adam-deep-reasoning"
  cognitive_account_id = azurerm_cognitive_account.adam_openai.id

  model {{
    format  = "OpenAI"
    name    = "o1"
    version = "2024-12-17"
  }}

  sku {{
    name     = "GlobalStandard"
    capacity = 100
  }}
}}
'''

    def _tf_data_explorer(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM Data Explorer - BOSS Score History & Time Series

variable "resource_group_name" {{ type = string }}
variable "location" {{ type = string }}
variable "environment" {{ type = string }}
variable "company_slug" {{ type = string }}
variable "tags" {{ type = map(string) }}

resource "azurerm_kusto_cluster" "adam_boss" {{
  name                = "adxadamboss${{var.environment}}"
  location            = var.location
  resource_group_name = var.resource_group_name

  sku {{
    name     = "Standard_E8ads_v5"
    capacity = 3
  }}

  auto_stop_enabled = false
  tags              = var.tags
}}

resource "azurerm_kusto_database" "boss_history" {{
  name                = "adam-boss-history"
  resource_group_name = var.resource_group_name
  location            = var.location
  cluster_name        = azurerm_kusto_cluster.adam_boss.name
  hot_cache_period    = "P90D"
  soft_delete_period  = "P1825D"  # 5 years
}}
'''

    def _bicep_main(self) -> str:
        # header_comment("//") already prefixes every line with "// ";
        # do not add an extra "// " here (would yield "// // ..." on line 1).
        return f'''{self.header_comment("//")}

targetScope = 'subscription'

@description('Primary Azure region')
param primaryRegion string = 'westeurope'

@description('Environment name')
param environment string = 'production'

@description('Company name from DNA Questionnaire')
param companyName string = '{self.company_name}'

var companySlug = toLower(replace(replace(companyName, ' ', '-'), ',', ''))

// Resource Groups
resource rgGovernance 'Microsoft.Resources/resourceGroups@2023-07-01' = {{
  name: 'rg-adam-governance-${{environment}}'
  location: primaryRegion
  tags: {{
    'adam-company': companyName
    'adam-platform': 'azure-primary'
  }}
}}

resource rgAgents 'Microsoft.Resources/resourceGroups@2023-07-01' = {{
  name: 'rg-adam-agents-${{environment}}'
  location: primaryRegion
  tags: {{
    'adam-company': companyName
  }}
}}

resource rgData 'Microsoft.Resources/resourceGroups@2023-07-01' = {{
  name: 'rg-adam-data-${{environment}}'
  location: primaryRegion
  tags: {{
    'adam-company': companyName
  }}
}}

// ADAM CORE Engine Module
module adamCore 'modules/adam-core.bicep' = {{
  name: 'adam-core-deployment'
  scope: rgGovernance
  params: {{
    location: primaryRegion
    environment: environment
    companySlug: companySlug
  }}
}}

output governanceResourceGroup string = rgGovernance.name
output agentsResourceGroup string = rgAgents.name
output dataResourceGroup string = rgData.name
'''

    def _bicep_adam_core(self) -> str:
        return f'''// {self.header_comment("//")}
// ADAM CORE Engine Bicep Module

param location string
param environment string
param companySlug string

// Cosmos DB for CORE Graph
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' = {{
  name: 'cosmos-adam-core-${{companySlug}}-${{environment}}'
  location: location
  kind: 'GlobalDocumentDB'
  properties: {{
    databaseAccountOfferType: 'Standard'
    enableAutomaticFailover: true
    enableMultipleWriteLocations: true
    capabilities: [
      {{ name: 'EnableGremlin' }}
    ]
    consistencyPolicy: {{
      defaultConsistencyLevel: 'BoundedStaleness'
      maxIntervalInSeconds: 300
      maxStalenessPrefix: 100000
    }}
    locations: [
      {{ locationName: location, failoverPriority: 0 }}
    ]
  }}
}}

// Key Vault for Cryptographic Authorization Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {{
  name: 'kv-adam-${{companySlug}}-${{environment}}'
  location: location
  properties: {{
    sku: {{ family: 'A', name: 'premium' }}
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enablePurgeProtection: true
    softDeleteRetentionInDays: 90
    networkAcls: {{
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    }}
  }}
}}
'''

    def _azure_config(self) -> Dict[str, Any]:
        """Generate Azure-specific JSON configuration."""
        return {
            "adam_deployment": {
                "platform": "azure",
                "company": self.company_name,
                "version": "1.1",
                "generated": self.timestamp,
            },
            "governance_plane": {
                "core_engine": {
                    "database": "cosmos-db-gremlin",
                    "throughput_ru": 100000,
                    "multi_region": True,
                    "consistency": "BoundedStaleness",
                },
                "policy_enforcement": {
                    "engine": "opa-gatekeeper",
                    "evaluation_target": "100K/sec",
                },
                "boss_scoring": {
                    "engine": "azure-data-explorer",
                    "dimensions": self.get_boss_dimensions(),
                    "thresholds": self.get_boss_thresholds(),
                },
                "flight_recorder": {
                    "storage": "azure-blob-immutable",
                    "ledger": "azure-confidential-ledger",
                    "retention_years": 7,
                },
                "crypto_vault": {
                    "service": "azure-key-vault-premium",
                    "hsm": True,
                },
            },
            "agent_mesh": {
                "orchestration": "aks",
                "total_agents": self.total_agents(),
                "total_vcpus": self.total_vcpus(),
                "total_ram_gb": self.total_ram_gb(),
                "gpu_agents": self.gpu_agents_count(),
                "node_pools": {
                    "governance": {"vm_size": "Standard_D16s_v5", "min": 3, "max": 10},
                    "agent_mesh": {"vm_size": "Standard_D32s_v5", "min": 5, "max": 50},
                    "gpu": {"vm_size": "Standard_NC24ads_A100_v4", "min": 2, "max": 20},
                    "human_interface": {"vm_size": "Standard_D8s_v5", "min": 2, "max": 10},
                },
            },
            "ai_services": {
                "provider": "azure-openai",
                "models": {
                    "reasoning": {"model": "gpt-4o", "tpm": 450000},
                    "execution": {"model": "gpt-4o-mini", "tpm": 1000000},
                    "deep_reasoning": {"model": "o1", "tpm": 100000},
                },
            },
            "networking": {
                "topology": "hub-spoke",
                "governance_isolation": True,
                "private_endpoints": True,
                "no_public_internet": ["governance", "data"],
            },
        }

    def _azure_values(self) -> Dict[str, Any]:
        """Generate Azure Helm values."""
        return {
            "global": {
                "company": self.company_name,
                "platform": "azure",
            },
            "coreEngine": {
                "cosmosDb": {
                    "enabled": True,
                    "api": "gremlin",
                    "throughput": 100000,
                },
            },
            "bossScoring": {
                "dimensions": self.get_boss_dimensions(),
                "thresholds": self.get_boss_thresholds(),
            },
            "agentMesh": {
                "replicaCount": 3,
                "resources": {
                    "governorAgents": {"cpu": "50", "memory": "200Gi", "gpu": 1},
                    "orchestrationAgents": {"cpu": "100", "memory": "400Gi"},
                    "workGroupAgents": {"cpu": "20", "memory": "80Gi"},
                    "digitalTwins": {"cpu": "200", "memory": "800Gi", "gpu": 4},
                },
            },
        }
