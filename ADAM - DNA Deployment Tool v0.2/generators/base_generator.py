"""
Base Generator for ADAM DNA Deployment Specifications.
All platform generators inherit from this base class.
"""

import os
import json
import yaml
from typing import Dict, Any
from datetime import datetime

# ADAM's 81+ Agent Mesh (reference count 81; dynamic scaling per enterprise DNA)
# Canonical five Governor Agents per ADAM book v1.4:
# Financial, Legal & Compliance, Security & Trust, Market & Ecosystem, Operations & Delivery
AGENT_CLASSES = {
    "domain_governors": {
        "description": "Domain Governance - the canonical 5 Governor Agents evaluate intent against domain constraints",
        "agents": [
            {"name": "Financial Governor Agent", "id": "ga-financial", "resources": {"vcpus": 50, "ram_gb": 200, "gpu": True}},
            {"name": "Legal & Compliance Governor Agent", "id": "ga-legal", "resources": {"vcpus": 50, "ram_gb": 200, "gpu": True}},
            {"name": "Security & Trust Governor Agent", "id": "ga-security", "resources": {"vcpus": 50, "ram_gb": 200, "gpu": True}},
            {"name": "Market & Ecosystem Governor Agent", "id": "ga-market", "resources": {"vcpus": 50, "ram_gb": 200, "gpu": True}},
            {"name": "Operations & Delivery Governor Agent", "id": "ga-operations", "resources": {"vcpus": 50, "ram_gb": 200, "gpu": True}},
        ],
    },
    "orchestration_agents": {
        "description": "Decompose authorized intent into deterministic executable plans",
        "agents": [
            {"name": "Global Orchestration Agent", "id": "orch-global", "resources": {"vcpus": 100, "ram_gb": 400, "gpu": False}},
            {"name": "Policy Enforcement Orchestrator", "id": "orch-policy", "resources": {"vcpus": 100, "ram_gb": 400, "gpu": False}},
            {"name": "Exception & Escalation Orchestrator", "id": "orch-exception", "resources": {"vcpus": 100, "ram_gb": 400, "gpu": False}},
            {"name": "Evidence-First Execution Orchestrator", "id": "orch-evidence", "resources": {"vcpus": 100, "ram_gb": 400, "gpu": False}},
        ],
    },
    "human_interface_agents": {
        "description": "Human-ADAM interaction layer",
        "agents": [
            {"name": "Intent Interpretation Agent", "id": "hi-intent", "resources": {"vcpus": 50, "ram_gb": 200, "gpu": True}},
            {"name": "Human Trust Gateway Agent", "id": "hi-gateway", "resources": {"vcpus": 50, "ram_gb": 200, "gpu": False}},
            {"name": "Explain-Back Agent", "id": "hi-explain", "resources": {"vcpus": 50, "ram_gb": 200, "gpu": True}},
        ],
    },
    "corporate_work_groups": {
        "description": "Corporate Functions Domain - end-to-end corporate concerns",
        "agents": [
            # Financial Stewardship Work Group
            {"name": "Transaction Processing Agent", "id": "wg-fin-txn", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": False}},
            {"name": "Reconciliation Agent", "id": "wg-fin-recon", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": False}},
            {"name": "Budget & Forecasting Agent", "id": "wg-fin-budget", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": True}},
            {"name": "Capital Allocation Agent", "id": "wg-fin-capital", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": False}},
            {"name": "Audit Preparation Agent", "id": "wg-fin-audit", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": False}},
            {"name": "Economic Efficiency Agent", "id": "wg-fin-efficiency", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": True}},
            # Legal & Regulatory Work Group
            {"name": "Contract Lifecycle Agent", "id": "wg-legal-contract", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": True}},
            {"name": "Regulatory Interpretation Agent", "id": "wg-legal-reg", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": True}},
            {"name": "Compliance Monitoring Agent", "id": "wg-legal-compliance", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": False}},
            {"name": "Legal Risk Analysis Agent", "id": "wg-legal-risk", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": True}},
            {"name": "Jurisdictional Logic Agent", "id": "wg-legal-jurisdiction", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": False}},
            # Security & Trust Work Group (formerly "Enterprise Risk" under pre-v1.4 naming)
            {"name": "Risk Assessment Agent", "id": "wg-risk-assess", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": True}},
            {"name": "Risk Monitoring Agent", "id": "wg-risk-monitor", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": False}},
            {"name": "Liability Tracking Agent", "id": "wg-risk-liability", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": False}},
            # Market Interface Work Group
            {"name": "Customer Interaction Agent", "id": "wg-market-customer", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": True}},
            {"name": "Partner Coordination Agent", "id": "wg-market-partner", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": False}},
            {"name": "Market Intelligence Agent", "id": "wg-market-intel", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": True}},
            {"name": "Demand Signal Agent", "id": "wg-market-demand", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": True}},
            {"name": "Reputation Monitoring Agent", "id": "wg-market-reputation", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": True}},
            # Operations & Delivery Work Group (formerly "Strategy & Objectives" under pre-v1.4 naming)
            {"name": "Execution Translation Agent", "id": "wg-ops-translate", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": True}},
            {"name": "Innovation Portfolio Agent", "id": "wg-ops-innovation", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": True}},
            # Operational Continuity Work Group
            {"name": "Dependency Awareness Agent", "id": "wg-ops-dependency", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": False}},
            {"name": "Failure Recovery Agent", "id": "wg-ops-recovery", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": False}},
            {"name": "Business Continuity Agent", "id": "wg-ops-bc", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": False}},
            {"name": "Resilience Testing Agent", "id": "wg-ops-resilience", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": False}},
            {"name": "Catastrophic Scenario Agent", "id": "wg-ops-catastrophe", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": True}},
            # Security & Trust Work Group
            {"name": "Threat Detection Agent", "id": "wg-sec-threat", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": True}},
            {"name": "Access Control Agent", "id": "wg-sec-access", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": False}},
            {"name": "Incident Response Agent", "id": "wg-sec-incident", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": False}},
            {"name": "Cryptographic Vault Agent", "id": "wg-sec-vault", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": False}},
            # Corporate Governance Interface Work Group
            {"name": "Board Reporting Agent", "id": "wg-gov-board", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": False}},
            {"name": "Stakeholder Communication Agent", "id": "wg-gov-stakeholder", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": True}},
            {"name": "Regulatory Filing Agent", "id": "wg-gov-filing", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": False}},
            {"name": "Compliance Reporting Agent", "id": "wg-gov-compliance", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": False}},
            # Data Governance Work Group
            {"name": "Data Governance Agent", "id": "wg-data-gov", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": False}},
            {"name": "Data Quality Agent", "id": "wg-data-quality", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": False}},
            {"name": "Data Residency Agent", "id": "wg-data-residency", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": False}},
            {"name": "PII Protection Agent", "id": "wg-data-pii", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": False}},
            {"name": "Rights & Licensing Agent", "id": "wg-data-rights", "resources": {"vcpus": 20, "ram_gb": 80, "gpu": True}},
        ],
    },
    "ai_centric_division": {
        "description": "AI-Centric Division - continuous monitoring and governance",
        "agents": [
            # Autonomy Governance
            {"name": "Autonomy Budget Manager Agent", "id": "ai-auto-budget", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": False}},
            {"name": "Authority Boundary Agent", "id": "ai-auto-authority", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": False}},
            {"name": "Escalation Logic Agent", "id": "ai-auto-escalation", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": False}},
            # Audit & Evidence
            {"name": "Evidence Collection Agent", "id": "ai-audit-collect", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": False}},
            {"name": "Evidence Correlation Agent", "id": "ai-audit-correlate", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": True}},
            {"name": "Internal Audit Simulation Agent", "id": "ai-audit-simulate", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": True}},
            # Ethics & Trust
            {"name": "Bias Detection Agent", "id": "ai-ethics-bias", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": True}},
            {"name": "Fairness Monitoring Agent", "id": "ai-ethics-fairness", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": True}},
            {"name": "Ethical Alignment Agent", "id": "ai-ethics-alignment", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": True}},
            # Model/Data Stewardship
            {"name": "Model Registry Agent", "id": "ai-model-registry", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": False}},
            {"name": "Model Drift Detection Agent", "id": "ai-model-drift", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": True}},
            {"name": "Data Pipeline Agent", "id": "ai-data-pipeline", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": False}},
            {"name": "Knowledge Management Agent", "id": "ai-data-knowledge", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": True}},
            # Innovation
            {"name": "Experiment Pipeline Agent", "id": "ai-innov-experiment", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": True}},
            {"name": "Safe Rollout Agent", "id": "ai-innov-rollout", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": False}},
            {"name": "Experiment Results Agent", "id": "ai-innov-results", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": True}},
            # CORE Graph Maintenance
            {"name": "CORE Graph Sync Agent", "id": "ai-core-sync", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": False}},
            {"name": "CORE Alignment Scoring Agent", "id": "ai-core-alignment", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": True}},
            # External Stakeholder Interface
            {"name": "External Stakeholder Agent", "id": "ai-external-stakeholder", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": True}},
            {"name": "Regulatory Interface Agent", "id": "ai-external-regulatory", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": False}},
            # Corporate Strategy AI
            {"name": "Strategy Alignment Agent", "id": "ai-strategy-align", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": True}},
            {"name": "Competitive Intelligence Agent", "id": "ai-strategy-competitive", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": True}},
            {"name": "Scenario Planning Agent", "id": "ai-strategy-scenario", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": True}},
        ],
    },
    "digital_twin_agents": {
        "description": "Digital Twins - live self-models consulted before/during/after execution",
        "agents": [
            {"name": "Enterprise Digital Twin Agent", "id": "twin-enterprise", "resources": {"vcpus": 200, "ram_gb": 800, "gpu": True}},
            {"name": "Operational Twin Agent", "id": "twin-operational", "resources": {"vcpus": 200, "ram_gb": 800, "gpu": True}},
            {"name": "Economic Twin Agent", "id": "twin-economic", "resources": {"vcpus": 200, "ram_gb": 800, "gpu": True}},
            {"name": "Risk & Compliance Twin Agent", "id": "twin-risk", "resources": {"vcpus": 200, "ram_gb": 800, "gpu": True}},
        ],
    },
    "meta_governance_agents": {
        "description": "Meta-Governance - what makes ADAM autonomous instead of automated",
        "agents": [
            {"name": "Autonomy Stability Agent", "id": "meta-stability", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": False}},
            {"name": "CORE Graph Integrity Agent", "id": "meta-integrity", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": True}},
            {"name": "Self-Audit Readiness Agent", "id": "meta-audit", "resources": {"vcpus": 30, "ram_gb": 120, "gpu": False}},
        ],
    },
}

class BaseGenerator:
    """Base class for all platform-specific deployment generators."""

    PLATFORM_NAME = "base"
    PLATFORM_DISPLAY = "Base Platform"

    def __init__(self, dna_data: Dict[str, Any], output_dir: str):
        self.dna = dna_data
        self.output_dir = output_dir
        self.company_name = dna_data.get("meta", {}).get("company_name", "Company")
        self.company_slug = self.company_name.lower().replace(" ", "-").replace(",", "").replace(".", "")[:30]
        self.timestamp = datetime.now().strftime("%Y-%m-%d")
        self.platform_dir = os.path.join(output_dir, self.PLATFORM_NAME)

    def generate(self) -> Dict[str, str]:
        """Generate all artifacts for this platform. Returns dict of filepath -> description."""
        os.makedirs(self.platform_dir, exist_ok=True)
        files = {}
        files.update(self.generate_iac())
        files.update(self.generate_configs())
        return files

    def generate_iac(self) -> Dict[str, str]:
        """Generate Infrastructure-as-Code files. Override in subclasses."""
        raise NotImplementedError

    def generate_configs(self) -> Dict[str, str]:
        """Generate configuration files. Override in subclasses."""
        raise NotImplementedError

    def write_file(self, filename: str, content: str) -> str:
        """Write content to file in platform directory."""
        filepath = os.path.join(self.platform_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            f.write(content)
        return filepath

    def write_json(self, filename: str, data: Any) -> str:
        """Write JSON file."""
        return self.write_file(filename, json.dumps(data, indent=2))

    def write_yaml(self, filename: str, data: Any) -> str:
        """Write YAML file."""
        return self.write_file(filename, yaml.dump(data, default_flow_style=False, sort_keys=False))

    def get_boss_dimensions(self) -> Dict[str, float]:
        """Get BOSS scoring dimensions from DNA data.

        Canonical BOSS Formulas v3.2 Priority Tier weights (denominator Σ = 24.0):
        Top=5.0 (Security only), Very High=4.0, High=3.0, Medium=2.0.
        Aligned to ADAM book v1.4.
        """
        boss = self.dna.get("boss_config", {})
        return boss.get("dimensions", {
            "security_impact": 5.0,       # Top tier
            "sovereignty_action": 4.0,    # Very High tier
            "financial_exposure": 4.0,    # Very High tier
            "regulatory_impact": 3.0,     # High tier
            "reputational_risk": 3.0,     # High tier
            "rights_certainty": 3.0,      # High tier
            "doctrinal_alignment": 2.0,   # Medium tier
        })

    def get_boss_thresholds(self) -> Dict[str, Dict]:
        """Get BOSS routing thresholds."""
        boss = self.dna.get("boss_config", {})
        return boss.get("routing_thresholds", {
            "soap": {"min": 0, "max": 10},
            "moderate": {"min": 11, "max": 30},
            "elevated": {"min": 31, "max": 50},
            "high": {"min": 51, "max": 75},
            "ohshat": {"min": 76, "max": 100},
        })

    def total_agents(self) -> int:
        """Count total agents."""
        return sum(len(cls["agents"]) for cls in AGENT_CLASSES.values())

    def total_vcpus(self) -> int:
        """Calculate total vCPUs needed."""
        total = 0
        for cls in AGENT_CLASSES.values():
            for agent in cls["agents"]:
                total += agent["resources"]["vcpus"]
        return total

    def total_ram_gb(self) -> int:
        """Calculate total RAM needed."""
        total = 0
        for cls in AGENT_CLASSES.values():
            for agent in cls["agents"]:
                total += agent["resources"]["ram_gb"]
        return total

    def gpu_agents_count(self) -> int:
        """Count agents needing GPU."""
        count = 0
        for cls in AGENT_CLASSES.values():
            for agent in cls["agents"]:
                if agent["resources"]["gpu"]:
                    count += 1
        return count

    def header_comment(self, comment_char: str = "#") -> str:
        """Generate standard header comment for IaC files."""
        lines = [
            f"{comment_char} ============================================================",
            f"{comment_char} ADAM DNA Deployment Specification",
            f"{comment_char} Platform: {self.PLATFORM_DISPLAY}",
            f"{comment_char} Company: {self.company_name}",
            f"{comment_char} Generated: {self.timestamp}",
            f"{comment_char} ADAM Version: 1.4 | DNA Questionnaire Version: 1.0 | BOSS Formulas: v3.2",
            f"{comment_char} ============================================================",
            f"{comment_char} This file was auto-generated by the ADAM DNA Deployment Tool",
            f"{comment_char} from a completed ADAM DNA Questionnaire.",
            f"{comment_char}",
            f"{comment_char} ADAM Agents: {self.total_agents()} | vCPUs: {self.total_vcpus()} | RAM: {self.total_ram_gb()} GB",
            f"{comment_char} GPU Agents: {self.gpu_agents_count()}",
            f"{comment_char} ============================================================",
        ]
        return "\n".join(lines)
