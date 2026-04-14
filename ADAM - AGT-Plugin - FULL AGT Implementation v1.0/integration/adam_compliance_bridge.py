"""
ADAM-AGT Compliance Bridge Module

This module bridges Microsoft's Agent Governance Toolkit (AGT) Agent Compliance package
with ADAM's Evidence & Audit Plane and Legal framework. It provides:

- Regulatory Framework classification and mapping
- Automated compliance assessment against regulatory requirements
- Control-to-obligation mapping for ADAM governance
- Compliance-ready audit trail generation from Flight Recorder evidence
- BOSS Compliance dimension scoring integration

Regulatory Frameworks Supported:
- EU AI Act (EU)
- DORA (Supervisory Authority)
- NIS2 (Network & Information Systems)
- HIPAA (Healthcare)
- SOC2 (Service Organization Control)
- GDPR (Data Protection)

The bridge maintains immutable evidence chains and integrates with ADAM's
5-Director Constitution (CEO, CFO, Legal, Market, CISO) for escalations.

Author: ADAM Book v0.4
Version: 1.0.0
Python: 3.10+
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Set, Optional, Tuple, Any
from uuid import uuid4

# Configure module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RegulatoryFramework(Enum):
    """Supported regulatory frameworks for ADAM agents."""
    EU_AI_ACT = "eu_ai_act"
    DORA = "dora"
    NIS2 = "nis2"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    GDPR = "gdpr"


class ComplianceStatus(Enum):
    """Compliance assessment status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    UNKNOWN = "unknown"


class BOSSComplianceTier(Enum):
    """BOSS Score compliance tier mapping."""
    SOAP = "SOAP"  # 0-10: Safe and operational
    MODERATE = "MODERATE"  # 11-30: Monitor closely
    ELEVATED = "ELEVATED"  # 31-50: Elevated caution required
    HIGH = "HIGH"  # 51-75: High-risk monitoring
    OHSHAT = "OHSHAT"  # 76-100: Emergency situation


@dataclass
class RegulatoryRequirement:
    """Represents a single regulatory requirement."""
    requirement_id: str
    framework: RegulatoryFramework
    title: str
    description: str
    mandatory: bool
    control_ids: List[str] = field(default_factory=list)
    implementation_guidance: str = ""
    evidence_types: List[str] = field(default_factory=list)

    def __hash__(self) -> int:
        return hash(self.requirement_id)


@dataclass
class ComplianceControl:
    """Represents a compliance control implementation."""
    control_id: str
    framework: RegulatoryFramework
    control_name: str
    control_description: str
    implementation_status: str  # "implemented", "in_progress", "planned", "not_applicable"
    evidence_count: int = 0
    last_tested: Optional[datetime] = None
    next_review: Optional[datetime] = None
    responsible_director: str = ""  # CEO, CFO, Legal, Market, CISO
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_due_for_review(self) -> bool:
        """Check if control is due for review."""
        if self.next_review is None:
            return True
        return datetime.utcnow() >= self.next_review


