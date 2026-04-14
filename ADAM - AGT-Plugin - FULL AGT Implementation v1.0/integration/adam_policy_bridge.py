"""
ADAM Policy Bridge Module

Bridges Microsoft's Agent Governance Toolkit (AGT) Agent OS policy engine with ADAM's
CORE Engine and Policy & Risk Plane. Translates ADAM governance rules and BOSS scores
into AGT policy formats (YAML, OPA Rego, Cedar) for enforcement.

Key Components:
- BOSSScoreMapper: Converts ADAM's 7-dimension BOSS scores to AGT policy contexts
- PolicyLanguageTranslator: Translates ADAM rules to OPA Rego and Cedar formats
- LangGraphPolicyHandler: Integrates with LangGraph execution for policy checkpoints
- AdamPolicyBridge: Main orchestration class for policy evaluation flows

ADAM Concepts:
- CORE Engine: Culture/Objectives/Rules/Expectations repository
- BOSS Score: 7-dimensional risk assessment (0-100 scale) with 5 tiers
  * SOAP (0-10): Safe and operational
  * MODERATE (11-30): Monitor closely
  * ELEVATED (31-50): Elevated caution required
  * HIGH (51-75): High-risk monitoring
  * OHSHAT (76-100): Emergency situation
- Exception Economy: Autonomy budgets and escalation routing
- Policy & Risk Plane: Runtime policy enforcement

Author: ADAM Framework
Version: 1.0.0
Python: 3.10+
"""

import asyncio
import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from abc import ABC, abstractmethod

__version__ = "1.0.0"
__author__ = "ADAM Framework"

# Configure logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


# ============================================================================
# Enums and Constants
# ============================================================================

class BOSSTier(str, Enum):
    """BOSS Score escalation tiers based on 0-100 scale."""
    SOAP = "SOAP"           # 0-10: Safe and operational
    MODERATE = "MODERATE"   # 11-30: Monitor closely
    ELEVATED = "ELEVATED"   # 31-50: Elevated caution required
    HIGH = "HIGH"           # 51-75: High-risk monitoring
    OHSHAT = "OHSHAT"       # 76-100: Emergency situation


class BOSSDimension(str, Enum):
    """ADAM BOSS Score's 7 dimensions."""
    SECURITY_IMPACT = "security_impact"
    SOVEREIGNTY_ACTION = "sovereignty_action"
    FINANCIAL_EXPOSURE = "financial_exposure"
    REGULATORY_IMPACT = "regulatory_impact"
    REPUTATIONAL_RISK = "reputational_risk"
    RIGHTS_CERTAINTY = "rights_certainty"
    DOCTRINAL_ALIGNMENT = "doctrinal_alignment"


class PolicyLanguage(str, Enum):
    """Supported policy languages for AGT."""
    YAML = "yaml"
    OPA_REGO = "opa-rego"
    CEDAR = "cedar"


class PolicyAction(str, Enum):
    """Policy enforcement actions."""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    ESCALATE = "escalate"
    AUDIT = "audit"
    KILL_SWITCH = "kill_switch"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class BOSSScore:
    """Represents an ADAM BOSS Score with all 7 dimensions."""

    security_impact: float  # Security Impact dimension (0-100)
    sovereignty_action: float  # Sovereignty Action dimension (0-100)
    financial_exposure: float  # Financial Exposure dimension (0-100)
    regulatory_impact: float  # Regulatory Impact dimension (0-100)
    reputational_risk: float  # Reputational Risk dimension (0-100)
    rights_certainty: float  # Rights Certainty dimension (0-100)
    doctrinal_alignment: float  # Doctrinal Alignment dimension (0-100)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """Validate BOSS score dimensions are within valid range."""
        for dim_name in BOSSDimension:
            value = getattr(self, dim_name.value)
            if not 0 <= value <= 100:
                raise ValueError(
                    f"{dim_name.value} must be between 0-100, got {value}"
                )

    @property
    def composite_score(self) -> float:
        """Calculate composite BOSS score as average of all dimensions."""
        return (
            self.security_impact + self.sovereignty_action + self.financial_exposure +
            self.regulatory_impact + self.reputational_risk + self.rights_certainty + self.doctrinal_alignment
        ) / 7.0

    @property
    def tier(self) -> BOSSTier:
        """Determine escalation tier based on composite score."""
        score = self.composite_score
        if score <= 10:
            return BOSSTier.SOAP
        elif score <= 30:
            return BOSSTier.MODERATE
        elif score <= 50:
            return BOSSTier.ELEVATED
        elif score <= 75:
            return BOSSTier.HIGH
        else:
            return BOSSTier.OHSHAT

    @property
    def threat_vector(self) -> Dict[str, float]:
        """Identify highest-risk dimensions."""
        return {
            dim.value: getattr(self, dim.value)
            for dim in BOSSDimension
        }


