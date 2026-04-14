"""
ADAM-AGT Execution Rings Integration Bridge

Bridges AGT Agent Runtime (execution rings, sagas, kill switch) with ADAM's
enforcement hooks and autonomy governance. Maps 5 execution rings to BOSS
score tiers with real-time policy enforcement, saga orchestration, and
emergency termination capabilities.

Key Components:
- ExecutionRing enum: 5-level privilege hierarchy (Ring 0-4)
- AdamExecutionRing: Ring configuration with autonomy budgets and policies
- SagaOrchestrator: Multi-step agent operations with compensating transactions
- KillSwitchController: Emergency termination with Flight Recorder integration
- AdamRuntimeBridge: Main orchestration engine

Author: ADAM-AGT Integration Framework
Version: 1.0.0
License: Proprietary
"""

import hashlib
import json
import logging
import threading
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from collections import defaultdict


# ============================================================================
# Constants and Configuration
# ============================================================================

BOSS_TIER_MAPPING = {
    "SOAP": (0, 20),          # Safe and operational
    "MODERATE": (21, 40),     # Monitor closely
    "ELEVATED": (41, 60),     # Elevated caution required
    "HIGH": (61, 80),     # Critical monitoring
    "OHSHAT": (81, 100),      # Emergency situation
}

RING_BOSS_MAPPING = {
    0: "OHSHAT",              # Ring 0: Kernel - OHSHAT response
    1: "HIGH",            # Ring 1: Privileged - HIGH-tier operations
    2: "ELEVATED",            # Ring 2: Standard - ELEVATED
    3: "MODERATE",            # Ring 3: Sandbox - MODERATE
    4: "SOAP",                # Ring 4: Quarantine - containment
}

ENFORCEMENT_HOOKS = [
    "policy_and_governance",  # Pre-execution validation
    "exception_and_escalation",  # Real-time monitoring
    "evidence_capture",       # Audit trail and Flight Recorder
    "recovery_and_rollback",  # Failure handling
]

DIRECTOR_ROLES = ["CEO", "CFO", "Legal", "Market", "CISO"]

logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================

class ExecutionRing(Enum):
    """AGT execution ring privilege levels mapped to ADAM BOSS tiers."""
    KERNEL = 0          # Ring 0: Highest privilege, OHSHAT response
    PRIVILEGED = 1      # Ring 1: Governor Agent level, HIGH
    STANDARD = 2        # Ring 2: Normal operations, ELEVATED
    SANDBOX = 3         # Ring 3: Restricted execution, MODERATE
    QUARANTINE = 4      # Ring 4: Isolation/containment, SOAP


class CompensationStrategy(Enum):
    """Strategies for compensating failed saga steps."""
    ROLLBACK = auto()   # Undo via compensating transaction
    RETRY = auto()      # Retry with exponential backoff
    ESCALATE = auto()   # Escalate to Director for manual intervention
    NOTIFY = auto()     # Notify via Flight Recorder, continue
    TERMINATE = auto()  # Terminate entire saga


class OperationStatus(Enum):
    """Status of saga operations and ring assignments."""
    PENDING = auto()
    IN_PROGRESS = auto()
    SUCCEEDED = auto()
    FAILED = auto()
    COMPENSATED = auto()
    TERMINATED = auto()


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class AdamEnforcementHook:
    """ADAM enforcement hook with validators and callbacks."""
    name: str                           # policy_and_governance, exception_and_escalation, etc.
    description: str
    enabled: bool = True
    validators: List[Callable] = field(default_factory=list)
    callbacks: List[Callable] = field(default_factory=list)
    timeout_seconds: int = 30
    critical: bool = False              # If True, failure blocks execution


