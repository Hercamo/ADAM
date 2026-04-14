"""
ADAM DNA Tool - DNA Configuration Builder
Accumulates DNA configuration data from the conversational process and
produces the DNA JSON that feeds into the existing DNA Deployment Tool.
"""

import json
import os
import copy
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog

from app.models.session import (
    Session, DNAPhase, DNAData, SectionProgress,
    PHASE_SECTION_MAP, PHASE_TITLES,
)

logger = structlog.get_logger()

# The full question inventory that maps to the DNA Questionnaire
QUESTION_INVENTORY = {
    "1": {
        "1.1.1": "Legal name, incorporation jurisdiction, founding date",
        "1.1.2": "Mission statement",
        "1.1.3": "Vision statement",
        "1.1.4": "Core principles as prioritized trade-off list",
        "1.1.5": "Sacred boundaries — things ADAM must NEVER do",
        "1.1.6": "Legal entity structure and jurisdictional implications",
        "1.2.1": "Human director roles — accountability, authority, veto scope",
        "1.2.2": "Optional director roles beyond core five",
        "1.2.3": "Delegation model — how directors delegate to ADAM",
        "1.2.4": "Director conflict resolution mechanism",
    },
    "2": {
        "2.1.1": "Values as trade-off priorities",
        "2.1.2": "Behavioral norms",
        "2.1.3": "Failure philosophy",
        "2.1.4": "Decision philosophy",
        "2.2.1": "External brand posture",
        "2.2.2": "Internal optimization posture",
        "2.2.3": "Posture conflict rules",
    },
    "3": {
        "3.1.1": "Mandates — absolute requirements",
        "3.1.2": "Mandate enforcement and escalation",
        "3.2.1": "Current fiscal year goals",
        "3.2.2": "Goal priority ordering",
        "3.2.3": "Planning/review cadence",
        "3.3.1": "Aspirational objectives",
        "3.3.2": "Progress measurement and deprioritization signals",
    },
    "4": {
        "4.1.1": "Hard rules with zero exception tolerance",
        "4.1.2": "Rule source authority and BOSS dimension mapping",
        "4.2.1": "Soft expectations with exception tolerance",
        "4.2.2": "Exception tolerance threshold",
    },
    "5": {
        "5.1.1": "Budget structure by business unit",
        "5.1.2": "Revenue recognition and reporting requirements",
        "5.1.3": "Capital allocation framework",
        "5.1.4": "Financial risk thresholds",
        "5.2.1": "Rights and licenses held",
        "5.2.2": "Minimum rights certainty threshold",
        "5.3.1": "Customer segmentation and treatment",
        "5.3.2": "Reputational red lines",
        "5.4.1": "Regulatory frameworks by jurisdiction",
        "5.4.2": "Data residency requirements",
        "5.5.1": "Drift detection mechanism",
        "5.5.2": "Maximum acceptable drift threshold",
    },
    "6": {
        "6.1.1": "BOSS scoring dimensions and weights",
        "6.1.2": "BOSS routing thresholds",
        "6.1.3": "Recalibration cadence",
        "6.2.1": "Exception packet structure",
        "6.2.2": "Target exception volume",
        "6.2.3": "Exception feedback loop",
    },
    "7": {
        "7.1.1": "Default risk tolerance per director role",
        "7.1.2": "Urgency level behaviors",
        "7.1.3": "Default constraints for routine operations",
        "7.1.4": "Approval chain by action category",
        "7.2.1": "Doctrine conflict categories",
        "7.2.2": "Arbitration routing rules",
        "7.2.3": "Time-to-decision windows",
        "7.2.4": "Doctrine self-amendment boundaries",
    },
    "8": {
        "8.1.1": "Financial Governance Governor configuration",
        "8.1.2": "Legal & Compliance Governor configuration",
        "8.1.3": "Enterprise Risk Governor configuration",
        "8.1.4": "Market & Ecosystem Governor configuration",
        "8.1.5": "Enterprise Strategy Governor configuration",
        "8.2.1": "Corporate Work Group domains",
        "8.2.2": "AI-Centric Division domains",
        "8.3.1": "Digital Twin definitions",
        "8.3.2": "Simulation requirements",
    },
    "9": {
        "9.1": "Evidence retention periods",
        "9.2": "Tamper-evidence requirements",
        "9.3": "Audit interface requirements",
        "9.4": "Compliance reporting automation",
        "9.5": "Evidence export formats",
    },
    "10": {
        "10.1": "Products and services inventory",
        "10.2": "Product ecosystem interconnections",
        "10.3": "Competitive differentiation",
        "10.4": "Supply chain dependencies",
        "10.5": "Customer lifecycle",
        "10.6": "Revenue and cost structures",
    },
    "11": {
        "11.1.1": "Seasonal/cyclical patterns",
        "11.1.2": "Doctrine refresh cadence",
        "11.2.1": "Region-specific doctrine overrides",
        "11.2.2": "Jurisdictional conflict resolution",
    },
    "12": {
        "12.1.1": "Multi-cloud topology",
        "12.1.2": "Sovereignty boundary",
        "12.1.3": "Data residency by type",
        "12.1.4": "Cross-border data flow restrictions",
        "12.2.1": "CORE Engine compute requirements",
        "12.2.2": "Agent Mesh compute requirements",
        "12.2.3": "Auto-scaling parameters",
        "12.3.1": "Storage requirements",
        "12.3.2": "Networking and DR requirements",
        "12.4.1": "On-premises configuration",
        "12.4.2": "Sync and failback strategy",
        "12.5.1": "Unified management strategy",
        "12.5.2": "AI-assisted infrastructure services",
    },
    "13": {
        "13.1": "Disaster posture tiers",
        "13.2": "Idempotency requirements",
        "13.3": "Security posture",
        "13.4": "Threat model",
    },
}