@dataclass
class PolicyContext:
    """Policy evaluation context derived from BOSS score and ADAM state."""

    boss_score: BOSSScore
    invocation_contract_id: str
    agent_id: str
    action_id: str
    resource_id: str
    requested_permissions: Set[str]
    enforcement_hooks: Dict[str, bool] = field(default_factory=dict)  # pre, during, post, exception
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)
    escalation_budget_remaining: float = 1000.0  # autonomy budget

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for policy evaluation."""
        return {
            "boss_score": asdict(self.boss_score),
            "invocation_contract_id": self.invocation_contract_id,
            "agent_id": self.agent_id,
            "action_id": self.action_id,
            "resource_id": self.resource_id,
            "requested_permissions": list(self.requested_permissions),
            "enforcement_hooks": self.enforcement_hooks,
            "escalation_budget_remaining": self.escalation_budget_remaining,
        }


@dataclass
class PolicyEvaluationResult:
    """Result of policy evaluation."""

    policy_id: str
    action: PolicyAction
    allowed: bool
    reason: str
    matching_dimensions: List[BOSSDimension]
    required_approvals: List[str] = field(default_factory=list)
    escalation_path: Optional[str] = None
    cost_to_budget: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    evidence_hash: str = ""

    def __post_init__(self):
        """Generate cryptographic evidence hash for Flight Recorder."""
        evidence_data = json.dumps({
            "policy_id": self.policy_id,
            "action": self.action.value,
            "allowed": self.allowed,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
        }, sort_keys=True)
        self.evidence_hash = hashlib.sha256(evidence_data.encode()).hexdigest()


# ============================================================================
# BOSS Score Mapper
# ============================================================================

class BOSSScoreMapper:
    """Maps ADAM BOSS scores to AGT policy contexts and dimensions."""

    # Dimension to policy domain mapping
    DIMENSION_TO_POLICY_DOMAIN = {
        BOSSDimension.SECURITY_IMPACT: "security",
        BOSSDimension.SOVEREIGNTY_ACTION: "sovereignty",
        BOSSDimension.FINANCIAL_EXPOSURE: "finance",
        BOSSDimension.REGULATORY_IMPACT: "compliance",
        BOSSDimension.REPUTATIONAL_RISK: "reputation",
        BOSSDimension.RIGHTS_CERTAINTY: "governance",
        BOSSDimension.DOCTRINAL_ALIGNMENT: "doctrine",
    }

    # Tier to policy template mapping
    TIER_TO_DEFAULT_POLICIES = {
        BOSSTier.SOAP: [],  # No special policies
        BOSSTier.MODERATE: ["audit-required"],
        BOSSTier.ELEVATED: ["escalate-to-governor-agent"],
        BOSSTier.HIGH: ["require-multi-approval", "real-time-monitoring"],
        BOSSTier.OHSHAT: ["kill-switch-armed", "immediate-escalation"],
    }

    def __init__(self):
        """Initialize BOSS score mapper."""
        self.logger = logging.getLogger(f"{__name__}.BOSSScoreMapper")

    def map_score_to_agt_context(
        self,
        boss_score: BOSSScore,
        invocation_contract_id: str,
        agent_id: str,
    ) -> PolicyContext:
        """
        Map ADAM BOSS score to AGT policy context.

        Args:
            boss_score: ADAM BOSS score with all 7 dimensions
            invocation_contract_id: ADAM invocation contract ID
            agent_id: Agent executing the invocation

        Returns:
            PolicyContext ready for AGT evaluation
        """
        self.logger.info(
            f"Mapping BOSS score tier={boss_score.tier} "
            f"composite={boss_score.composite_score:.1f} "
            f"to AGT policy context"
        )

        # Determine enforcement hooks based on tier
        enforcement_hooks = self._determine_enforcement_hooks(boss_score.tier)

        # Calculate escalation budget impact
        budget_impact = self._calculate_budget_impact(boss_score)

        context = PolicyContext(
            boss_score=boss_score,
            invocation_contract_id=invocation_contract_id,
            agent_id=agent_id,
            action_id=str(uuid.uuid4()),
            resource_id=f"adam-invocation-{invocation_contract_id}",
            requested_permissions=self._infer_permissions_from_score(boss_score),
            enforcement_hooks=enforcement_hooks,
            escalation_budget_remaining=1000.0 - budget_impact,
        )

        return context

    def get_applicable_policies(self, boss_score: BOSSScore) -> List[str]:
        """
        Determine which AGT policies apply based on BOSS score tier.

        Args:
            boss_score: ADAM BOSS score

        Returns:
            List of policy IDs to apply
        """
        tier = boss_score.tier
        base_policies = self.TIER_TO_DEFAULT_POLICIES.get(tier, [])

        # Add dimension-specific policies for high-risk dimensions
        dimension_policies = []
        for dimension, value in boss_score.threat_vector.items():
            if value >= 60:  # ELEVATED or higher
                domain = self.DIMENSION_TO_POLICY_DOMAIN.get(dimension, "unknown")
                dimension_policies.append(f"enforce-{domain}-controls")

        return base_policies + dimension_policies

    def _determine_enforcement_hooks(self, tier: BOSSTier) -> Dict[str, bool]:
        """Determine which ADAM enforcement hooks to activate."""
        hooks = {
            "pre_decision_validation": tier != BOSSTier.SOAP,
            "during_execution_monitoring": tier in (BOSSTier.ELEVATED, BOSSTier.HIGH, BOSSTier.OHSHAT),
            "post_completion_validation": tier in (BOSSTier.HIGH, BOSSTier.OHSHAT),
            "exception_handling": tier in (BOSSTier.HIGH, BOSSTier.OHSHAT),
        }
        return hooks

    def _calculate_budget_impact(self, boss_score: BOSSScore) -> float:
        """Calculate impact on autonomy budget based on BOSS score tier."""
        tier = boss_score.tier
        impact_map = {
            BOSSTier.SOAP: 0,
            BOSSTier.MODERATE: 10,
            BOSSTier.ELEVATED: 50,
            BOSSTier.HIGH: 150,
            BOSSTier.OHSHAT: 500,
        }
        return impact_map.get(tier, 0)

    def _infer_permissions_from_score(self, boss_score: BOSSScore) -> Set[str]:
        """Infer required permissions based on BOSS score dimensions."""
        permissions = {"invoke_action"}  # Base permission

        # Add dimension-specific permissions
        if boss_score.financial_exposure > 60:
            permissions.add("financial_approval")
        if boss_score.regulatory_impact > 60:
            permissions.add("compliance_review")
        if boss_score.security_impact > 70:
            permissions.add("security_approval")
        if boss_score.composite_score > 70:
            permissions.add("escalate_to_director")

        return permissions


# ============================================================================
# Policy Language Translator
# ============================================================================

class PolicyLanguageTranslator:
    """Translates ADAM governance rules to OPA Rego and Cedar policy formats."""

    def __init__(self):
        """Initialize policy language translator."""
        self.logger = logging.getLogger(f"{__name__}.PolicyLanguageTranslator")

    def translate_to_opa_rego(
        self,
        policy_name: str,
        boss_context: PolicyContext,
        target_action: PolicyAction = PolicyAction.ALLOW,
    ) -> str:
        """
        Translate ADAM policy to OPA Rego format.

        Args:
            policy_name: Name of the policy
            boss_context: Policy context with BOSS score
            target_action: Default action if policy matches

        Returns:
            OPA Rego policy as string
        """
        tier = boss_context.boss_score.tier

        rego_policy = f"""