@dataclass
class AutonomyBudget:
    """Exception Economy autonomy budget per agent class."""
    agent_class: str                    # strategic, tactical, operational, specialist, support
    total_budget: int                   # Total operations per time window
    consumed_budget: int = 0
    reset_interval_seconds: int = 3600  # 1 hour
    last_reset: datetime = field(default_factory=datetime.utcnow)
    emergency_threshold_percent: float = 90.0  # Alert when exceeded

    def is_exhausted(self) -> bool:
        """Check if budget is exhausted."""
        return self.consumed_budget >= self.total_budget

    def percent_consumed(self) -> float:
        """Return percentage of budget consumed."""
        if self.total_budget == 0:
            return 100.0
        return (self.consumed_budget / self.total_budget) * 100.0

    def should_reset(self) -> bool:
        """Check if budget should be reset based on interval."""
        elapsed = (datetime.utcnow() - self.last_reset).total_seconds()
        return elapsed >= self.reset_interval_seconds

    def consume(self, amount: int) -> bool:
        """Attempt to consume from budget. Returns True if successful."""
        if self.should_reset():
            self.consumed_budget = 0
            self.last_reset = datetime.utcnow()

        if self.consumed_budget + amount <= self.total_budget:
            self.consumed_budget += amount
            return True
        return False


@dataclass
class AdamExecutionRing:
    """Configuration for a single ADAM execution ring."""
    ring_id: int                        # 0-4
    ring_name: str                      # KERNEL, PRIVILEGED, STANDARD, SANDBOX, QUARANTINE
    agent_layers: List[str]             # Layer names for this ring
    privilege_level: int                # 0-10, higher = more privileged
    autonomy_budget: Optional[AutonomyBudget] = None
    memory_limit_mb: int = 512
    max_concurrent_operations: int = 100
    requires_approval_for: List[str] = field(default_factory=list)
    audit_all_decisions: bool = True
    enforcement_hooks: Dict[str, AdamEnforcementHook] = field(default_factory=dict)

    def get_boss_tier(self) -> str:
        """Get BOSS tier for this ring."""
        return RING_BOSS_MAPPING[self.ring_id]

    def can_execute_operation(self, operation_type: str) -> bool:
        """Check if operation type is allowed in this ring."""
        if operation_type in self.requires_approval_for:
            return False
        return True


@dataclass
class SagaStep:
    """Single step in a multi-step saga operation."""
    step_id: str
    description: str
    executor: Callable
    compensator: Optional[Callable] = None
    timeout_seconds: int = 60
    retry_count: int = 3
    compensation_strategy: CompensationStrategy = CompensationStrategy.ROLLBACK


