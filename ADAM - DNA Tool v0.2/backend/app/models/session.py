"""
ADAM DNA Tool - Session and DNA State Models
Tracks the conversational state, DNA completion progress, and ingested documents.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class DNAPhase(str, Enum):
    """Phases of the ADAM DNA configuration process."""
    WELCOME = "welcome"
    DOCUMENT_INGESTION = "document_ingestion"
    DOCTRINE_IDENTITY = "doctrine_identity"          # Section 1
    CULTURE_GRAPH = "culture_graph"                    # Section 2
    OBJECTIVES_GRAPH = "objectives_graph"              # Section 3
    RULES_EXPECTATIONS = "rules_expectations"          # Section 4
    ENTERPRISE_MEMORY = "enterprise_memory"            # Section 5
    BOSS_SCORING = "boss_scoring"                      # Section 6
    INTENT_CONFLICT = "intent_conflict"                # Section 7
    AGENTIC_ARCHITECTURE = "agentic_architecture"      # Section 8
    FLIGHT_RECORDER = "flight_recorder"                # Section 9
    PRODUCTS_SERVICES = "products_services"            # Section 10
    TEMPORAL_REGIONAL = "temporal_regional"             # Section 11
    CLOUD_INFRASTRUCTURE = "cloud_infrastructure"      # Section 12
    RESILIENCE_SECURITY = "resilience_security"        # Section 13
    REVIEW_VALIDATE = "review_validate"
    DEPLOYMENT_READY = "deployment_ready"

    @classmethod
    def section_phases(cls) -> List["DNAPhase"]:
        """Return only the 13 DNA section phases."""
        return [
            cls.DOCTRINE_IDENTITY, cls.CULTURE_GRAPH, cls.OBJECTIVES_GRAPH,
            cls.RULES_EXPECTATIONS, cls.ENTERPRISE_MEMORY, cls.BOSS_SCORING,
            cls.INTENT_CONFLICT, cls.AGENTIC_ARCHITECTURE, cls.FLIGHT_RECORDER,
            cls.PRODUCTS_SERVICES, cls.TEMPORAL_REGIONAL,
            cls.CLOUD_INFRASTRUCTURE, cls.RESILIENCE_SECURITY,
        ]


# Maps DNA phases to questionnaire section numbers
PHASE_SECTION_MAP = {
    DNAPhase.DOCTRINE_IDENTITY: "1",
    DNAPhase.CULTURE_GRAPH: "2",
    DNAPhase.OBJECTIVES_GRAPH: "3",
    DNAPhase.RULES_EXPECTATIONS: "4",
    DNAPhase.ENTERPRISE_MEMORY: "5",
    DNAPhase.BOSS_SCORING: "6",
    DNAPhase.INTENT_CONFLICT: "7",
    DNAPhase.AGENTIC_ARCHITECTURE: "8",
    DNAPhase.FLIGHT_RECORDER: "9",
    DNAPhase.PRODUCTS_SERVICES: "10",
    DNAPhase.TEMPORAL_REGIONAL: "11",
    DNAPhase.CLOUD_INFRASTRUCTURE: "12",
    DNAPhase.RESILIENCE_SECURITY: "13",
}

PHASE_TITLES = {
    DNAPhase.WELCOME: "Welcome & Setup",
    DNAPhase.DOCUMENT_INGESTION: "Document Ingestion",
    DNAPhase.DOCTRINE_IDENTITY: "Doctrine Identity & Constitutional Foundation",
    DNAPhase.CULTURE_GRAPH: "CORE Engine — Culture Graph",
    DNAPhase.OBJECTIVES_GRAPH: "CORE Engine — Objectives Graph",
    DNAPhase.RULES_EXPECTATIONS: "CORE Engine — Rules & Expectations",
    DNAPhase.ENTERPRISE_MEMORY: "CORE Subgraphs — Enterprise Memory",
    DNAPhase.BOSS_SCORING: "BOSS Scoring & Exception Economy",
    DNAPhase.INTENT_CONFLICT: "Intent Object & Doctrine Conflict",
    DNAPhase.AGENTIC_ARCHITECTURE: "Agentic Architecture & Domain Config",
    DNAPhase.FLIGHT_RECORDER: "Flight Recorder & Evidence Architecture",
    DNAPhase.PRODUCTS_SERVICES: "Products, Services & Operational Domain",
    DNAPhase.TEMPORAL_REGIONAL: "Temporal & Regional Variance",
    DNAPhase.CLOUD_INFRASTRUCTURE: "Cloud Infrastructure & Sovereignty",
    DNAPhase.RESILIENCE_SECURITY: "Resilience, Idempotency & Security",
    DNAPhase.REVIEW_VALIDATE: "Review & Validation",
    DNAPhase.DEPLOYMENT_READY: "Deployment Ready",
}


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    TEXT = "text"
    DOCUMENT_UPLOAD = "document_upload"
    URL_FETCH = "url_fetch"
    DNA_UPDATE = "dna_update"
    PHASE_TRANSITION = "phase_transition"
    PROGRESS_UPDATE = "progress_update"
    DEPLOYMENT_TRIGGER = "deployment_trigger"
    ERROR = "error"


class ChatMessage(BaseModel):
    """A single message in the conversation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole
    content: str
    message_type: MessageType = MessageType.TEXT
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class IngestedDocument(BaseModel):
    """A document that has been uploaded and processed."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    source_type: str  # upload, url, api
    source_url: Optional[str] = None
    mime_type: str
    size_bytes: int
    extracted_text: str = ""
    extracted_sections: Dict[str, Any] = Field(default_factory=dict)
    relevance_mapping: Dict[str, float] = Field(default_factory=dict)  # phase -> relevance score
    ingested_at: datetime = Field(default_factory=datetime.utcnow)


class SectionProgress(BaseModel):
    """Progress tracking for a single DNA section."""
    phase: DNAPhase
    section_number: Optional[str] = None
    title: str
    status: str = "pending"  # pending, in_progress, complete, needs_review
    completion_pct: float = 0.0
    questions_total: int = 0
    questions_answered: int = 0
    confidence_score: float = 0.0  # AI confidence in extracted answers
    source_documents: List[str] = Field(default_factory=list)  # doc IDs used
    notes: List[str] = Field(default_factory=list)


class DNAData(BaseModel):
    """The accumulated DNA configuration data — maps to questionnaire output."""
    meta: Dict[str, Any] = Field(default_factory=dict)
    sections: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    deployment_params: Dict[str, Any] = Field(default_factory=dict)
    governance: Dict[str, Any] = Field(default_factory=dict)
    boss_config: Dict[str, Any] = Field(default_factory=dict)
    agent_config: Dict[str, Any] = Field(default_factory=dict)
    infrastructure: Dict[str, Any] = Field(default_factory=dict)


class Session(BaseModel):
    """A complete ADAM DNA configuration session."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    current_phase: DNAPhase = DNAPhase.WELCOME
    messages: List[ChatMessage] = Field(default_factory=list)
    documents: List[IngestedDocument] = Field(default_factory=list)
    section_progress: Dict[str, SectionProgress] = Field(default_factory=dict)
    dna_data: DNAData = Field(default_factory=DNAData)
    company_name: str = ""
    ai_provider: str = "openai"

    def model_post_init(self, __context):
        """Initialize section progress for all phases."""
        if not self.section_progress:
            for phase in DNAPhase:
                self.section_progress[phase.value] = SectionProgress(
                    phase=phase,
                    section_number=PHASE_SECTION_MAP.get(phase),
                    title=PHASE_TITLES.get(phase, phase.value),
                )

    def get_overall_progress(self) -> float:
        """Calculate overall DNA completion percentage."""
        section_phases = DNAPhase.section_phases()
        if not section_phases:
            return 0.0
        total = sum(
            self.section_progress.get(p.value, SectionProgress(phase=p, title="")).completion_pct
            for p in section_phases
        )
        return round(total / len(section_phases), 1)

    def get_next_incomplete_phase(self) -> Optional[DNAPhase]:
        """Find the next section that needs work."""
        for phase in DNAPhase.section_phases():
            progress = self.section_progress.get(phase.value)
            if progress and progress.completion_pct < 100.0:
                return phase
        return DNAPhase.REVIEW_VALIDATE