# Auto-translated ADAM policy: {policy_name}
# BOSS Tier: {tier.value}
# Composite Score: {boss_context.boss_score.composite_score:.1f}

package adam.policies.{policy_name.replace('-', '_')}

import data.adam.boss
import data.adam.exception_economy

# Default decision
default allow = false

# SOAP tier - permissive
allow {{
    boss.composite_score <= 20
    input.agent_id in data.authorized_agents
}}

# MODERATE tier - audit required
allow {{
    boss.composite_score <= 40
    input.agent_id in data.authorized_agents
    input.audit_consent == true
}}

# ELEVATED tier - escalation required
allow {{
    boss.composite_score <= 60
    input.agent_id in data.authorized_agents
    input.governor_agent_approval == true
}}

# HIGH tier - multi-approval required
allow {{
    boss.composite_score <= 75
    input.agent_id in data.authorized_agents
    input.multi_approvals >= 2
    exception_economy.budget_available(input.budget_impact)
}}

# OHSHAT tier - emergency protocol
deny {{
    boss.composite_score > 75
    input.emergency_override != true
}}

# High-risk dimensions trigger escalation
require_escalation {{
    input.boss_score.financial_exposure > 60
}} with escalation_path as "/director/cfo"

require_escalation {{
    input.boss_score.regulatory_impact > 60
}} with escalation_path as "/director/legal"