@dataclass
class SagaOperation:
    """Multi-step agent operation with transaction semantics."""
    saga_id: str
    agent_id: str
    ring_id: int
    steps: List[SagaStep]
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: OperationStatus = OperationStatus.PENDING
    results: Dict[str, Any] = field(default_factory=dict)
    failures: Dict[str, Exception] = field(default_factory=dict)
    evidence_hash: Optional[str] = None  # For Flight Recorder linkage

    def duration_seconds(self) -> Optional[float]:
        """Return saga execution duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


@dataclass
class FlightRecorderEntry:
    """Evidence entry for ADAM Flight Recorder (hash-chained WORM)."""
    entry_id: str
    timestamp: datetime
    agent_id: str
    operation_type: str
    saga_id: Optional[str]
    ring_id: int
    boss_score: int
    action_description: str
    result: str  # success, failed, compensated, terminated
    previous_hash: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def compute_hash(self) -> str:
        """Compute hash for chain linkage (immutability)."""
        content = json.dumps({
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "operation_type": self.operation_type,
            "saga_id": self.saga_id,
            "ring_id": self.ring_id,
            "boss_score": self.boss_score,
            "action_description": self.action_description,
            "result": self.result,
            "previous_hash": self.previous_hash,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class KillSwitchEvent:
    """Emergency termination event triggered by OHSHAT BOSS."""
    event_id: str
    triggered_at: datetime
    trigger_reason: str
    boss_score: int
    triggered_by: str  # agent_id or director_id
    affected_ring: int
    affected_agents: List[str]
    evidence_entry: Optional[FlightRecorderEntry] = None
    notifications_sent: List[str] = field(default_factory=list)


# ============================================================================
# SagaOrchestrator Class
# ============================================================================

class SagaOrchestrator:
    """
    Manages multi-step agent operations with compensating transactions.
    Integrates with ADAM's 4 enforcement hooks for policy validation,
    exception handling, evidence capture, and recovery.
    """

    def __init__(self, flight_recorder: 'FlightRecorder', logger_instance=None):
        """
        Initialize saga orchestrator.

        Args:
            flight_recorder: FlightRecorder instance for evidence logging
            logger_instance: Optional logger instance
        """
        self.flight_recorder = flight_recorder
        self.logger = logger_instance or logger
        self.sagas: Dict[str, SagaOperation] = {}
        self.saga_lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=20)
        self.enforcement_hooks: Dict[str, List[Callable]] = defaultdict(list)

    def register_enforcement_hook(self, hook_name: str, callback: Callable) -> None:
        """
        Register callback for enforcement hook.

        Args:
            hook_name: Hook name (policy_and_governance, exception_and_escalation, etc.)
            callback: Callable with signature (saga_operation, context) -> bool
        """
        if hook_name not in ENFORCEMENT_HOOKS:
            raise ValueError(f"Unknown hook: {hook_name}")
        self.enforcement_hooks[hook_name].append(callback)

    def create_saga(self, agent_id: str, ring_id: int, steps: List[SagaStep]) -> SagaOperation:
        """
        Create new saga operation.

        Args:
            agent_id: Agent executing the saga
            ring_id: Execution ring (0-4)
            steps: List of saga steps

        Returns:
            SagaOperation instance
        """
        saga_id = f"saga-{uuid.uuid4().hex[:12]}"
        saga = SagaOperation(
            saga_id=saga_id,
            agent_id=agent_id,
            ring_id=ring_id,
            steps=steps,
        )

        with self.saga_lock:
            self.sagas[saga_id] = saga

        self.logger.info(f"Created saga {saga_id} for agent {agent_id}")
        return saga

    def execute_saga(self, saga: SagaOperation, boss_score: int) -> OperationStatus:
        """
        Execute saga with compensation strategy on failure.

        Args:
            saga: SagaOperation to execute
            boss_score: Current BOSS score (0-100)

        Returns:
            Final OperationStatus
        """
        with self.saga_lock:
            saga.started_at = datetime.utcnow()
            saga.status = OperationStatus.IN_PROGRESS

        try:
            # Phase 1: Pre-execution validation (policy_and_governance hook)
            self._invoke_hook("policy_and_governance", saga, {"boss_score": boss_score})

            # Phase 2: Execute steps
            for i, step in enumerate(saga.steps):
                self.logger.info(f"Executing step {i+1}/{len(saga.steps)}: {step.description}")

                # Monitor during execution (exception_and_escalation hook)
                self._invoke_hook("exception_and_escalation", saga, {"step_index": i})

                try:
                    result = self._execute_step_with_retry(step)
                    saga.results[step.step_id] = result

                except Exception as exc:
                    saga.failures[step.step_id] = exc
                    self.logger.error(f"Step {step.step_id} failed: {exc}")

                    # Handle compensation
                    compensation_result = self._handle_compensation(saga, step, i)

                    if compensation_result == CompensationStrategy.ESCALATE:
                        saga.status = OperationStatus.FAILED
                        # Evidence capture (evidence_capture hook)
                        self._invoke_hook("evidence_capture", saga, {"failure": str(exc)})
                        return saga.status
                    elif compensation_result == CompensationStrategy.TERMINATE:
                        saga.status = OperationStatus.TERMINATED
                        self._invoke_hook("evidence_capture", saga, {"termination": "user_request"})
                        return saga.status

            # Phase 3: Post-completion validation
            saga.status = OperationStatus.SUCCEEDED
            saga.completed_at = datetime.utcnow()
            self._invoke_hook("recovery_and_rollback", saga, {"status": "success"})

        except Exception as exc:
            saga.status = OperationStatus.FAILED
            saga.completed_at = datetime.utcnow()
            self.logger.error(f"Saga {saga.saga_id} failed: {exc}")
            self._invoke_hook("recovery_and_rollback", saga, {"error": str(exc)})

        # Record in Flight Recorder
        self._record_saga_evidence(saga, boss_score)

        with self.saga_lock:
            saga.completed_at = datetime.utcnow()

        return saga.status

    def _execute_step_with_retry(self, step: SagaStep) -> Any:
        """Execute step with retry logic."""
        last_exception = None

        for attempt in range(step.retry_count):
            try:
                return step.executor()
            except Exception as exc:
                last_exception = exc
                if attempt < step.retry_count - 1:
                    self.logger.warning(f"Step retry {attempt + 1}/{step.retry_count}: {exc}")
                    # Exponential backoff: 1s, 2s, 4s, 8s
                    backoff = 2 ** attempt
                    threading.Event().wait(backoff)

        raise last_exception

    def _handle_compensation(self, saga: SagaOperation, failed_step: SagaStep,
                            step_index: int) -> CompensationStrategy:
        """
        Handle compensation for failed step using specified strategy.

        Returns:
            CompensationStrategy indicating how failure was handled
        """
        strategy = failed_step.compensation_strategy

        if strategy == CompensationStrategy.ROLLBACK:
            if failed_step.compensator:
                try:
                    failed_step.compensator()
                    saga.status = OperationStatus.COMPENSATED
                    self.logger.info(f"Compensated step {failed_step.step_id}")
                    return CompensationStrategy.ROLLBACK
                except Exception as exc:
                    self.logger.error(f"Compensation failed: {exc}")
                    return CompensationStrategy.ESCALATE

        elif strategy == CompensationStrategy.RETRY:
            return CompensationStrategy.RETRY

        elif strategy == CompensationStrategy.ESCALATE:
            self.logger.warning(f"Escalating failure of step {failed_step.step_id}")
            return CompensationStrategy.ESCALATE

        elif strategy == CompensationStrategy.NOTIFY:
            self.logger.info(f"Recording failure, continuing saga")
            return CompensationStrategy.NOTIFY

        elif strategy == CompensationStrategy.TERMINATE:
            self.logger.critical(f"Terminating saga due to step {failed_step.step_id} failure")
            return CompensationStrategy.TERMINATE

        return CompensationStrategy.ESCALATE

    def _invoke_hook(self, hook_name: str, saga: SagaOperation, context: Dict[str, Any]) -> None:
        """Invoke all registered callbacks for enforcement hook."""
        if hook_name not in self.enforcement_hooks:
            return

        for callback in self.enforcement_hooks[hook_name]:
            try:
                callback(saga, context)
            except Exception as exc:
                self.logger.error(f"Enforcement hook {hook_name} failed: {exc}")

    def _record_saga_evidence(self, saga: SagaOperation, boss_score: int) -> None:
        """Record saga execution as Flight Recorder evidence."""
        entry = FlightRecorderEntry(
            entry_id=f"evt-{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow(),
            agent_id=saga.agent_id,
            operation_type="saga_execution",
            saga_id=saga.saga_id,
            ring_id=saga.ring_id,
            boss_score=boss_score,
            action_description=f"Saga with {len(saga.steps)} steps",
            result=saga.status.name,
            previous_hash=self.flight_recorder.get_last_hash(),
            metadata={
                "steps_completed": len(saga.results),
                "steps_failed": len(saga.failures),
                "duration_seconds": saga.duration_seconds(),
            }
        )

        self.flight_recorder.append(entry)
        saga.evidence_hash = entry.compute_hash()

    def get_saga(self, saga_id: str) -> Optional[SagaOperation]:
        """Retrieve saga by ID."""
        with self.saga_lock:
            return self.sagas.get(saga_id)


# ============================================================================
# KillSwitchController Class
# ============================================================================

class KillSwitchController:
    """
    Emergency termination system triggered by BOSS OHSHAT threshold.
    Integrates with Flight Recorder for evidence and notifies 5-Director
    Constitution.
    """

    def __init__(self, flight_recorder: 'FlightRecorder', logger_instance=None):
        """
        Initialize kill switch controller.

        Args:
            flight_recorder: FlightRecorder instance
            logger_instance: Optional logger instance
        """
        self.flight_recorder = flight_recorder
        self.logger = logger_instance or logger
        self.ohshat_threshold = 81  # BOSS score >= 81
        self.active_events: Dict[str, KillSwitchEvent] = {}
        self.event_lock = threading.RLock()
        self.director_notifiers: Dict[str, Callable] = {}  # Role -> notifier callback
        self.listeners: List[Callable] = []

    def register_director_notifier(self, role: str, notifier: Callable) -> None:
        """
        Register callback to notify director.

        Args:
            role: Director role (CEO, CFO, Legal, Market, CISO)
            notifier: Callable with signature (event: KillSwitchEvent) -> None
        """
        if role not in DIRECTOR_ROLES:
            raise ValueError(f"Invalid director role: {role}")
        self.director_notifiers[role] = notifier

    def register_listener(self, listener: Callable) -> None:
        """Register listener for kill switch events."""
        self.listeners.append(listener)

    def evaluate_boss_score(self, boss_score: int, agent_id: str,
                           ring_id: int) -> bool:
        """
        Evaluate BOSS score and trigger kill switch if OHSHAT.

        Args:
            boss_score: Current BOSS score (0-100)
            agent_id: Agent associated with score
            ring_id: Execution ring (0-4)

        Returns:
            True if kill switch was triggered
        """
        if boss_score >= self.ohshat_threshold:
            self.trigger_kill_switch(
                trigger_reason=f"BOSS OHSHAT threshold exceeded ({boss_score})",
                boss_score=boss_score,
                triggered_by=agent_id,
                affected_ring=ring_id,
                affected_agents=[agent_id],
            )
            return True
        return False

    def trigger_kill_switch(self, trigger_reason: str, boss_score: int,
                           triggered_by: str, affected_ring: int,
                           affected_agents: List[str]) -> KillSwitchEvent:
        """
        Trigger emergency kill switch.

        Args:
            trigger_reason: Reason for kill switch
            boss_score: Current BOSS score
            triggered_by: Who triggered (agent_id or director_id)
            affected_ring: Execution ring to terminate
            affected_agents: Agents to terminate

        Returns:
            KillSwitchEvent instance
        """
        event_id = f"kill-{uuid.uuid4().hex[:12]}"

        event = KillSwitchEvent(
            event_id=event_id,
            triggered_at=datetime.utcnow(),
            trigger_reason=trigger_reason,
            boss_score=boss_score,
            triggered_by=triggered_by,
            affected_ring=affected_ring,
            affected_agents=affected_agents,
        )

        self.logger.critical(
            f"KILL SWITCH TRIGGERED: {event_id} - {trigger_reason} "
            f"(BOSS={boss_score}, Ring={affected_ring}, Agents={affected_agents})"
        )

        with self.event_lock:
            self.active_events[event_id] = event

        # Record in Flight Recorder
        evidence = self._record_kill_switch_evidence(event)
        event.evidence_entry = evidence

        # Notify directors
        self._notify_directors(event)

        # Invoke listeners
        for listener in self.listeners:
            try:
                listener(event)
            except Exception as exc:
                self.logger.error(f"Listener invocation failed: {exc}")

        return event

    def _record_kill_switch_evidence(self, event: KillSwitchEvent) -> FlightRecorderEntry:
        """Record kill switch in Flight Recorder as immutable evidence."""
        entry = FlightRecorderEntry(
            entry_id=f"evt-{uuid.uuid4().hex[:12]}",
            timestamp=event.triggered_at,
            agent_id=event.triggered_by,
            operation_type="kill_switch",
            saga_id=None,
            ring_id=event.affected_ring,
            boss_score=event.boss_score,
            action_description=f"Kill switch triggered: {event.trigger_reason}",
            result="terminated",
            previous_hash=self.flight_recorder.get_last_hash(),
            metadata={
                "event_id": event.event_id,
                "affected_agents": event.affected_agents,
                "trigger_reason": event.trigger_reason,
            }
        )

        self.flight_recorder.append(entry)
        return entry

    def _notify_directors(self, event: KillSwitchEvent) -> None:
        """Notify 5-Director Constitution of kill switch."""
        notifications_sent = []

        for role, notifier in self.director_notifiers.items():
            try:
                notifier(event)
                notifications_sent.append(role)
                self.logger.info(f"Notified {role} of kill switch {event.event_id}")
            except Exception as exc:
                self.logger.error(f"Failed to notify {role}: {exc}")

        event.notifications_sent = notifications_sent

    def get_event(self, event_id: str) -> Optional[KillSwitchEvent]:
        """Retrieve kill switch event by ID."""
        with self.event_lock:
            return self.active_events.get(event_id)


# ============================================================================
# FlightRecorder Class (Simple Hash-Chained WORM)
# ============================================================================

class FlightRecorder:
    """
    ADAM Flight Recorder: Hash-chained WORM (Write-Once-Read-Many) evidence log.
    Stores immutable audit trail for compliance and forensics.
    """

    def __init__(self):
        """Initialize Flight Recorder."""
        self.entries: List[FlightRecorderEntry] = []
        self.entries_lock = threading.RLock()
        self.last_hash: Optional[str] = None

    def append(self, entry: FlightRecorderEntry) -> str:
        """
        Append entry to flight recorder.

        Args:
            entry: FlightRecorderEntry to append

        Returns:
            Hash of the entry
        """
        entry.previous_hash = self.last_hash
        entry_hash = entry.compute_hash()

        with self.entries_lock:
            self.entries.append(entry)
            self.last_hash = entry_hash

        logger.debug(f"Flight Recorder: {entry.operation_type} - {entry_hash[:16]}...")
        return entry_hash

    def get_last_hash(self) -> Optional[str]:
        """Get hash of last entry (for chain linkage)."""
        return self.last_hash

    def verify_chain(self) -> bool:
        """Verify integrity of hash chain."""
        if not self.entries:
            return True

        prev_hash = None
        with self.entries_lock:
            for entry in self.entries:
                if entry.previous_hash != prev_hash:
                    return False
                prev_hash = entry.compute_hash()

        return True


# ============================================================================
# AdamRuntimeBridge Class (Main Orchestrator)
# ============================================================================

class AdamRuntimeBridge:
    """
    Main orchestration engine bridging AGT Agent Runtime with ADAM
    enforcement hooks. Assigns execution rings based on real-time BOSS
    scores and manages autonomy budgets.
    """

    def __init__(self, logger_instance=None):
        """
        Initialize ADAM Runtime Bridge.

        Args:
            logger_instance: Optional logger instance
        """
        self.logger = logger_instance or logger
        self.flight_recorder = FlightRecorder()
        self.saga_orchestrator = SagaOrchestrator(self.flight_recorder, self.logger)
        self.kill_switch = KillSwitchController(self.flight_recorder, self.logger)

        # Execution rings (0-4)
        self.rings: Dict[int, AdamExecutionRing] = {}
        self._initialize_rings()

        # Agent state tracking
        self.agent_rings: Dict[str, int] = {}  # agent_id -> ring_id
        self.agent_autonomy: Dict[str, AutonomyBudget] = {}  # agent_id -> budget
        self.agent_lock = threading.RLock()
        self.agent_boss_scores: Dict[str, int] = {}  # agent_id -> current BOSS

    def _initialize_rings(self) -> None:
        """Initialize 5 execution rings with ADAM configuration."""
        ring_configs = [
            AdamExecutionRing(
                ring_id=0, ring_name="KERNEL",
                agent_layers=["intent-layer"],
                privilege_level=10,
                memory_limit_mb=2048,
                max_concurrent_operations=50,
                requires_approval_for=["major-policy-changes", "constitution-amendments"],
                audit_all_decisions=True,
            ),
            AdamExecutionRing(
                ring_id=1, ring_name="PRIVILEGED",
                agent_layers=["governor_agent-layer"],
                privilege_level=8,
                memory_limit_mb=1024,
                max_concurrent_operations=100,
                requires_approval_for=["exception-allocation"],
                audit_all_decisions=True,
            ),
            AdamExecutionRing(
                ring_id=2, ring_name="STANDARD",
                agent_layers=["orchestration-layer"],
                privilege_level=6,
                memory_limit_mb=512,
                max_concurrent_operations=200,
                audit_all_decisions=True,
            ),
            AdamExecutionRing(
                ring_id=3, ring_name="SANDBOX",
                agent_layers=["workgroup-layer"],
                privilege_level=4,
                memory_limit_mb=256,
                max_concurrent_operations=500,
                audit_all_decisions=False,
            ),
            AdamExecutionRing(
                ring_id=4, ring_name="QUARANTINE",
                agent_layers=["digital-twin-layer"],
                privilege_level=2,
                memory_limit_mb=128,
                max_concurrent_operations=50,
                requires_approval_for=["any-external-action"],
                audit_all_decisions=True,
            ),
        ]

        for config in ring_configs:
            self.rings[config.ring_id] = config

    def assign_ring_for_agent(self, agent_id: str, boss_score: int) -> Tuple[int, str]:
        """
        Assign execution ring to agent based on BOSS score.

        Args:
            agent_id: Agent identifier
            boss_score: Current BOSS score (0-100)

        Returns:
            Tuple of (ring_id, reason)
        """
        # Determine ring based on BOSS score
        if boss_score >= BOSS_TIER_MAPPING["OHSHAT"][0]:
            ring_id = 0  # KERNEL
            reason = "OHSHAT: emergency containment"
        elif boss_score >= BOSS_TIER_MAPPING["HIGH"][0]:
            ring_id = 1  # PRIVILEGED
            reason = "HIGH: elevated oversight"
        elif boss_score >= BOSS_TIER_MAPPING["ELEVATED"][0]:
            ring_id = 2  # STANDARD
            reason = "ELEVATED: standard operations with monitoring"
        elif boss_score >= BOSS_TIER_MAPPING["MODERATE"][0]:
            ring_id = 3  # SANDBOX
            reason = "MODERATE: sandbox execution"
        else:
            ring_id = 4  # QUARANTINE
            reason = "SOAP: normal operation"

        with self.agent_lock:
            old_ring = self.agent_rings.get(agent_id)
            self.agent_rings[agent_id] = ring_id
            self.agent_boss_scores[agent_id] = boss_score

        if old_ring != ring_id:
            self.logger.warning(
                f"Ring assignment changed for {agent_id}: "
                f"{old_ring} -> {ring_id} (BOSS={boss_score})"
            )

        # Trigger kill switch if OHSHAT
        self.kill_switch.evaluate_boss_score(boss_score, agent_id, ring_id)

        return ring_id, reason

    def can_execute(self, agent_id: str, operation_type: str) -> bool:
        """
        Check if agent can execute operation in assigned ring.

        Args:
            agent_id: Agent identifier
            operation_type: Type of operation (e.g., "data-query", "policy-change")

        Returns:
            True if execution is allowed
        """
        with self.agent_lock:
            ring_id = self.agent_rings.get(agent_id, 4)  # Default to quarantine

        ring = self.rings[ring_id]
        return ring.can_execute_operation(operation_type)

    def consume_autonomy_budget(self, agent_id: str, amount: int = 1) -> bool:
        """
        Attempt to consume from agent's autonomy budget.

        Args:
            agent_id: Agent identifier
            amount: Amount to consume

        Returns:
            True if budget was available and consumed
        """
        with self.agent_lock:
            if agent_id not in self.agent_autonomy:
                return False

            budget = self.agent_autonomy[agent_id]
            return budget.consume(amount)

    def get_ring_info(self, agent_id: str) -> Dict[str, Any]:
        """Get current ring assignment and status for agent."""
        with self.agent_lock:
            ring_id = self.agent_rings.get(agent_id, 4)
            boss_score = self.agent_boss_scores.get(agent_id, 0)

        ring = self.rings[ring_id]

        return {
            "agent_id": agent_id,
            "ring_id": ring_id,
            "ring_name": ring.ring_name,
            "boss_score": boss_score,
            "privilege_level": ring.privilege_level,
            "memory_limit_mb": ring.memory_limit_mb,
            "max_concurrent": ring.max_concurrent_operations,
        }

    def get_flight_recorder_chain(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent flight recorder entries."""
        with self.flight_recorder.entries_lock:
            entries = self.flight_recorder.entries[-limit:]

        return [
            {
                "entry_id": e.entry_id,
                "timestamp": e.timestamp.isoformat(),
                "agent_id": e.agent_id,
                "operation_type": e.operation_type,
                "ring_id": e.ring_id,
                "boss_score": e.boss_score,
                "result": e.result,
                "hash": e.compute_hash()[:16],
            }
            for e in entries
        ]

    def shutdown(self) -> None:
        """Graceful shutdown of runtime bridge."""
        self.logger.info("Shutting down ADAM Runtime Bridge")
        self.saga_orchestrator.executor.shutdown(wait=True)


# ============================================================================
# Module Initialization and Logging Setup
# ============================================================================

def configure_logging(level=logging.INFO) -> None:
    """Configure logging for the module."""
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)


if __name__ == "__main__":
    configure_logging(logging.DEBUG)
    logger.info("ADAM Execution Rings Integration module loaded")