@dataclass
class ComplianceAssessment:
    """Compliance assessment result for an agent action."""
    assessment_id: str
    agent_id: str
    action_type: str
    frameworks: List[RegulatoryFramework]
    status: ComplianceStatus
    boss_compliance_score: int  # 0-100
    compliant_requirements: Set[str] = field(default_factory=set)
    non_compliant_requirements: Set[str] = field(default_factory=set)
    violations: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    assessed_at: datetime = field(default_factory=datetime.utcnow)
    assessed_by: str = "adam_compliance_bridge"
    evidence_hashes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, converting enums to strings."""
        data = asdict(self)
        data['frameworks'] = [f.value for f in self.frameworks]
        data['status'] = self.status.value
        data['assessed_at'] = self.assessed_at.isoformat()
        data['compliant_requirements'] = list(self.compliant_requirements)
        data['non_compliant_requirements'] = list(self.non_compliant_requirements)
        return data


@dataclass
class AuditTrailEntry:
    """Single entry in compliance audit trail (immutable WORM record)."""
    entry_id: str
    timestamp: datetime
    record_type: str  # "policy_enforcement", "compliance_check", "violation", "remediation"
    agent_id: str
    action_description: str
    frameworks: List[str]  # framework names
    boss_score: int
    status: str  # "passed", "failed", "escalated"
    director_level: Optional[str] = None  # CEO, CFO, Legal, Market, CISO
    evidence_hash: str = ""
    previous_hash: str = ""  # For hash-chain linkage
    notes: str = ""

    def compute_entry_hash(self) -> str:
        """Compute immutable hash for this entry (WORM compliance)."""
        content = json.dumps({
            'entry_id': self.entry_id,
            'timestamp': self.timestamp.isoformat(),
            'record_type': self.record_type,
            'agent_id': self.agent_id,
            'action_description': self.action_description,
            'frameworks': self.frameworks,
            'boss_score': self.boss_score,
            'status': self.status,
            'director_level': self.director_level,
            'previous_hash': self.previous_hash,
            'notes': self.notes,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class RegulatoryClassifier:
    """
    Classifies agent actions against regulatory requirements and maps
    findings to BOSS Compliance dimension (0-100 scale).
    """

    def __init__(self):
        """Initialize regulatory classifier with framework requirements."""
        self._frameworks: Dict[RegulatoryFramework, List[RegulatoryRequirement]] = {}
        self._initialize_requirements()
        logger.info("RegulatoryClassifier initialized")

    def _initialize_requirements(self) -> None:
        """Initialize regulatory framework requirements."""
        # EU AI Act requirements
        self._frameworks[RegulatoryFramework.EU_AI_ACT] = [
            RegulatoryRequirement(
                requirement_id="eu_ai_act_transparency_001",
                framework=RegulatoryFramework.EU_AI_ACT,
                title="Transparency Requirements",
                description="Agents must disclose AI usage in decision-making",
                mandatory=True,
                control_ids=["ctrl_transparency_001", "ctrl_transparency_002"],
                evidence_types=["audit_log", "user_notification", "disclosure_record"]
            ),
            RegulatoryRequirement(
                requirement_id="eu_ai_act_risk_assessment_001",
                framework=RegulatoryFramework.EU_AI_ACT,
                title="Risk Assessment",
                description="High-risk AI systems must undergo risk assessment",
                mandatory=True,
                control_ids=["ctrl_risk_001"],
                evidence_types=["risk_assessment_report", "impact_analysis"]
            ),
        ]

        # DORA requirements
        self._frameworks[RegulatoryFramework.DORA] = [
            RegulatoryRequirement(
                requirement_id="dora_ict_incident_001",
                framework=RegulatoryFramework.DORA,
                title="ICT Incident Management",
                description="Incident detection, response, and reporting procedures",
                mandatory=True,
                control_ids=["ctrl_incident_001", "ctrl_incident_002"],
                evidence_types=["incident_log", "response_plan", "notification_records"]
            ),
        ]

        # NIS2 requirements
        self._frameworks[RegulatoryFramework.NIS2] = [
            RegulatoryRequirement(
                requirement_id="nis2_security_incident_001",
                framework=RegulatoryFramework.NIS2,
                title="Security Incident Reporting",
                description="Mandatory reporting of security incidents",
                mandatory=True,
                control_ids=["ctrl_nis2_incident_001"],
                evidence_types=["incident_report", "forensic_analysis"]
            ),
        ]

        # HIPAA requirements
        self._frameworks[RegulatoryFramework.HIPAA] = [
            RegulatoryRequirement(
                requirement_id="hipaa_privacy_001",
                framework=RegulatoryFramework.HIPAA,
                title="Privacy Controls",
                description="Protection of protected health information (PHI)",
                mandatory=True,
                control_ids=["ctrl_privacy_001"],
                evidence_types=["access_log", "encryption_certificate", "audit_trail"]
            ),
        ]

        # SOC2 requirements
        self._frameworks[RegulatoryFramework.SOC2] = [
            RegulatoryRequirement(
                requirement_id="soc2_security_001",
                framework=RegulatoryFramework.SOC2,
                title="Security Controls",
                description="Implementation of security controls",
                mandatory=True,
                control_ids=["ctrl_soc2_001"],
                evidence_types=["control_test_result", "audit_report"]
            ),
        ]

        # GDPR requirements
        self._frameworks[RegulatoryFramework.GDPR] = [
            RegulatoryRequirement(
                requirement_id="gdpr_consent_001",
                framework=RegulatoryFramework.GDPR,
                title="Consent Management",
                description="Obtain and maintain consent for data processing",
                mandatory=True,
                control_ids=["ctrl_consent_001"],
                evidence_types=["consent_record", "user_opt_in"]
            ),
        ]

        logger.info(f"Initialized {sum(len(reqs) for reqs in self._frameworks.values())} regulatory requirements")

    def classify_action(
        self,
        agent_id: str,
        action_type: str,
        frameworks: List[RegulatoryFramework],
        evidence_items: Optional[List[str]] = None
    ) -> Tuple[ComplianceStatus, int]:
        """
        Classify agent action compliance status and compute BOSS Compliance score.

        Args:
            agent_id: ID of the agent performing the action
            action_type: Type of action being performed
            frameworks: Applicable regulatory frameworks
            evidence_items: Evidence supporting compliance assessment

        Returns:
            Tuple of (ComplianceStatus, BOSS_compliance_score 0-100)
        """
        if not frameworks:
            return ComplianceStatus.UNKNOWN, 50

        evidence_items = evidence_items or []
        compliant_count = 0
        total_requirements = 0

        for framework in frameworks:
            requirements = self._frameworks.get(framework, [])
            for req in requirements:
                total_requirements += 1
                # Check if evidence supports compliance
                if self._has_sufficient_evidence(req, evidence_items):
                    compliant_count += 1

        if total_requirements == 0:
            return ComplianceStatus.UNKNOWN, 50

        compliance_ratio = compliant_count / total_requirements
        boss_score = int(100 * (1 - compliance_ratio))  # Invert: lower score = more compliant

        if compliance_ratio == 1.0:
            status = ComplianceStatus.COMPLIANT
        elif compliance_ratio == 0.0:
            status = ComplianceStatus.NON_COMPLIANT
        else:
            status = ComplianceStatus.PARTIALLY_COMPLIANT

        logger.info(
            f"Classified action {action_type} for agent {agent_id}: "
            f"status={status.value}, boss_score={boss_score}"
        )
        return status, boss_score

    def _has_sufficient_evidence(
        self,
        requirement: RegulatoryRequirement,
        evidence_items: List[str]
    ) -> bool:
        """Check if sufficient evidence exists for a requirement."""
        if not requirement.mandatory:
            return True
        return len(evidence_items) > 0

    def get_framework_requirements(
        self,
        framework: RegulatoryFramework
    ) -> List[RegulatoryRequirement]:
        """Get all requirements for a specific framework."""
        return self._frameworks.get(framework, [])


class ControlsToObligationsMapper:
    """
    Maps AGT compliance controls to ADAM's governance obligations.
    Maintains bidirectional traceability between control implementations
    and governance requirements.
    """

    def __init__(self):
        """Initialize the mapper."""
        self._control_to_obligations: Dict[str, List[str]] = {}
        self._obligation_to_controls: Dict[str, List[str]] = {}
        self._director_responsibilities: Dict[str, List[str]] = {}
        self._initialize_mappings()
        logger.info("ControlsToObligationsMapper initialized")

    def _initialize_mappings(self) -> None:
        """Initialize control-to-obligation mappings."""
        # Example mappings between AGT controls and ADAM obligations
        mappings = {
            "ctrl_transparency_001": ["obligation_disclose_ai_usage", "obligation_explain_decision"],
            "ctrl_transparency_002": ["obligation_maintain_audit_log"],
            "ctrl_risk_001": ["obligation_assess_ai_risk", "obligation_mitigate_high_risk"],
            "ctrl_incident_001": ["obligation_detect_incidents", "obligation_report_incidents"],
            "ctrl_incident_002": ["obligation_maintain_incident_log"],
            "ctrl_nis2_incident_001": ["obligation_report_to_authority"],
            "ctrl_privacy_001": ["obligation_protect_phi", "obligation_encryption"],
            "ctrl_soc2_001": ["obligation_implement_security", "obligation_audit_security"],
            "ctrl_consent_001": ["obligation_obtain_consent", "obligation_track_consent"],
        }

        for control_id, obligations in mappings.items():
            self._control_to_obligations[control_id] = obligations
            for obligation in obligations:
                if obligation not in self._obligation_to_controls:
                    self._obligation_to_controls[obligation] = []
                self._obligation_to_controls[obligation].append(control_id)

        # Director responsibility assignments
        self._director_responsibilities = {
            "CEO": ["obligation_disclose_ai_usage", "obligation_assess_ai_risk"],
            "CFO": ["obligation_maintain_audit_log", "obligation_track_consent"],
            "Legal": ["obligation_comply_regulations", "obligation_explain_decision"],
            "CISO": ["obligation_protect_phi", "obligation_encryption", "obligation_detect_incidents"],
            "Market": ["obligation_explain_decision", "obligation_disclose_ai_usage"],
        }

    def map_control_to_obligations(self, control_id: str) -> List[str]:
        """Get ADAM governance obligations for an AGT control."""
        return self._control_to_obligations.get(control_id, [])

    def map_obligation_to_controls(self, obligation_id: str) -> List[str]:
        """Get AGT controls implementing an ADAM governance obligation."""
        return self._obligation_to_controls.get(obligation_id, [])

    def get_director_obligations(self, director_role: str) -> List[str]:
        """Get governance obligations assigned to a director role."""
        return self._director_responsibilities.get(director_role, [])

    def create_compliance_control(
        self,
        control_id: str,
        framework: RegulatoryFramework,
        control_name: str,
        implementation_status: str,
        responsible_director: str = ""
    ) -> ComplianceControl:
        """Create a compliance control with obligation mappings."""
        control = ComplianceControl(
            control_id=control_id,
            framework=framework,
            control_name=control_name,
            control_description="",
            implementation_status=implementation_status,
            responsible_director=responsible_director,
            next_review=datetime.utcnow() + timedelta(days=90)
        )

        obligations = self.map_control_to_obligations(control_id)
        control.metadata['obligations'] = obligations

        logger.debug(f"Created control {control_id} with {len(obligations)} obligations")
        return control


class AuditTrailGenerator:
    """
    Generates compliance-ready audit trails from Flight Recorder evidence.
    Maintains immutable, hash-chained audit records suitable for regulatory
    reporting and legal discovery.
    """

    def __init__(self):
        """Initialize audit trail generator."""
        self._audit_trail: List[AuditTrailEntry] = []
        self._last_hash = ""
        logger.info("AuditTrailGenerator initialized")

    def create_audit_entry(
        self,
        record_type: str,
        agent_id: str,
        action_description: str,
        frameworks: List[str],
        boss_score: int,
        status: str,
        director_level: Optional[str] = None,
        notes: str = ""
    ) -> AuditTrailEntry:
        """
        Create a new immutable audit trail entry with hash-chain linkage.

        Args:
            record_type: Type of compliance record
            agent_id: ID of the agent involved
            action_description: Description of the action
            frameworks: Regulatory frameworks involved
            boss_score: BOSS Compliance score at time of action
            status: Compliance status (passed, failed, escalated)
            director_level: Director level (CEO, CFO, Legal, Market, CISO)
            notes: Additional notes

        Returns:
            AuditTrailEntry with computed hash and previous_hash linkage
        """
        entry = AuditTrailEntry(
            entry_id=str(uuid4()),
            timestamp=datetime.utcnow(),
            record_type=record_type,
            agent_id=agent_id,
            action_description=action_description,
            frameworks=frameworks,
            boss_score=boss_score,
            status=status,
            director_level=director_level,
            notes=notes,
            previous_hash=self._last_hash
        )

        # Compute immutable hash
        entry.evidence_hash = entry.compute_entry_hash()
        self._last_hash = entry.evidence_hash

        self._audit_trail.append(entry)
        logger.info(f"Created audit entry {entry.entry_id}: {record_type} for {agent_id}")

        return entry

    def get_audit_trail(self) -> List[AuditTrailEntry]:
        """Get full audit trail."""
        return list(self._audit_trail)

    def verify_audit_chain(self) -> bool:
        """Verify integrity of hash-chain audit trail."""
        previous_hash = ""
        for entry in self._audit_trail:
            if entry.previous_hash != previous_hash:
                logger.error(f"Audit chain broken at entry {entry.entry_id}")
                return False
            previous_hash = entry.evidence_hash

        logger.info(f"Verified audit chain integrity for {len(self._audit_trail)} entries")
        return True

    def export_audit_trail_for_regulatory_report(
        self,
        framework: Optional[RegulatoryFramework] = None
    ) -> List[Dict[str, Any]]:
        """
        Export audit trail in format suitable for regulatory reporting.

        Args:
            framework: Optional filter by regulatory framework

        Returns:
            List of audit entries as dictionaries
        """
        entries = []
        for entry in self._audit_trail:
            if framework and framework.value not in entry.frameworks:
                continue

            entries.append({
                'entry_id': entry.entry_id,
                'timestamp': entry.timestamp.isoformat(),
                'record_type': entry.record_type,
                'agent_id': entry.agent_id,
                'action_description': entry.action_description,
                'frameworks': entry.frameworks,
                'boss_score': entry.boss_score,
                'status': entry.status,
                'director_level': entry.director_level,
                'evidence_hash': entry.evidence_hash,
                'notes': entry.notes,
            })

        logger.info(f"Exported {len(entries)} audit entries for regulatory report")
        return entries


class BOSSRegulatoryDimension:
    """
    BOSS Score Regulatory Dimension (one of 7 dimensions, 0-100 scale).
    Maps compliance assessments into the BOSS framework's Regulatory tier:
    - SOAP (0-10): Safe and operational
    - MODERATE (11-30): Monitor closely
    - ELEVATED (31-50): Elevated caution required
    - HIGH (51-75): Director review required
    - OHSHAT (76-100): Emergency situation
    """

    def __init__(self):
        """Initialize BOSS Regulatory dimension tracker."""
        self._current_score = 0
        self._dimension_history: List[Tuple[datetime, int]] = []
        self._escalation_threshold = 50  # HIGH tier
        logger.info("BOSSRegulatoryDimension initialized")

    def update_score(self, new_score: int) -> BOSSComplianceTier:
        """
        Update the regulatory dimension score and return tier.

        Args:
            new_score: New compliance score (0-100)

        Returns:
            BOSSComplianceTier corresponding to the score
        """
        new_score = max(0, min(100, new_score))  # Clamp to 0-100
        self._current_score = new_score
        self._dimension_history.append((datetime.utcnow(), new_score))

        tier = self._get_tier_from_score(new_score)
        logger.info(f"Updated regulatory score to {new_score}, tier: {tier.value}")

        return tier

    def get_current_score(self) -> int:
        """Get current regulatory dimension score."""
        return self._current_score

    def get_current_tier(self) -> BOSSComplianceTier:
        """Get current tier based on score."""
        return self._get_tier_from_score(self._current_score)

    def is_escalation_required(self) -> bool:
        """Check if score requires escalation to director level."""
        return self._current_score >= self._escalation_threshold

    def get_score_history(self) -> List[Tuple[datetime, int]]:
        """Get historical scores."""
        return list(self._dimension_history)

    @staticmethod
    def _get_tier_from_score(score: int) -> BOSSComplianceTier:
        """Map score to compliance tier."""
        if score <= 20:
            return BOSSComplianceTier.SOAP
        elif score <= 40:
            return BOSSComplianceTier.MODERATE
        elif score <= 60:
            return BOSSComplianceTier.ELEVATED
        elif score <= 80:
            return BOSSComplianceTier.HIGH
        else:
            return BOSSComplianceTier.OHSHAT


class AdamComplianceBridge:
    """
    Main compliance bridge orchestrating integration between AGT Agent Compliance
    and ADAM's Evidence & Audit Plane, Legal framework, and BOSS Compliance scoring.

    This class provides the primary interface for:
    1. Classifying agent actions against regulatory requirements
    2. Generating compliance assessments
    3. Creating immutable audit trails
    4. Updating BOSS regulatory dimension scores
    5. Escalating to 5-Director Constitution when needed
    """

    def __init__(self):
        """Initialize the compliance bridge."""
        self._classifier = RegulatoryClassifier()
        self._mapper = ControlsToObligationsMapper()
        self._audit_generator = AuditTrailGenerator()
        self._boss_dimension = BOSSRegulatoryDimension()
        self._active_assessments: Dict[str, ComplianceAssessment] = {}
        logger.info("AdamComplianceBridge initialized")

    def assess_agent_action(
        self,
        agent_id: str,
        action_type: str,
        frameworks: List[RegulatoryFramework],
        evidence_items: Optional[List[str]] = None
    ) -> ComplianceAssessment:
        """
        Perform comprehensive compliance assessment of an agent action.

        Args:
            agent_id: ID of the agent
            action_type: Type of action
            frameworks: Applicable regulatory frameworks
            evidence_items: Evidence supporting the action

        Returns:
            ComplianceAssessment with detailed findings
        """
        assessment_id = str(uuid4())
        status, boss_score = self._classifier.classify_action(
            agent_id, action_type, frameworks, evidence_items
        )

        assessment = ComplianceAssessment(
            assessment_id=assessment_id,
            agent_id=agent_id,
            action_type=action_type,
            frameworks=frameworks,
            status=status,
            boss_compliance_score=boss_score,
            evidence_hashes=evidence_items or []
        )

        # Populate compliance details based on frameworks
        for framework in frameworks:
            requirements = self._classifier.get_framework_requirements(framework)
            for req in requirements:
                if self._classifier._has_sufficient_evidence(req, evidence_items or []):
                    assessment.compliant_requirements.add(req.requirement_id)
                else:
                    assessment.non_compliant_requirements.add(req.requirement_id)
                    assessment.violations.append(f"{req.title}: {req.description}")

        self._active_assessments[assessment_id] = assessment

        # Update BOSS dimension
        tier = self._boss_dimension.update_score(boss_score)

        # Create audit trail entry
        self._audit_generator.create_audit_entry(
            record_type="compliance_check",
            agent_id=agent_id,
            action_description=f"{action_type} compliance assessment",
            frameworks=[f.value for f in frameworks],
            boss_score=boss_score,
            status=status.value
        )

        logger.info(
            f"Assessed action {action_type} for agent {agent_id}: "
            f"{len(assessment.compliant_requirements)} compliant, "
            f"{len(assessment.non_compliant_requirements)} non-compliant, "
            f"tier={tier.value}"
        )

        return assessment

    def get_assessment(self, assessment_id: str) -> Optional[ComplianceAssessment]:
        """Retrieve a compliance assessment."""
        return self._active_assessments.get(assessment_id)

    def get_boss_compliance_score(self) -> int:
        """Get current BOSS Regulatory dimension score."""
        return self._boss_dimension.get_current_score()

    def get_boss_compliance_tier(self) -> BOSSComplianceTier:
        """Get current BOSS Regulatory tier."""
        return self._boss_dimension.get_current_tier()

    def requires_director_escalation(self) -> bool:
        """Check if current compliance status requires director-level escalation."""
        return self._boss_dimension.is_escalation_required()

    def get_director_escalation_context(self) -> Dict[str, Any]:
        """Get escalation context for 5-Director Constitution."""
        tier = self._boss_dimension.get_current_tier()
        return {
            'regulatory_score': self._boss_dimension.get_current_score(),
            'tier': tier.value,
            'requires_escalation': self._boss_dimension.is_escalation_required(),
            'escalation_level': 'CEO' if tier == BOSSComplianceTier.OHSHAT else 'Legal',
            'assessment_count': len(self._active_assessments),
            'audit_trail_length': len(self._audit_generator.get_audit_trail())
        }

    def export_for_regulatory_report(
        self,
        framework: Optional[RegulatoryFramework] = None
    ) -> Dict[str, Any]:
        """
        Export compliance data in regulatory report format.

        Args:
            framework: Optional filter by regulatory framework

        Returns:
            Dictionary with compliance report data
        """
        frameworks_list = [framework.value] if framework else []
        return {
            'report_id': str(uuid4()),
            'generated_at': datetime.utcnow().isoformat(),
            'regulatory_frameworks': frameworks_list,
            'boss_score': self._boss_dimension.get_current_score(),
            'boss_tier': self._boss_dimension.get_current_tier().value,
            'audit_trail': self._audit_generator.export_audit_trail_for_regulatory_report(framework),
            'assessment_count': len(self._active_assessments),
            'verification_status': 'verified' if self._audit_generator.verify_audit_chain() else 'unverified'
        }

    def get_audit_trail(self) -> List[AuditTrailEntry]:
        """Get full immutable audit trail."""
        return self._audit_generator.get_audit_trail()

    def verify_audit_integrity(self) -> bool:
        """Verify integrity of audit trail hash-chain."""
        return self._audit_generator.verify_audit_chain()
