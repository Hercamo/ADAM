"""
ADAM DNA Configuration Bundle Generator.
Creates comprehensive JSON/YAML config bundles that capture all ADAM configuration
from a filled DNA Questionnaire - platform-agnostic machine-readable format.
"""

import json
import yaml
import os
from typing import Dict, Any
from .base_generator import BaseGenerator, AGENT_CLASSES


class ConfigBundleGenerator(BaseGenerator):
    PLATFORM_NAME = "config-bundle"
    PLATFORM_DISPLAY = "ADAM Configuration Bundle (Platform-Agnostic)"

    def generate_iac(self) -> Dict[str, str]:
        return {}  # Config bundle doesn't generate IaC

    def generate_configs(self) -> Dict[str, str]:
        files = {}

        # Master configuration
        files[self.write_json("adam-master-config.json", self._master_config())] = "Master ADAM configuration"
        files[self.write_yaml("adam-master-config.yaml", self._master_config())] = "Master ADAM configuration (YAML)"

        # CORE Graph seed data
        files[self.write_json("core-graph/doctrine-seed.json", self._doctrine_seed())] = "CORE Graph doctrine seed"
        files[self.write_json("core-graph/culture-seed.json", self._culture_seed())] = "CORE Graph culture seed"
        files[self.write_json("core-graph/objectives-seed.json", self._objectives_seed())] = "CORE Graph objectives seed"
        files[self.write_json("core-graph/rules-seed.json", self._rules_seed())] = "CORE Graph rules seed"

        # BOSS configuration
        files[self.write_json("boss/boss-config.json", self._boss_config_detailed())] = "BOSS scoring configuration"
        files[self.write_file("boss/boss-routing.rego", self._boss_rego())] = "BOSS OPA/Rego policies"

        # Agent registry
        files[self.write_json("agents/agent-registry.json", self._agent_registry())] = "81-agent registry"
        files[self.write_yaml("agents/agent-registry.yaml", self._agent_registry())] = "81-agent registry (YAML)"

        # Intent Object schema
        files[self.write_json("schemas/intent-object-schema.json", self._intent_schema())] = "Intent Object JSON schema"
        files[self.write_json("schemas/boss-score-schema.json", self._boss_score_schema())] = "BOSS Score JSON schema"
        files[self.write_json("schemas/flight-recorder-schema.json", self._flight_recorder_schema())] = "Flight Recorder entry schema"

        # Governance configuration
        files[self.write_json("governance/directors.json", self._directors_config())] = "Director roles configuration"
        files[self.write_json("governance/delegation-model.json", self._delegation_config())] = "Delegation model"
        files[self.write_yaml("governance/exception-economy.yaml", self._exception_economy())] = "Exception economy config"

        return files

    def generate(self) -> Dict[str, str]:
        os.makedirs(self.platform_dir, exist_ok=True)
        return self.generate_configs()

    def _master_config(self) -> Dict[str, Any]:
        return {
            "$schema": "https://adam.io/schemas/dna-config/v1.0",
            "adam_version": "0.4",
            "dna_version": "1.0",
            "company": {
                "name": self.company_name,
                "slug": self.company_slug,
                "generated": self.timestamp,
                "mission": self.dna.get("governance", {}).get("mission", ""),
                "vision": self.dna.get("governance", {}).get("vision", ""),
            },
            "core_engine": {
                "graph_type": "gremlin-compatible",
                "vertex_types": ["Doctrine", "Culture", "Objectives", "Rules", "Expectations",
                                 "Financials", "Rights", "Customer", "Regulatory", "StrategyDrift", "IntentObject"],
                "edge_types": ["GOVERNS", "CONSTRAINS", "PRIORITIZES", "CONFLICTS_WITH", "DELEGATES_TO",
                               "MONITORS", "FEEDS_INTO", "ESCALATES_TO", "AUDITS", "SIMULATES"],
                "immutable_layer": "doctrine-root",
                "version_controlled": True,
            },
            "boss": {
                "dimensions": self.get_boss_dimensions(),
                "thresholds": self.get_boss_thresholds(),
                "composite_formula": "weighted_average_with_override",
                "non_idempotent_penalty": 15,
                "critical_dimension_override_threshold": 75,
            },
            "agent_mesh": {
                "total_agents": self.total_agents(),
                "total_vcpus": self.total_vcpus(),
                "total_ram_gb": self.total_ram_gb(),
                "gpu_agents": self.gpu_agents_count(),
                "classes": {k: len(v["agents"]) for k, v in AGENT_CLASSES.items()},
            },
            "governance": {
                "model": "5-director-constitution",
                "directors": ["CEO", "CFO", "Legal Director", "Market Director", "CISO"],
                "optional_directors": ["CPO"],
                "interface_agents": ["Intent Interpretation", "Trust Gateway", "Explain-Back"],
                "exception_economy": True,
            },
            "platforms_supported": ["azure", "aws", "gcp", "kubernetes", "azure-local"],
        }

    def _doctrine_seed(self) -> Dict:
        gov = self.dna.get("governance", {})
        sections = self.dna.get("sections", {})
        doctrine_section = sections.get("doctrine_identity", {})
        questions = doctrine_section.get("questions", {})

        return {
            "vertex_type": "Doctrine",
            "partition_key": "root",
            "company": self.company_name,
            "mission": gov.get("mission", ""),
            "vision": gov.get("vision", ""),
            "principles": gov.get("principles", []),
            "sacred_boundaries": gov.get("sacred_boundaries", []),
            "legal_entity": questions.get("1.1.6", {}).get("answer", ""),
            "immutable": True,
            "requires_board_approval_to_modify": True,
        }

    def _culture_seed(self) -> Dict:
        sections = self.dna.get("sections", {})
        culture = sections.get("culture_graph", {})
        questions = culture.get("questions", {})

        return {
            "vertex_type": "Culture",
            "subgraph": "culture",
            "values_trade_offs": questions.get("2.1.1", {}).get("answer", ""),
            "behavioral_norms": questions.get("2.1.2", {}).get("answer", ""),
            "failure_philosophy": questions.get("2.1.3", {}).get("answer", ""),
            "decision_philosophy": questions.get("2.1.4", {}).get("answer", ""),
            "external_posture": questions.get("2.2.1", {}).get("answer", ""),
            "internal_posture": questions.get("2.2.2", {}).get("answer", ""),
            "posture_conflict_rules": questions.get("2.2.3", {}).get("answer", ""),
        }

    def _objectives_seed(self) -> Dict:
        sections = self.dna.get("sections", {})
        obj = sections.get("objectives_graph", {})
        questions = obj.get("questions", {})

        return {
            "vertex_type": "Objectives",
            "subgraph": "objectives",
            "mandates": questions.get("3.1.1", {}).get("answer", ""),
            "mandate_enforcement": questions.get("3.1.2", {}).get("answer", ""),
            "goals": questions.get("3.2.1", {}).get("answer", ""),
            "goal_priorities": questions.get("3.2.2", {}).get("answer", ""),
            "planning_cadence": questions.get("3.2.3", {}).get("answer", ""),
            "objectives_aspirational": questions.get("3.3.1", {}).get("answer", ""),
            "deprioritization_signals": questions.get("3.3.2", {}).get("answer", ""),
        }

    def _rules_seed(self) -> Dict:
        sections = self.dna.get("sections", {})
        rules = sections.get("rules_expectations", {})
        questions = rules.get("questions", {})

        return {
            "vertex_type": "Rules",
            "subgraph": "rules_expectations",
            "hard_rules": questions.get("4.1.1", {}).get("answer", ""),
            "rule_sources": questions.get("4.1.2", {}).get("answer", ""),
            "soft_expectations": questions.get("4.2.1", {}).get("answer", ""),
            "exception_tolerance": questions.get("4.2.2", {}).get("answer", ""),
        }

    def _boss_config_detailed(self) -> Dict:
        boss = self.dna.get("boss_config", {})
        return {
            "$schema": "https://adam.io/schemas/boss-config/v1.0",
            "dimensions": boss.get("dimensions", self.get_boss_dimensions()),
            "composite_formula": {
                "type": "weighted_average",
                "weight_sum": sum(self.get_boss_dimensions().values()),
                "formula": "C = Sum(S_d * W_d) / Sum(W_d)",
                "critical_override": "if max(S_d) > 75: C = max(C, max(S_d) - 10)",
                "non_idempotent_penalty": 15,
                "cap": 100,
            },
            "routing_thresholds": self.get_boss_thresholds(),
            "recalibration": boss.get("recalibration_cadence", "Quarterly with director approval"),
            "exception_economy": {
                "packet_structure": boss.get("exception_packets", ""),
                "target_volume": boss.get("target_exception_volume", "5-15 per director per day"),
                "feedback_loop": boss.get("feedback_loop", ""),
            },
        }

    def _boss_rego(self) -> str:
        dims = self.get_boss_dimensions()
        weights_str = ", ".join(f'"{k}": {v}' for k, v in dims.items())

        return f'''{self.header_comment("#")}
# ADAM BOSS Scoring - OPA/Rego Policy
# Company: {self.company_name}

package adam.boss

import future.keywords.in

# Dimension weights from DNA Questionnaire
weights := {{{weights_str}}}

# Composite score calculation
composite_score := score {{
  weighted_sum := sum([input.dimensions[d] * weights[d] | some d in object.keys(weights)])
  weight_total := sum([w | some w in object.values(weights)])
  raw := weighted_sum / weight_total

  # Critical dimension override
  max_dim := max([input.dimensions[d] | some d in object.keys(weights)])
  override := max_dim - 10

  base := max(raw, override) if max_dim > 75 else raw

  # Non-idempotent penalty
  penalty := 15 if input.is_non_idempotent else 0

  score := min(base + penalty, 100)
}}

# Routing tier
default routing_tier := "soap"
routing_tier := "ohshat" if composite_score > 75
routing_tier := "high" if composite_score > 50
routing_tier := "elevated" if composite_score > 30
routing_tier := "moderate" if composite_score > 10

# Escalation targets per tier
escalation_targets["ohshat"] := ["CEO", "All Directors"]
escalation_targets["high"] := ["Relevant Domain Director"]
escalation_targets["elevated"] := ["Domain Governor Agent"]
escalation_targets["moderate"] := ["Enhanced Logging"]
escalation_targets["soap"] := ["Autonomous Execution"]

# Intent validation
intent_valid {{
  input.intent.intent_id != ""
  input.intent.source.role != ""
  count(input.intent.desired_outcomes) > 0
}}

# Director authorization check
director_authorized {{
  input.intent.source.role == "director"
}}

director_authorized {{
  count(input.intent.source.delegation_chain) > 0
}}
'''

    def _agent_registry(self) -> Dict:
        registry = {
            "adam_version": "0.4",
            "company": self.company_name,
            "total_agents": self.total_agents(),
            "agent_classes": {},
        }

        for class_key, class_data in AGENT_CLASSES.items():
            registry["agent_classes"][class_key] = {
                "description": class_data["description"],
                "agent_count": len(class_data["agents"]),
                "agents": [
                    {
                        "id": a["id"],
                        "name": a["name"],
                        "resources": a["resources"],
                    }
                    for a in class_data["agents"]
                ],
            }

        return registry

    def _intent_schema(self) -> Dict:
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "ADAM Intent Object",
            "type": "object",
            "required": ["intent_id", "timestamp", "source", "desired_outcomes", "constraints"],
            "properties": {
                "intent_id": {"type": "string", "format": "uuid"},
                "timestamp": {"type": "string", "format": "date-time"},
                "source": {
                    "type": "object",
                    "required": ["user_id", "role"],
                    "properties": {
                        "user_id": {"type": "string"},
                        "role": {"type": "string", "enum": ["director", "executive", "operator", "system"]},
                        "delegation_chain": {"type": "array"},
                    },
                },
                "desired_outcomes": {
                    "type": "array", "minItems": 1,
                    "items": {
                        "type": "object",
                        "required": ["outcome_id", "description", "success_criteria"],
                        "properties": {
                            "outcome_id": {"type": "string"},
                            "description": {"type": "string"},
                            "success_criteria": {"type": "array"},
                            "priority": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                        },
                    },
                },
                "constraints": {"type": "array"},
                "risk_tolerance": {
                    "type": "object",
                    "properties": {
                        "financial_threshold": {"type": "number"},
                        "regulatory_exposure": {"type": "string"},
                        "reputational_risk": {"type": "string"},
                        "rights_certainty_minimum": {"type": "number"},
                    },
                },
                "urgency": {"type": "string", "enum": ["routine", "elevated", "critical", "emergency"]},
                "approval_conditions": {"type": "array"},
                "core_graph_context": {"type": "object"},
            },
        }

    def _boss_score_schema(self) -> Dict:
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "ADAM BOSS Score",
            "type": "object",
            "required": ["score_id", "intent_id", "dimensions", "composite_score", "routing_tier"],
            "properties": {
                "score_id": {"type": "string", "format": "uuid"},
                "intent_id": {"type": "string", "format": "uuid"},
                "timestamp": {"type": "string", "format": "date-time"},
                "dimensions": {
                    "type": "object",
                    "properties": {k: {"type": "number", "minimum": 0, "maximum": 100} for k in self.get_boss_dimensions()},
                },
                "composite_score": {"type": "number", "minimum": 0, "maximum": 100},
                "routing_tier": {"type": "string", "enum": ["soap", "moderate", "elevated", "high", "ohshat"]},
                "is_non_idempotent": {"type": "boolean"},
                "critical_override_applied": {"type": "boolean"},
                "policy_provenance": {"type": "array"},
            },
        }

    def _flight_recorder_schema(self) -> Dict:
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "ADAM Flight Recorder Entry",
            "type": "object",
            "required": ["entry_id", "timestamp", "action_id", "agent_id", "evidence"],
            "properties": {
                "entry_id": {"type": "string", "format": "uuid"},
                "timestamp": {"type": "string", "format": "date-time"},
                "action_id": {"type": "string", "format": "uuid"},
                "intent_id": {"type": "string", "format": "uuid"},
                "agent_id": {"type": "string"},
                "agent_class": {"type": "string"},
                "evidence": {
                    "type": "object",
                    "properties": {
                        "action_type": {"type": "string"},
                        "input_state": {"type": "object"},
                        "output_state": {"type": "object"},
                        "boss_score": {"type": "object"},
                        "policy_evaluations": {"type": "array"},
                        "doctrine_version": {"type": "string"},
                    },
                },
                "hash_chain": {
                    "type": "object",
                    "properties": {
                        "previous_hash": {"type": "string"},
                        "current_hash": {"type": "string"},
                        "algorithm": {"type": "string", "default": "SHA-256"},
                    },
                },
                "cryptographic_proof": {"type": "object"},
                "tamper_evident": {"type": "boolean", "default": True},
            },
        }

    def _directors_config(self) -> Dict:
        return {
            "governance_model": "5-director-constitution",
            "company": self.company_name,
            "directors": {
                "ceo": {"title": "CEO", "domain": "Overall Enterprise Intent", "authority": "Final arbiter for irreconcilable conflicts"},
                "cfo": {"title": "CFO", "domain": "Financial Stewardship", "authority": "Financial doctrine, spending thresholds"},
                "legal": {"title": "Legal Director", "domain": "Regulatory Compliance", "authority": "Jurisdictional rules, legal personality"},
                "market": {"title": "Market Director", "domain": "External Posture", "authority": "Brand doctrine, competitive strategy"},
                "ciso": {"title": "CISO", "domain": "Security & Resilience", "authority": "Security doctrine, trust boundaries"},
            },
            "optional_directors": {
                "cpo": {"title": "CPO", "domain": "Product & Innovation", "activation": "3+ product lines"},
            },
            "interface_agents": ["Intent Interpretation Agent", "Human Trust Gateway Agent", "Explain-Back Agent"],
            "directors_raw": self.dna.get("governance", {}).get("directors", ""),
        }

    def _delegation_config(self) -> Dict:
        return {
            "model": "explicit-scoped-revocable-auditable",
            "properties": {
                "explicit": "Defined as CORE configuration",
                "scoped": "Bounded by domain, risk threshold, and financial cap",
                "revocable": "Any director can throttle autonomy to zero within seconds",
                "auditable": "Every delegation creates a Flight Recorder entry",
            },
            "delegation_raw": self.dna.get("governance", {}).get("delegation_model", ""),
        }

    def _exception_economy(self) -> Dict:
        boss = self.dna.get("boss_config", {})
        return {
            "principle": "Autonomy is the default state. Human involvement is earned by consequence.",
            "target_exceptions_per_director_per_day": "5-15",
            "escalation_structure": boss.get("exception_packets", ""),
            "feedback_loop": boss.get("feedback_loop", ""),
            "auto_threshold_adjustment": {
                "approved_90_percent": "Propose threshold relaxation",
                "rejected_50_percent": "Propose tighter constraint",
            },
            "doctrine_self_amendment": False,
        }
