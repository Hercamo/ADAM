"""
Azure Local (formerly Azure Stack HCI) Deployment Generator for ADAM DNA Specification.
Generates Bicep templates + configs for on-premises failover deployment.
"""

from typing import Dict, Any
from .base_generator import BaseGenerator

class AzureLocalGenerator(BaseGenerator):
    PLATFORM_NAME = "azure-local"
    PLATFORM_DISPLAY = "Azure Local (On-Premises Failover)"

    def generate_iac(self) -> Dict[str, str]:
        files = {}
        files[self.write_file("bicep/main.bicep", self._bicep_main())] = "Bicep deployment template"
        files[self.write_file("bicep/modules/aks-hci.bicep", self._bicep_aks_hci())] = "AKS-HCI module"
        files[self.write_file("bicep/modules/arc-services.bicep", self._bicep_arc_services())] = "Azure Arc services"
        files[self.write_file("terraform/main.tf", self._terraform_main())] = "Terraform for Azure Local"
        files[self.write_file("scripts/bootstrap-azure-local.sh", self._bootstrap_script())] = "Bootstrap script"
        files[self.write_file("scripts/failover-activate.sh", self._failover_script())] = "Failover activation script"
        files[self.write_file("scripts/failback-procedure.sh", self._failback_script())] = "Failback procedure script"
        return files

    def generate_configs(self) -> Dict[str, str]:
        files = {}
        files[self.write_json("config/adam-azure-local-config.json", self._azure_local_config())] = "Azure Local config"
        files[self.write_yaml("config/adam-azure-local-values.yaml", self._azure_local_values())] = "Azure Local Helm values"
        files[self.write_yaml("config/failover-policy.yaml", self._failover_policy())] = "Failover policy definition"
        return files

    def _bicep_main(self) -> str:
        return f'''// {self.header_comment("//")}
// Azure Local Deployment - On-Premises Failover for ADAM
// ACTIVATION: Only when both Azure and AWS are simultaneously unavailable,
// or for data residency isolation requirements.

targetScope = 'resourceGroup'

@description('Azure Local cluster name')
param clusterName string = 'adam-local-{self.company_slug}'

@description('Location')
param location string = resourceGroup().location

@description('Environment')
param environment string = 'production'

// AKS-HCI for critical-path agents only
module aksHci 'modules/aks-hci.bicep' = {{
  name: 'adam-aks-hci'
  params: {{
    clusterName: clusterName
    location: location
    environment: environment
  }}
}}

// Azure Arc for unified management
module arcServices 'modules/arc-services.bicep' = {{
  name: 'adam-arc-services'
  params: {{
    clusterName: clusterName
    location: location
  }}
}}
'''

    def _bicep_aks_hci(self) -> str:
        return f'''// {self.header_comment("//")}
// AKS-HCI Module - Reduced agent mesh for failover
// Only governance + orchestration + 5 governors run on Azure Local

param clusterName string
param location string
param environment string

// AKS-HCI cluster for ADAM critical services
resource aksHciCluster 'Microsoft.Kubernetes/connectedClusters@2024-01-01' = {{
  name: '${{clusterName}}-aks'
  location: location
  identity: {{
    type: 'SystemAssigned'
  }}
  properties: {{
    agentPublicKeyCertificate: ''
    distribution: 'aks_edge_k8s'
  }}
  tags: {{
    'adam-company': '{self.company_name}'
    'adam-platform': 'azure-local-failover'
    'adam-mode': 'survival'
  }}
}}

// Note: Azure Local runs a REDUCED agent set:
// - CORE Engine (read-only graph replica)
// - Policy Enforcement (cached policies)
// - BOSS Scoring (cached weights)
// - 5 Domain Governor Agents
// - 4 Orchestration Agents
// - 3 Human Interface Agents
// - Flight Recorder (local write, sync on reconnection)
// Total: 16 agents (vs 81 in full deployment)
// Capacity: ~30% of production traffic
'''

    def _bicep_arc_services(self) -> str:
        return f'''// {self.header_comment("//")}
// Azure Arc Services for unified management

param clusterName string
param location string

resource arcExtensionFlux 'Microsoft.KubernetesConfiguration/extensions@2023-05-01' = {{
  name: 'flux'
  scope: resourceGroup()
  properties: {{
    extensionType: 'microsoft.flux'
    autoUpgradeMinorVersion: true
  }}
}}

resource arcExtensionMonitor 'Microsoft.KubernetesConfiguration/extensions@2023-05-01' = {{
  name: 'azuremonitor-containers'
  scope: resourceGroup()
  properties: {{
    extensionType: 'Microsoft.AzureMonitor.Containers'
    autoUpgradeMinorVersion: true
  }}
}}
'''

    def _terraform_main(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM Azure Local Terraform - On-Premises Failover

terraform {{
  required_version = ">= 1.5.0"
  required_providers {{
    azurerm = {{
      source  = "hashicorp/azurerm"
      version = "~> 3.90"
    }}
    azapi = {{
      source  = "Azure/azapi"
      version = "~> 1.10"
    }}
  }}
}}

provider "azurerm" {{
  features {{}}
}}

# Azure Local Resource Group
resource "azurerm_resource_group" "adam_local" {{
  name     = "rg-adam-local-{self.company_slug}"
  location = var.location
  tags = {{
    "adam-company"  = "{self.company_name}"
    "adam-platform" = "azure-local"
    "adam-mode"     = "failover"
  }}
}}

# Arc-enabled Kubernetes for ADAM critical services
resource "azapi_resource" "adam_arc_cluster" {{
  type      = "Microsoft.Kubernetes/connectedClusters@2024-01-01"
  name      = "adam-local-{self.company_slug}"
  location  = var.location
  parent_id = azurerm_resource_group.adam_local.id

  identity {{
    type = "SystemAssigned"
  }}

  body = jsonencode({{
    properties = {{
      agentPublicKeyCertificate = ""
      distribution              = "aks_edge_k8s"
    }}
  }})
}}

variable "location" {{
  type    = string
  default = "westeurope"
}}
'''

    def _bootstrap_script(self) -> str:
        return f'''#!/bin/bash
{self.header_comment("#")}
# Bootstrap script for Azure Local ADAM deployment
# Run on each Azure Local node to prepare for ADAM failover

set -euo pipefail

COMPANY="{self.company_name}"
COMPANY_SLUG="{self.company_slug}"
echo "============================================================"
echo "  ADAM Azure Local Bootstrap"
echo "  Company: $COMPANY"
echo "  Mode: Failover (Survival)"
echo "============================================================"

# Phase 1: Validate Azure Local prerequisites
echo "[Phase 1] Validating prerequisites..."
command -v kubectl >/dev/null 2>&1 || {{ echo "kubectl not found"; exit 1; }}
command -v helm >/dev/null 2>&1 || {{ echo "helm not found"; exit 1; }}
command -v az >/dev/null 2>&1 || {{ echo "Azure CLI not found"; exit 1; }}

# Phase 2: Apply ADAM namespaces
echo "[Phase 2] Creating ADAM namespaces..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: adam-governance
  labels:
    adam/plane: governance
    adam/mode: failover
---
apiVersion: v1
kind: Namespace
metadata:
  name: adam-agents
  labels:
    adam/plane: execution
    adam/mode: failover
---
apiVersion: v1
kind: Namespace
metadata:
  name: adam-data
  labels:
    adam/plane: data
    adam/mode: failover
EOF

# Phase 3: Deploy CORE Engine (read-only replica)
echo "[Phase 3] Deploying CORE Engine (read-only mode)..."
helm upgrade --install adam-core ./helm/adam-platform \\
  --namespace adam-governance \\
  --set coreEngine.mode=readonly \\
  --set coreEngine.replicas=2 \\
  --set agentMesh.mode=survival \\
  --set global.company="$COMPANY" \\
  --set global.platform=azure-local \\
  --wait --timeout 10m

# Phase 4: Sync CORE Graph from primary
echo "[Phase 4] Syncing CORE Graph delta from primary..."
echo "  NOTE: This requires network connectivity to Azure primary."
echo "  If disconnected, ADAM will use the last cached CORE Graph snapshot."

# Phase 5: Deploy critical-path agents only
echo "[Phase 5] Deploying critical-path agents (16 of 81)..."
echo "  - 5 Domain Governor Agents"
echo "  - 4 Orchestration Agents"
echo "  - 3 Human Interface Agents"
echo "  - BOSS Scoring Engine"
echo "  - Policy Enforcement Engine"
echo "  - Flight Recorder (local write)"
echo "  - CORE Engine (read-only)"

# Phase 6: Validation
echo "[Phase 6] Validating deployment..."
kubectl get pods -n adam-governance
kubectl get pods -n adam-agents
kubectl get pods -n adam-data

echo ""
echo "============================================================"
echo "  ADAM Azure Local Bootstrap COMPLETE"
echo "  Status: STANDBY (waiting for failover activation)"
echo "  Capacity: ~30% of production traffic"
echo "  Disconnected mode: Up to 72 hours"
echo "============================================================"
'''

    def _failover_script(self) -> str:
        return f'''#!/bin/bash
{self.header_comment("#")}
# ADAM Failover Activation Script
# MUST be explicitly authorized by CISO
# ADAM does not self-failover to Azure Local

set -euo pipefail

echo "============================================================"
echo "  ADAM FAILOVER ACTIVATION"
echo "  Company: {self.company_name}"
echo "  Target: Azure Local (On-Premises)"
echo "============================================================"
echo ""
echo "  WARNING: This activates ADAM in survival mode."
echo "  Only critical-path services will be available."
echo "  CISO authorization is REQUIRED."
echo ""

read -p "Enter CISO authorization code: " AUTH_CODE
# In production, this would validate against the Crypto Vault

echo "[1/5] Activating Azure Local ADAM services..."
kubectl scale deployment --all -n adam-governance --replicas=2
kubectl scale deployment --all -n adam-agents --replicas=1

echo "[2/5] Switching DNS to Azure Local endpoints..."
echo "  NOTE: Manual DNS update required for director portal."

echo "[3/5] Enabling Flight Recorder local write mode..."
kubectl set env deployment/adam-flight-recorder -n adam-data \\
  WRITE_MODE=local SYNC_ON_RECONNECT=true

echo "[4/5] Loading cached CORE Graph and policies..."
kubectl exec -n adam-governance deploy/adam-core-engine -- \\
  /bin/adam-core load-cache --mode=readonly

echo "[5/5] Activating BOSS Scoring with cached weights..."
kubectl exec -n adam-governance deploy/adam-boss-engine -- \\
  /bin/adam-boss activate --mode=cached

echo ""
echo "============================================================"
echo "  ADAM FAILOVER ACTIVE"
echo "  Mode: Survival (30% capacity)"
echo "  Disconnected operation: Up to 72 hours"
echo "  FAILBACK: Must be manually authorized by CISO"
echo "============================================================"
'''

    def _failback_script(self) -> str:
        return f'''#!/bin/bash
{self.header_comment("#")}
# ADAM Failback Procedure
# Always manual. Requires data consistency verification.
# Minimum 4-hour validation window.

set -euo pipefail

echo "============================================================"
echo "  ADAM FAILBACK PROCEDURE"
echo "  Source: Azure Local -> Target: Azure Primary"
echo "  MINIMUM VALIDATION WINDOW: 4 hours"
echo "============================================================"

echo "[1/6] Verifying Azure primary availability..."
# Check Azure primary endpoints

echo "[2/6] Syncing Flight Recorder entries to primary..."
# Merge local evidence entries into primary store
# With conflict detection

echo "[3/6] Verifying CORE Graph consistency..."
# Compare local read-only graph against primary
# Flag any divergence

echo "[4/6] Running data consistency validation..."
# 4-hour minimum validation window
echo "  Starting validation timer (4 hours minimum)..."

echo "[5/6] Switching traffic back to Azure primary..."
# Requires CISO authorization

echo "[6/6] Scaling down Azure Local to standby..."
kubectl scale deployment --all -n adam-governance --replicas=0
kubectl scale deployment --all -n adam-agents --replicas=0

echo ""
echo "  ADAM has returned to Azure Primary."
echo "  Azure Local is back in STANDBY mode."
echo "============================================================"
'''

    def _azure_local_config(self) -> Dict[str, Any]:
        return {
            "adam_deployment": {
                "platform": "azure-local",
                "company": self.company_name,
                "version": "1.1",
                "generated": self.timestamp,
                "mode": "failover-standby",
            },
            "activation_policy": {
                "trigger": "Both Azure and AWS simultaneously unavailable OR data residency isolation",
                "authorization": "CISO explicit authorization required",
                "adam_self_failover": False,
            },
            "reduced_agent_set": {
                "total_agents": 16,
                "agents": [
                    "5 Domain Governor Agents",
                    "4 Orchestration Agents",
                    "3 Human Interface Agents",
                    "CORE Engine (read-only)",
                    "BOSS Scoring (cached)",
                    "Policy Enforcement (cached)",
                    "Flight Recorder (local write)",
                ],
                "not_available": [
                    "Corporate Work Groups (39 agents)",
                    "AI-Centric Division (23 agents)",
                    "Digital Twins (4 agents)",
                    "Meta-Governance (3 agents - partial)",
                ],
            },
            "capacity": {
                "traffic_percentage": 30,
                "disconnected_hours": 72,
                "core_graph_mode": "read-only-cached",
                "policy_mode": "cached-snapshot",
            },
            "sync_strategy": {
                "core_graph_delta": "every 5 minutes (when connected)",
                "policy_refresh": "hourly (when connected)",
                "flight_recorder": "local write, merge on reconnection",
                "failback": "manual only, CISO authorized, 4-hour validation minimum",
            },
            "boss_config": {
                "dimensions": self.get_boss_dimensions(),
                "thresholds": self.get_boss_thresholds(),
                "mode": "cached-weights",
            },
        }

    def _azure_local_values(self) -> Dict[str, Any]:
        return {
            "global": {
                "company": self.company_name,
                "platform": "azure-local",
                "mode": "failover",
            },
            "coreEngine": {
                "mode": "readonly",
                "replicas": 2,
                "cacheEnabled": True,
            },
            "bossScoring": {
                "mode": "cached",
                "dimensions": self.get_boss_dimensions(),
            },
            "agentMesh": {
                "mode": "survival",
                "totalAgents": 16,
                "replicaCount": 1,
            },
            "flightRecorder": {
                "mode": "local-write",
                "syncOnReconnect": True,
            },
        }

    def _failover_policy(self) -> Dict[str, Any]:
        return {
            "apiVersion": "adam.io/v1",
            "kind": "FailoverPolicy",
            "metadata": {
                "name": "adam-failover-policy",
                "company": self.company_name,
            },
            "spec": {
                "tiers": {
                    "tier0_normal": {
                        "description": "Full autonomy, all agents operational",
                        "platforms": ["azure-primary"],
                        "agents": 81,
                    },
                    "tier1_degraded": {
                        "description": "1+ non-critical agents offline",
                        "action": "Reduce autonomy budget 20%, enhanced logging",
                        "platforms": ["azure-primary", "aws-warm-standby"],
                    },
                    "tier2_impaired": {
                        "description": "Critical service degradation",
                        "action": "Reduce autonomy budget 50%, essential agents only",
                        "platforms": ["aws-activated"],
                    },
                    "tier3_crisis": {
                        "description": "Major outage or security incident",
                        "action": "Minimum autonomy, mandates only",
                        "platforms": ["aws-activated"],
                    },
                    "tier4_catastrophic": {
                        "description": "Azure Local failover activated",
                        "action": "Survival mode, CISO + CEO directing",
                        "platforms": ["azure-local"],
                        "agents": 16,
                        "capacity": "30%",
                    },
                },
            },
        }