class DNABuilder:
    """Builds and manages the DNA configuration data structure."""

    def __init__(self, session: Session):
        self.session = session

    def update_answer(self, question_number: str, answer: str, confidence: float = 1.0, source_doc_id: Optional[str] = None):
        """Record an answer to a specific DNA question."""
        section_num = question_number.split(".")[0]
        section_key = self._section_key(section_num)

        if section_key not in self.session.dna_data.sections:
            self.session.dna_data.sections[section_key] = {
                "section_number": section_num,
                "title": self._section_title(section_num),
                "questions": {},
                "context": [],
                "core_engine_notes": [],
            }

        self.session.dna_data.sections[section_key]["questions"][question_number] = {
            "question_number": question_number,
            "question": QUESTION_INVENTORY.get(section_num, {}).get(question_number, ""),
            "answer": answer,
            "confidence": confidence,
            "source_document": source_doc_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Update section progress
        self._update_section_progress(section_num)

    def update_meta(self, company_name: str = None, **kwargs):
        """Update DNA metadata."""
        if company_name:
            self.session.dna_data.meta["company_name"] = company_name
            self.session.company_name = company_name
        for k, v in kwargs.items():
            self.session.dna_data.meta[k] = v

    def update_governance(self, **kwargs):
        """Update governance configuration."""
        self.session.dna_data.governance.update(kwargs)

    def update_boss_config(self, **kwargs):
        """Update BOSS scoring configuration."""
        self.session.dna_data.boss_config.update(kwargs)

    def update_infrastructure(self, **kwargs):
        """Update infrastructure parameters."""
        self.session.dna_data.infrastructure.update(kwargs)

    def update_deployment_params(self, **kwargs):
        """Update deployment parameters."""
        self.session.dna_data.deployment_params.update(kwargs)

    def get_section_status(self, section_num: str) -> Dict[str, Any]:
        """Get the completion status of a specific section."""
        section_key = self._section_key(section_num)
        questions = QUESTION_INVENTORY.get(section_num, {})
        answered = self.session.dna_data.sections.get(section_key, {}).get("questions", {})

        total = len(questions)
        completed = len([q for q in questions if q in answered and answered[q].get("answer")])

        return {
            "section": section_num,
            "total_questions": total,
            "answered": completed,
            "completion_pct": round((completed / total * 100) if total > 0 else 0, 1),
            "missing": [q for q in questions if q not in answered or not answered[q].get("answer")],
        }

    def get_overall_status(self) -> Dict[str, Any]:
        """Get overall DNA completion status across all sections."""
        sections = {}
        total_q = 0
        total_a = 0

        for section_num in QUESTION_INVENTORY:
            status = self.get_section_status(section_num)
            sections[section_num] = status
            total_q += status["total_questions"]
            total_a += status["answered"]

        return {
            "total_questions": total_q,
            "total_answered": total_a,
            "overall_completion_pct": round((total_a / total_q * 100) if total_q > 0 else 0, 1),
            "sections": sections,
        }

    def export_dna_json(self) -> Dict[str, Any]:
        """Export the DNA data in the format expected by the DNA Deployment Tool."""
        dna = {
            "meta": {
                "company_name": self.session.company_name or self.session.dna_data.meta.get("company_name", "Unknown"),
                "source": "ADAM DNA Tool v1.0",
                "generated": datetime.utcnow().isoformat(),
                "questionnaire_version": "1.0",
                "adam_version": "0.4",
            },
            "sections": {},
        }

        # Map section data to the format the DNA Deployment Tool expects
        section_key_map = {
            "1": "doctrine_identity",
            "2": "culture_graph",
            "3": "objectives_graph",
            "4": "rules_expectations",
            "5": "enterprise_memory",
            "6": "boss_scoring",
            "7": "intent_conflict",
            "8": "agentic_architecture",
            "9": "flight_recorder",
            "10": "products_services",
            "11": "temporal_regional",
            "12": "cloud_infrastructure",
            "13": "resilience_security",
        }

        section_titles = {
            "1": "Doctrine Identity & Constitutional Foundation",
            "2": "CORE Engine — Culture Graph",
            "3": "CORE Engine — Objectives Graph",
            "4": "CORE Engine — Rules & Expectations Graph",
            "5": "CORE Subgraphs — Enterprise Memory",
            "6": "BOSS Scoring & Exception Economy Configuration",
            "7": "Intent Object & Doctrine Conflict Configuration",
            "8": "Agentic Architecture & Domain Configuration",
            "9": "Flight Recorder & Evidence Architecture",
            "10": "Products, Services & Operational Domain",
            "11": "Temporal & Regional Variance Configuration",
            "12": "Cloud Infrastructure Sizing & Sovereignty Architecture",
            "13": "Resilience, Idempotency & Security Posture",
        }

        for sec_num, sec_key in section_key_map.items():
            section_data = self.session.dna_data.sections.get(sec_key, {})
            questions = section_data.get("questions", {})

            # Convert to the format the parser expects
            clean_questions = {}
            for qn, qdata in questions.items():
                clean_questions[qn] = {
                    "question_number": qn,
                    "question": qdata.get("question", ""),
                    "answer": qdata.get("answer", ""),
                    "section": sec_num,
                }

            dna["sections"][sec_key] = {
                "section_number": sec_num,
                "title": section_titles.get(sec_num, f"Section {sec_num}"),
                "questions": clean_questions,
                "context": section_data.get("context", []),
                "core_engine_notes": section_data.get("core_engine_notes", []),
            }

        # Add extracted parameter groups
        dna["deployment_params"] = self.session.dna_data.deployment_params
        dna["governance"] = self.session.dna_data.governance
        dna["boss_config"] = self.session.dna_data.boss_config
        dna["agent_config"] = self.session.dna_data.agent_config
        dna["infrastructure"] = self.session.dna_data.infrastructure

        return dna

    def save_dna_json(self, output_dir: str) -> str:
        """Save the DNA JSON to a file."""
        os.makedirs(output_dir, exist_ok=True)
        dna = self.export_dna_json()

        company_slug = (self.session.company_name or "company").lower().replace(" ", "-")[:30]
        filename = f"adam-dna-{company_slug}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w") as f:
            json.dump(dna, f, indent=2, default=str)

        logger.info("DNA JSON saved", filepath=filepath)
        return filepath

    def _section_key(self, section_num: str) -> str:
        """Map section number to key."""
        mapping = {
            "1": "doctrine_identity", "2": "culture_graph", "3": "objectives_graph",
            "4": "rules_expectations", "5": "enterprise_memory", "6": "boss_scoring",
            "7": "intent_conflict", "8": "agentic_architecture", "9": "flight_recorder",
            "10": "products_services", "11": "temporal_regional",
            "12": "cloud_infrastructure", "13": "resilience_security",
        }
        return mapping.get(section_num, f"section_{section_num}")

    def _section_title(self, section_num: str) -> str:
        """Get human-readable section title."""
        titles = {
            "1": "Doctrine Identity & Constitutional Foundation",
            "2": "CORE Engine — Culture Graph",
            "3": "CORE Engine — Objectives Graph",
            "4": "CORE Engine — Rules & Expectations Graph",
            "5": "CORE Subgraphs — Enterprise Memory",
            "6": "BOSS Scoring & Exception Economy Configuration",
            "7": "Intent Object & Doctrine Conflict Configuration",
            "8": "Agentic Architecture & Domain Configuration",
            "9": "Flight Recorder & Evidence Architecture",
            "10": "Products, Services & Operational Domain",
            "11": "Temporal & Regional Variance Configuration",
            "12": "Cloud Infrastructure Sizing & Sovereignty Architecture",
            "13": "Resilience, Idempotency & Security Posture",
        }
        return titles.get(section_num, f"Section {section_num}")

    def _update_section_progress(self, section_num: str):
        """Recalculate section progress after an answer update."""
        status = self.get_section_status(section_num)

        # Find the matching phase
        phase = None
        for p, sn in PHASE_SECTION_MAP.items():
            if sn == section_num:
                phase = p
                break

        if phase and phase.value in self.session.section_progress:
            progress = self.session.section_progress[phase.value]
            progress.questions_total = status["total_questions"]
            progress.questions_answered = status["answered"]
            progress.completion_pct = status["completion_pct"]
            if status["completion_pct"] >= 100:
                progress.status = "complete"
            elif status["answered"] > 0:
                progress.status = "in_progress"