require_escalation {{
    input.boss_score.security_impact > 70
}} with escalation_path as "/director/ciso"

# Exception economy integration
insufficient_budget {{
    input.escalation_budget_remaining < input.budget_impact
}}
"""
        self.logger.debug(f"Translated {policy_name} to OPA Rego")
        return rego_policy

    def translate_to_cedar(
        self,
        policy_name: str,
        boss_context: PolicyContext,
    ) -> str:
        """
        Translate ADAM policy to AWS Cedar format.

        Args:
            policy_name: Name of the policy
            boss_context: Policy context with BOSS score

        Returns:
            Cedar policy as string
        """
        tier = boss_context.boss_score.tier

        cedar_policy = f"""
@namespace("{policy_name}")
@description("ADAM policy: {policy_name} (Tier: {tier.value})")

permit(
    principal,
    action,
    resource,
    context
)
when {{
    // Context required for SOAP tier
    if context.boss_tier == "SOAP" then
        principal has authorized_agents &&
        principal in principal.authorized_agents

    // MODERATE tier adds audit requirement
    else if context.boss_tier == "MODERATE" then
        principal has authorized_agents &&
        principal in principal.authorized_agents &&
        context.audit_consent == true

    // ELEVATED tier requires domain governance approval
    else if context.boss_tier == "ELEVATED" then
        principal has authorized_agents &&
        principal in principal.authorized_agents &&
        context.has_domain_approval == true

    // HIGH tier requires multiple approvals
    else if context.boss_tier == "HIGH" then
        principal has authorized_agents &&
        principal in principal.authorized_agents &&
        context.approval_count >= 2 &&
        context.has_budget == true

    // OHSHAT tier only with emergency override
    else if context.boss_tier == "OHSHAT" then
        context.emergency_override == true &&
        context.director_authorization == true
    else
        false
}};

forbid(
    principal,
    action,
    resource,
    context
)
when {{
    context.boss_tier == "OHSHAT" &&
    !has(context.emergency_override)
}};

"""
        self.logger.debug(f"Translated {policy_name} to Cedar format")
        return cedar_policy

    def translate_to_yaml(
        self,
        policy_name: str,
        boss_context: PolicyContext,
    ) -> Dict[str, Any]:
        """
        Translate ADAM policy to YAML-compatible dictionary format.

        Args:
            policy_name: Name of the policy
            boss_context: Policy context with BOSS score

        Returns:
            YAML-serializable policy dictionary
        """
        tier = boss_context.boss_score.tier

        yaml_policy = {
            "apiVersion": "adam.governance/v1",
            "kind": "AdamPolicy",
            "metadata": {
                "name": policy_name,
                "namespace": "adam-governance",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "spec": {
                "description": f"Auto-translated ADAM policy for {policy_name}",
                "bossTier": tier.value,
                "compositeScore": round(boss_context.boss_score.composite_score, 2),
                "threatVector": boss_context.boss_score.threat_vector,
                "rules": self._generate_yaml_rules(tier, boss_context),
                "escalationPath": self._get_escalation_path(boss_context.boss_score),
                "enforcementHooks": boss_context.enforcement_hooks,
                "budgetImpact": {
                    "remainingBudget": boss_context.escalation_budget_remaining,
                    "costPerExecution": self._calculate_policy_cost(tier),
                },
            },
        }

        self.logger.debug(f"Translated {policy_name} to YAML format")
        return yaml_policy

    def _generate_yaml_rules(
        self,
        tier: BOSSTier,
        boss_context: PolicyContext,
    ) -> List[Dict[str, Any]]:
        """Generate YAML-formatted policy rules based on tier."""
        rules = []

        rule_templates = {
            BOSSTier.SOAP: [
                {"action": "allow", "condition": "authorized_agent", "priority": 1},
            ],
            BOSSTier.MODERATE: [
                {"action": "audit", "condition": "log_action", "priority": 1},
                {"action": "allow", "condition": "authorized_agent", "priority": 2},
            ],
            BOSSTier.ELEVATED: [
                {"action": "escalate", "target": "governor_agent", "priority": 1},
                {"action": "allow", "condition": "has_approval", "priority": 2},
            ],
            BOSSTier.HIGH: [
                {"action": "escalate", "target": "director_council", "priority": 1},
                {"action": "require_multi_approval", "count": 2, "priority": 2},
                {"action": "deny", "condition": "insufficient_budget", "priority": 0},
            ],
            BOSSTier.OHSHAT: [
                {"action": "kill_switch", "armed": True, "priority": 0},
                {"action": "deny", "condition": "no_emergency_override", "priority": 0},
                {"action": "immediate_escalation", "target": "ceo", "priority": 1},
            ],
        }

        return rule_templates.get(tier, [])

    def _get_escalation_path(self, boss_score: BOSSScore) -> Optional[Dict[str, str]]:
        """Determine escalation path based on threat vector."""
        highest_dimension = max(
            boss_score.threat_vector.items(),
            key=lambda x: x[1]
        )

        dimension_to_director = {
            BOSSDimension.SECURITY_IMPACT.value: "/director/ciso",
            BOSSDimension.SOVEREIGNTY_ACTION.value: "/director/operations",
            BOSSDimension.FINANCIAL_EXPOSURE.value: "/director/cfo",
            BOSSDimension.REGULATORY_IMPACT.value: "/director/legal",
            BOSSDimension.REPUTATIONAL_RISK.value: "/director/market",
            BOSSDimension.RIGHTS_CERTAINTY.value: "/director/ceo",
            BOSSDimension.DOCTRINAL_ALIGNMENT.value: "/director/ceo",
        }

        if highest_dimension[1] > 60:
            return {
                "primary": dimension_to_director.get(highest_dimension[0], "/director/ceo"),
                "reason": f"High {highest_dimension[0]} score: {highest_dimension[1]}",
            }

        return None

    def _calculate_policy_cost(self, tier: BOSSTier) -> float:
        """Calculate autonomy budget cost per policy execution."""
        cost_map = {
            BOSSTier.SOAP: 0.0,
            BOSSTier.MODERATE: 5.0,
            BOSSTier.ELEVATED: 25.0,
            BOSSTier.HIGH: 75.0,
            BOSSTier.OHSHAT: 250.0,
        }
        return cost_map.get(tier, 0.0)


# ============================================================================
# LangGraph Policy Handler
# ============================================================================

class LangGraphPolicyHandler:
    """Integrates ADAM policies with LangGraph execution for policy checkpoints."""

    def __init__(self):
        """Initialize LangGraph policy handler."""
        self.logger = logging.getLogger(f"{__name__}.LangGraphPolicyHandler")
        self.evaluation_history: List[PolicyEvaluationResult] = []

    async def evaluate_policy_checkpoint(
        self,
        policy_context: PolicyContext,
        checkpoint_type: str = "pre_decision",
    ) -> PolicyEvaluationResult:
        """
        Evaluate policy at a LangGraph execution checkpoint.

        Args:
            policy_context: Policy context with BOSS score and invocation details
            checkpoint_type: Type of checkpoint (pre_decision, during, post, exception)

        Returns:
            Policy evaluation result
        """
        self.logger.info(
            f"Evaluating policy at {checkpoint_type} checkpoint "
            f"for invocation {policy_context.invocation_contract_id}"
        )

        # Simulate async policy evaluation
        await asyncio.sleep(0.001)  # <0.1ms latency target

        # Determine policy action based on BOSS tier
        action, reason = self._determine_policy_action(
            policy_context,
            checkpoint_type
        )

        result = PolicyEvaluationResult(
            policy_id=f"adam-{checkpoint_type}-{policy_context.action_id}",
            action=action,
            allowed=action in (PolicyAction.ALLOW, PolicyAction.AUDIT),
            reason=reason,
            matching_dimensions=self._find_matching_dimensions(policy_context.boss_score),
            required_approvals=self._determine_required_approvals(
                policy_context,
                action
            ),
            escalation_path=self._get_escalation_path(policy_context.boss_score),
            cost_to_budget=policy_context.escalation_budget_remaining,
        )

        self.evaluation_history.append(result)
        return result

    async def apply_multi_checkpoint_evaluation(
        self,
        policy_context: PolicyContext,
    ) -> Dict[str, PolicyEvaluationResult]:
        """
        Apply policy evaluation across all ADAM enforcement hooks.

        Args:
            policy_context: Policy context for evaluation

        Returns:
            Dictionary of evaluation results per checkpoint
        """
        self.logger.info(
            f"Applying multi-checkpoint evaluation across {sum(policy_context.enforcement_hooks.values())} active hooks"
        )

        results = {}
        checkpoint_types = [
            ("pre_decision_validation", "pre_decision"),
            ("during_execution_monitoring", "during"),
            ("post_completion_validation", "post"),
            ("exception_handling", "exception"),
        ]

        for hook_name, checkpoint_type in checkpoint_types:
            if policy_context.enforcement_hooks.get(hook_name, False):
                result = await self.evaluate_policy_checkpoint(
                    policy_context,
                    checkpoint_type
                )
                results[hook_name] = result

                # Stop on deny
                if not result.allowed and checkpoint_type != "post":
                    self.logger.warning(
                        f"Policy denied at {checkpoint_type} checkpoint"
                    )
                    break

        return results

    def _determine_policy_action(
        self,
        policy_context: PolicyContext,
        checkpoint_type: str,
    ) -> Tuple[PolicyAction, str]:
        """Determine policy action based on BOSS score and checkpoint type."""
        tier = policy_context.boss_score.tier

        # OHSHAT tier always requires kill switch at critical checkpoints
        if tier == BOSSTier.OHSHAT:
            if checkpoint_type in ("pre_decision", "exception"):
                return (
                    PolicyAction.KILL_SWITCH,
                    "OHSHAT tier triggers kill switch activation"
                )

        # HIGH tier requires approval at pre-decision
        if tier == BOSSTier.HIGH and checkpoint_type == "pre_decision":
            return (
                PolicyAction.REQUIRE_APPROVAL,
                f"HIGH tier requires multi-approval at {checkpoint_type}"
            )

        # ELEVATED tier escalates to governor agent
        if tier == BOSSTier.ELEVATED and checkpoint_type == "pre_decision":
            return (
                PolicyAction.ESCALATE,
                f"ELEVATED tier escalates to governor agent at {checkpoint_type}"
            )

        # MODERATE tier requires audit
        if tier == BOSSTier.MODERATE:
            return (
                PolicyAction.AUDIT,
                f"MODERATE tier requires audit logging at {checkpoint_type}"
            )

        # Default: allow
        return (
            PolicyAction.ALLOW,
            f"{tier.value} tier allows action at {checkpoint_type}"
        )

    def _find_matching_dimensions(self, boss_score: BOSSScore) -> List[BOSSDimension]:
        """Find BOSS dimensions that triggered the policy."""
        matching = []
        for dimension in BOSSDimension:
            value = getattr(boss_score, dimension.value)
            # Consider dimensions > 60 as matching (ELEVATED or higher)
            if value > 60:
                matching.append(dimension)
        return matching

    def _determine_required_approvals(
        self,
        policy_context: PolicyContext,
        action: PolicyAction,
    ) -> List[str]:
        """Determine which approvals are required."""
        if action == PolicyAction.ALLOW:
            return []

        approvals = []
        threat_vector = policy_context.boss_score.threat_vector

        # Map high-risk dimensions to required approvals
        if threat_vector.get(BOSSDimension.FINANCIAL_EXPOSURE.value, 0) > 60:
            approvals.append("cfo_approval")
        if threat_vector.get(BOSSDimension.REGULATORY_IMPACT.value, 0) > 60:
            approvals.append("legal_approval")
        if threat_vector.get(BOSSDimension.SECURITY_IMPACT.value, 0) > 70:
            approvals.append("ciso_approval")
        if threat_vector.get(BOSSDimension.REPUTATIONAL_RISK.value, 0) > 60:
            approvals.append("market_director_approval")

        return approvals if approvals else ["general_approval"]

    def _get_escalation_path(self, boss_score: BOSSScore) -> Optional[str]:
        """Get escalation path for high-risk scenarios."""
        threat_vector = boss_score.threat_vector
        max_dimension = max(threat_vector.items(), key=lambda x: x[1])

        if max_dimension[1] > 70:
            director_map = {
                BOSSDimension.SECURITY_IMPACT.value: "ciso",
                BOSSDimension.SOVEREIGNTY_ACTION.value: "operations",
                BOSSDimension.FINANCIAL_EXPOSURE.value: "cfo",
                BOSSDimension.REGULATORY_IMPACT.value: "legal",
                BOSSDimension.REPUTATIONAL_RISK.value: "market",
                BOSSDimension.RIGHTS_CERTAINTY.value: "ceo",
                BOSSDimension.DOCTRINAL_ALIGNMENT.value: "ceo",
            }
            return f"/director/{director_map.get(max_dimension[0], 'ceo')}"

        return None


# ============================================================================
# Main ADAM Policy Bridge
# ============================================================================

class AdamPolicyBridge:
    """
    Main orchestration class for ADAM-AGT policy integration.

    Orchestrates the complete policy evaluation flow from ADAM invocation contracts
    through AGT Agent OS, managing BOSS scores, policy translation, and enforcement.
    """

    def __init__(self):
        """Initialize ADAM Policy Bridge."""
        self.logger = logging.getLogger(__name__)
        self.boss_mapper = BOSSScoreMapper()
        self.translator = PolicyLanguageTranslator()
        self.langraph_handler = LangGraphPolicyHandler()
        self.policy_cache: Dict[str, Any] = {}
        self.evaluation_metrics = {
            "total_evaluations": 0,
            "allowed": 0,
            "denied": 0,
            "escalated": 0,
            "avg_evaluation_time_ms": 0.0,
        }

    async def evaluate_invocation(
        self,
        boss_score: BOSSScore,
        invocation_contract_id: str,
        agent_id: str,
        target_language: PolicyLanguage = PolicyLanguage.YAML,
    ) -> Dict[str, Any]:
        """
        Main entry point: evaluate an ADAM invocation contract.

        Args:
            boss_score: ADAM BOSS score for the invocation
            invocation_contract_id: Unique ID of the invocation contract
            agent_id: Agent executing the invocation
            target_language: Preferred policy language (YAML/OPA/Cedar)

        Returns:
            Comprehensive evaluation result with policies and recommendations
        """
        import time
        start_time = time.time()

        self.logger.info(
            f"Evaluating invocation {invocation_contract_id} "
            f"for agent {agent_id} at {boss_score.tier} tier"
        )

        # Step 1: Map BOSS score to policy context
        policy_context = self.boss_mapper.map_score_to_agt_context(
            boss_score,
            invocation_contract_id,
            agent_id,
        )

        # Step 2: Determine applicable policies
        applicable_policies = self.boss_mapper.get_applicable_policies(boss_score)

        # Step 3: Translate policies to target language
        translated_policies = {}
        for policy_name in applicable_policies:
            if target_language == PolicyLanguage.OPA_REGO:
                translated_policies[policy_name] = (
                    self.translator.translate_to_opa_rego(
                        policy_name,
                        policy_context,
                    )
                )
            elif target_language == PolicyLanguage.CEDAR:
                translated_policies[policy_name] = (
                    self.translator.translate_to_cedar(
                        policy_name,
                        policy_context,
                    )
                )
            else:  # YAML
                translated_policies[policy_name] = (
                    self.translator.translate_to_yaml(
                        policy_name,
                        policy_context,
                    )
                )

        # Step 4: Apply multi-checkpoint evaluation
        checkpoint_results = await self.langraph_handler.apply_multi_checkpoint_evaluation(
            policy_context
        )

        # Step 5: Aggregate results
        overall_allowed = all(r.allowed for r in checkpoint_results.values())
        evaluation_time = (time.time() - start_time) * 1000  # ms

        # Update metrics
        self._update_metrics(overall_allowed, evaluation_time, checkpoint_results)

        result = {
            "invocation_contract_id": invocation_contract_id,
            "agent_id": agent_id,
            "boss_score": asdict(boss_score),
            "boss_tier": boss_score.tier.value,
            "composite_score": round(boss_score.composite_score, 2),
            "threat_vector": boss_score.threat_vector,
            "overall_allowed": overall_allowed,
            "applicable_policies": applicable_policies,
            "translated_policies": translated_policies,
            "checkpoint_results": {
                k: {
                    "action": v.action.value,
                    "allowed": v.allowed,
                    "reason": v.reason,
                    "evidence_hash": v.evidence_hash,
                }
                for k, v in checkpoint_results.items()
            },
            "escalation_budget_remaining": policy_context.escalation_budget_remaining,
            "evaluation_time_ms": round(evaluation_time, 3),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self.logger.info(f"Evaluation result: allowed={overall_allowed}")
        return result

    def get_metrics(self) -> Dict[str, Any]:
        """Get policy bridge evaluation metrics."""
        return self.evaluation_metrics.copy()

    def _update_metrics(
        self,
        allowed: bool,
        evaluation_time_ms: float,
        checkpoint_results: Dict[str, PolicyEvaluationResult],
    ):
        """Update evaluation metrics."""
        self.evaluation_metrics["total_evaluations"] += 1
        if allowed:
            self.evaluation_metrics["allowed"] += 1
        else:
            self.evaluation_metrics["denied"] += 1

        # Count escalations
        for result in checkpoint_results.values():
            if result.action == PolicyAction.ESCALATE:
                self.evaluation_metrics["escalated"] += 1
                break

        # Update average time
        total = self.evaluation_metrics["total_evaluations"]
        current_avg = self.evaluation_metrics["avg_evaluation_time_ms"]
        self.evaluation_metrics["avg_evaluation_time_ms"] = (
            (current_avg * (total - 1) + evaluation_time_ms) / total
        )


# ============================================================================
# Module initialization and exports
# ============================================================================

def create_policy_bridge() -> AdamPolicyBridge:
    """
    Factory function to create a configured ADAM Policy Bridge.

    Returns:
        Initialized AdamPolicyBridge instance
    """
    return AdamPolicyBridge()


if __name__ == "__main__":
    # Example usage
    logger.info(f"ADAM Policy Bridge v{__version__}")
