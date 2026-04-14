"""
ADAM-AGT SRE (Site Reliability Engineering) Integration Bridge

Bridges AGT Agent SRE (SLOs, error budgets, circuit breakers, chaos engineering)
with ADAM's Stability & Drift Plane. Maps error budgets to Exception Economy,
integrates circuit breakers with BOSS thresholds, and manages controlled
fault injection within governance bounds.

Key Components:
- ErrorBudgetManager: Maps AGT error budgets to ADAM autonomy budgets
- CircuitBreakerManager: Integrates circuit breakers with BOSS thresholds
- ChaosEngineer: Controlled fault injection within governance bounds
- SLOMonitor: Tracks SLOs per agent class with different targets
- AdamSREIntegration: Full SRE lifecycle management

Author: ADAM-AGT Integration Framework
Version: 1.0.0
License: Proprietary
"""

import json
import logging
import statistics
import threading
import uuid
from collections import deque, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple, Deque
from abc import ABC, abstractmethod


# ============================================================================
# Constants and Configuration
# ============================================================================

AGENT_CLASSES = {
    "STRATEGIC": {
        "availability_slo": 99.99,  # 4.3 min/month downtime
        "latency_slo_ms": 50,
        "error_rate_slo": 0.01,
        "budget_minutes_month": 4.3,
    },
    "TACTICAL": {
        "availability_slo": 99.95,  # 21.6 min/month downtime
        "latency_slo_ms": 100,
        "error_rate_slo": 0.05,
        "budget_minutes_month": 21.6,
    },
    "OPERATIONAL": {
        "availability_slo": 99.9,   # 43.2 min/month downtime
        "latency_slo_ms": 200,
        "error_rate_slo": 0.1,
        "budget_minutes_month": 43.2,
    },
    "SPECIALIST": {
        "availability_slo": 99.5,   # 216 min/month downtime
        "latency_slo_ms": 500,
        "error_rate_slo": 0.5,
        "budget_minutes_month": 216,
    },
    "SUPPORT": {
        "availability_slo": 95.0,   # 36 hours/month downtime
        "latency_slo_ms": 1000,
        "error_rate_slo": 5.0,
        "budget_minutes_month": 2160,
    },
}

BOSS_THRESHOLDS = {
    "SOAP": (0, 20),          # Safe and operational
    "MODERATE": (21, 40),     # Monitor closely
    "ELEVATED": (41, 60),     # Elevated caution
    "HIGH": (61, 80),     # Critical situation
    "OHSHAT": (81, 100),      # Emergency
}

logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================

class CircuitBreakerState(Enum):
    """States of circuit breaker."""
    CLOSED = auto()           # Normal operation, requests pass through
    OPEN = auto()             # Failure threshold exceeded, requests blocked
    HALF_OPEN = auto()        # Testing recovery, limited requests allowed


class SLOStatus(Enum):
    """SLO compliance status."""
    HEALTHY = auto()          # Within SLO
    WARNING = auto()          # Approaching SLO limits
    VIOLATED = auto()         # SLO violated
    RECOVERED = auto()        # Recovered after violation


class ChaosScenarioType(Enum):
    """Types of chaos engineering scenarios."""
    LATENCY_INJECTION = auto()      # Add artificial latency
    ERROR_INJECTION = auto()        # Inject errors
    RESOURCE_STARVATION = auto()    # Limit resources
    NETWORK_PARTITION = auto()      # Simulate network failure
    CASCADING_FAILURE = auto()      # Multi-agent failure


class DirectorApprovalStatus(Enum):
    """Status of Director approval for chaos scenarios."""
    PENDING = auto()
    APPROVED = auto()
    REJECTED = auto()
    REVOKED = auto()


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ServiceLevelObjective:
    """Service Level Objective for an agent class."""
    agent_class: str                   # STRATEGIC, TACTICAL, OPERATIONAL, SPECIALIST, SUPPORT
    availability_slo: float            # Availability percentage (0-100)
    latency_slo_ms: int                # Latency SLO in milliseconds
    error_rate_slo: float              # Error rate SLO (percentage)
    freshness_slo_seconds: int = 300   # Data freshness SLO


@dataclass
class ErrorBudget:
    """Exception Economy autonomy budget mapped to error budget."""
    agent_class: str
    total_minutes_month: float         # Total error budget in minutes
    consumed_minutes: float = 0.0
    reset_date: datetime = field(default_factory=datetime.utcnow)
    emergency_threshold_percent: float = 90.0
    director_approvals: List[str] = field(default_factory=list)

    def is_exhausted(self) -> bool:
        """Check if budget is exhausted."""
        return self.consumed_minutes >= self.total_minutes_month

    def percent_remaining(self) -> float:
        """Return percentage of budget remaining."""
        if self.total_minutes_month == 0:
            return 0.0
        return max(0.0, (1.0 - self.consumed_minutes / self.total_minutes_month) * 100.0)

    def in_emergency_mode(self) -> bool:
        """Check if in emergency mode (approaching exhaustion)."""
        return (100.0 - self.percent_remaining()) >= self.emergency_threshold_percent

    def consume(self, minutes: float) -> bool:
        """Consume from error budget."""
        if self.consumed_minutes + minutes <= self.total_minutes_month:
            self.consumed_minutes += minutes
            return True
        return False


@dataclass
class MetricSample:
    """Single metric sample (latency, error, availability)."""
    timestamp: datetime
    latency_ms: Optional[float] = None
    is_error: bool = False
    is_available: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SLOViolation:
    """Record of SLO violation."""
    violation_id: str
    agent_id: str
    agent_class: str
    timestamp: datetime
    slo_type: str                      # availability, latency, error_rate
    current_value: float
    slo_target: float
    duration_seconds: int
    remediation_actions: List[str] = field(default_factory=list)
    resolved: bool = False


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    agent_id: str
    failure_threshold: int = 5         # Failures to trigger open state
    failure_window_seconds: int = 60   # Time window for failure counting
    recovery_timeout_seconds: int = 300  # Time before attempting recovery
    success_threshold: int = 2         # Successes to close circuit
    boss_activation_threshold: int = 41  # Activate at ELEVATED (41+)


@dataclass
class CircuitBreaker:
    """Circuit breaker state machine."""
    config: CircuitBreakerConfig
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failures: Deque[datetime] = field(default_factory=lambda: deque(maxlen=100))
    successes_in_half_open: int = 0
    last_failure_time: Optional[datetime] = None
    last_state_change: datetime = field(default_factory=datetime.utcnow)
    lock: threading.RLock = field(default_factory=threading.RLock)

    def record_success(self) -> None:
        """Record successful request."""
        with self.lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.successes_in_half_open += 1
                if self.successes_in_half_open >= self.config.success_threshold:
                    self._transition_to(CircuitBreakerState.CLOSED)

    def record_failure(self) -> None:
        """Record failed request."""
        with self.lock:
            self.failures.append(datetime.utcnow())
            self.last_failure_time = datetime.utcnow()

            # Count failures within window
            cutoff = datetime.utcnow() - timedelta(seconds=self.config.failure_window_seconds)
            recent_failures = sum(1 for f in self.failures if f > cutoff)

            if recent_failures >= self.config.failure_threshold:
                if self.state != CircuitBreakerState.OPEN:
                    self._transition_to(CircuitBreakerState.OPEN)

            elif self.state == CircuitBreakerState.HALF_OPEN:
                self._transition_to(CircuitBreakerState.OPEN)
                self.successes_in_half_open = 0

    def can_execute(self) -> bool:
        """Check if request can be executed."""
        with self.lock:
            if self.state == CircuitBreakerState.CLOSED:
                return True

            elif self.state == CircuitBreakerState.OPEN:
                # Check if recovery timeout has elapsed
                elapsed = (datetime.utcnow() - self.last_state_change).total_seconds()
                if elapsed >= self.config.recovery_timeout_seconds:
                    self._transition_to(CircuitBreakerState.HALF_OPEN)
                    self.successes_in_half_open = 0
                    return True
                return False

            elif self.state == CircuitBreakerState.HALF_OPEN:
                return True

            return False

    def _transition_to(self, new_state: CircuitBreakerState) -> None:
        """Internal: transition to new state (lock must be held)."""
        old_state = self.state
        self.state = new_state
        self.last_state_change = datetime.utcnow()
        logger.info(f"Circuit breaker {self.config.agent_id}: {old_state.name} -> {new_state.name}")


@dataclass
class ChaosScenario:
    """Controlled chaos scenario for resilience testing."""
    scenario_id: str
    agent_id: str
    scenario_type: ChaosScenarioType
    description: str
    duration_seconds: int
    intensity: float                   # 0.0-1.0
    affected_agents: List[str]
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    director_approval: Optional[str] = None  # Director role who approved
    approval_timestamp: Optional[datetime] = None
    approval_status: DirectorApprovalStatus = DirectorApprovalStatus.PENDING


@dataclass
class IncidentRecord:
    """Record of incident detected during SRE monitoring."""
    incident_id: str
    timestamp: datetime
    agent_id: str
    agent_class: str
    incident_type: str                 # slo_violation, circuit_breaker_open, budget_exhausted
    description: str
    severity: int                      # 1-5, higher is more severe
    slo_violations: List[SLOViolation] = field(default_factory=list)
    remediation_started: Optional[datetime] = None
    remediation_completed: Optional[datetime] = None
    root_cause_analysis: str = ""


# ============================================================================
# ErrorBudgetManager Class
# ============================================================================

class ErrorBudgetManager:
    """
    Manages error budgets for agent classes, mapping AGT error budgets
    to ADAM's Exception Economy autonomy budgets.
    """

    def __init__(self, logger_instance=None):
        """Initialize error budget manager."""
        self.logger = logger_instance or logger
        self.budgets: Dict[str, ErrorBudget] = {}
        self.budget_lock = threading.RLock()
        self.budget_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._initialize_budgets()

    def _initialize_budgets(self) -> None:
        """Initialize error budgets for all agent classes."""
        for agent_class, config in AGENT_CLASSES.items():
            budget = ErrorBudget(
                agent_class=agent_class,
                total_minutes_month=config["budget_minutes_month"],
            )
            with self.budget_lock:
                self.budgets[agent_class] = budget

            self.logger.info(
                f"Initialized error budget for {agent_class}: "
                f"{config['budget_minutes_month']:.1f} minutes/month"
            )

    def consume_budget(self, agent_class: str, minutes: float) -> Tuple[bool, str]:
        """
        Attempt to consume from error budget.

        Args:
            agent_class: Agent class name
            minutes: Minutes to consume

        Returns:
            Tuple of (success, reason)
        """
        with self.budget_lock:
            if agent_class not in self.budgets:
                return False, f"Unknown agent class: {agent_class}"

            budget = self.budgets[agent_class]

            if budget.consume(minutes):
                self._record_budget_event(agent_class, "consume", minutes)

                if budget.in_emergency_mode():
                    self.logger.warning(
                        f"Error budget {agent_class} in EMERGENCY MODE: "
                        f"{budget.percent_remaining():.1f}% remaining"
                    )

                return True, f"Consumed {minutes:.2f} minutes from {agent_class} budget"

            return False, f"Error budget {agent_class} exhausted"

    def get_budget_status(self, agent_class: str) -> Dict[str, Any]:
        """Get current budget status."""
        with self.budget_lock:
            if agent_class not in self.budgets:
                return {}

            budget = self.budgets[agent_class]
            return {
                "agent_class": agent_class,
                "total_minutes_month": budget.total_minutes_month,
                "consumed_minutes": budget.consumed_minutes,
                "remaining_minutes": budget.total_minutes_month - budget.consumed_minutes,
                "percent_consumed": 100.0 - budget.percent_remaining(),
                "percent_remaining": budget.percent_remaining(),
                "in_emergency_mode": budget.in_emergency_mode(),
                "is_exhausted": budget.is_exhausted(),
            }

    def _record_budget_event(self, agent_class: str, event_type: str, amount: float) -> None:
        """Record budget consumption event for audit trail."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "amount_minutes": amount,
            "budget_state": asdict(self.budgets[agent_class]),
        }
        self.budget_history[agent_class].append(event)


# ============================================================================
# CircuitBreakerManager Class
# ============================================================================

class CircuitBreakerManager:
    """
    Manages circuit breakers for agent resilience. Integrates circuit
    breaker state with BOSS score thresholds.
    """

    def __init__(self, logger_instance=None):
        """Initialize circuit breaker manager."""
        self.logger = logger_instance or logger
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.breaker_lock = threading.RLock()

    def register_breaker(self, config: CircuitBreakerConfig) -> CircuitBreaker:
        """Register new circuit breaker."""
        breaker = CircuitBreaker(config=config)

        with self.breaker_lock:
            self.breakers[config.agent_id] = breaker

        self.logger.info(f"Registered circuit breaker for agent {config.agent_id}")
        return breaker

    def evaluate_boss_score(self, agent_id: str, boss_score: int) -> None:
        """
        Evaluate BOSS score and adjust circuit breaker state.

        Args:
            agent_id: Agent identifier
            boss_score: Current BOSS score (0-100)
        """
        with self.breaker_lock:
            if agent_id not in self.breakers:
                return

            breaker = self.breakers[agent_id]

            # Activate circuit breaker if BOSS is ELEVATED or higher
            if boss_score >= breaker.config.boss_activation_threshold:
                if breaker.state == CircuitBreakerState.CLOSED:
                    # Force to OPEN if BOSS score is high
                    with breaker.lock:
                        breaker._transition_to(CircuitBreakerState.OPEN)
                    self.logger.warning(
                        f"Circuit breaker {agent_id} forced OPEN due to BOSS={boss_score}"
                    )

    def can_execute(self, agent_id: str) -> bool:
        """Check if agent can execute given circuit breaker state."""
        with self.breaker_lock:
            if agent_id not in self.breakers:
                return True
            return self.breakers[agent_id].can_execute()

    def record_execution(self, agent_id: str, success: bool) -> None:
        """Record execution result for circuit breaker."""
        with self.breaker_lock:
            if agent_id not in self.breakers:
                return

            breaker = self.breakers[agent_id]
            if success:
                breaker.record_success()
            else:
                breaker.record_failure()

    def get_breaker_status(self, agent_id: str) -> Dict[str, Any]:
        """Get circuit breaker status."""
        with self.breaker_lock:
            if agent_id not in self.breakers:
                return {}

            breaker = self.breakers[agent_id]
            return {
                "agent_id": agent_id,
                "state": breaker.state.name,
                "failure_count": len(breaker.failures),
                "last_failure": breaker.last_failure_time.isoformat() if breaker.last_failure_time else None,
                "last_state_change": breaker.last_state_change.isoformat(),
                "config": asdict(breaker.config),
            }


# ============================================================================
# ChaosEngineer Class
# ============================================================================

class ChaosEngineer:
    """
    Controlled fault injection for resilience testing within ADAM
    governance bounds. Requires Director approval for MODERATE+ scenarios.
    """

    def __init__(self, logger_instance=None):
        """Initialize chaos engineer."""
        self.logger = logger_instance or logger
        self.scenarios: Dict[str, ChaosScenario] = {}
        self.scenario_lock = threading.RLock()
        self.director_approvers: Dict[str, Callable] = {}  # Role -> approver callback
        self.active_effects: Dict[str, Callable] = {}  # scenario_id -> effect function

    def register_director_approver(self, role: str, approver: Callable) -> None:
        """
        Register director role as approver for chaos scenarios.

        Args:
            role: Director role (CEO, CFO, Legal, Market, CISO)
            approver: Callback to check approval status
        """
        self.director_approvers[role] = approver

    def propose_scenario(self, agent_id: str, scenario_type: ChaosScenarioType,
                        description: str, duration_seconds: int, intensity: float,
                        affected_agents: List[str]) -> ChaosScenario:
        """
        Propose chaos scenario (requires Director approval for MODERATE+).

        Args:
            agent_id: Proposing agent
            scenario_type: Type of chaos
            description: Scenario description
            duration_seconds: Duration of scenario
            intensity: Intensity 0.0-1.0
            affected_agents: Agents to affect

        Returns:
            ChaosScenario instance
        """
        scenario_id = f"chaos-{uuid.uuid4().hex[:12]}"

        scenario = ChaosScenario(
            scenario_id=scenario_id,
            agent_id=agent_id,
            scenario_type=scenario_type,
            description=description,
            duration_seconds=duration_seconds,
            intensity=intensity,
            affected_agents=affected_agents,
        )

        with self.scenario_lock:
            self.scenarios[scenario_id] = scenario

        self.logger.info(
            f"Proposed chaos scenario {scenario_id}: {scenario_type.name} "
            f"({duration_seconds}s, intensity={intensity:.1f})"
        )

        return scenario

    def request_director_approval(self, scenario_id: str) -> bool:
        """
        Request approval from Director Constitution for chaos scenario.

        Args:
            scenario_id: Scenario ID

        Returns:
            True if approval granted
        """
        with self.scenario_lock:
            if scenario_id not in self.scenarios:
                return False

            scenario = self.scenarios[scenario_id]

        # Request from one approver (in production, would be all directors)
        for role, approver in self.director_approvers.items():
            try:
                if approver(scenario):
                    with self.scenario_lock:
                        scenario.director_approval = role
                        scenario.approval_timestamp = datetime.utcnow()
                        scenario.approval_status = DirectorApprovalStatus.APPROVED

                    self.logger.info(
                        f"Chaos scenario {scenario_id} approved by {role}"
                    )
                    return True
            except Exception as exc:
                self.logger.error(f"Director approval check failed: {exc}")

        return False

    def execute_scenario(self, scenario_id: str, boss_score: int) -> bool:
        """
        Execute approved chaos scenario if requirements are met.

        Args:
            scenario_id: Scenario ID
            boss_score: Current BOSS score

        Returns:
            True if scenario was executed
        """
        with self.scenario_lock:
            if scenario_id not in self.scenarios:
                return False

            scenario = self.scenarios[scenario_id]

        # Require approval for MODERATE (21+) scenarios
        if boss_score >= BOSS_THRESHOLDS["MODERATE"][0]:
            if scenario.approval_status != DirectorApprovalStatus.APPROVED:
                self.logger.warning(
                    f"Chaos scenario {scenario_id} rejected: requires approval "
                    f"for BOSS={boss_score}"
                )
                return False

        # Execute scenario
        try:
            with self.scenario_lock:
                scenario.started_at = datetime.utcnow()

            self.logger.info(
                f"Executing chaos scenario {scenario_id}: {scenario.description}"
            )

            # Create effect function based on scenario type
            effect = self._create_effect(scenario)
            with self.scenario_lock:
                self.active_effects[scenario_id] = effect

            # Simulate execution (in production, would actually inject faults)
            self._simulate_chaos_effect(scenario, effect)

            with self.scenario_lock:
                scenario.completed_at = datetime.utcnow()
                del self.active_effects[scenario_id]

            self.logger.info(f"Chaos scenario {scenario_id} completed")
            return True

        except Exception as exc:
            self.logger.error(f"Chaos scenario {scenario_id} failed: {exc}")
            return False

    def _create_effect(self, scenario: ChaosScenario) -> Callable:
        """Create effect function for scenario."""
        if scenario.scenario_type == ChaosScenarioType.LATENCY_INJECTION:
            return lambda: self._latency_effect(scenario)
        elif scenario.scenario_type == ChaosScenarioType.ERROR_INJECTION:
            return lambda: self._error_effect(scenario)
        elif scenario.scenario_type == ChaosScenarioType.RESOURCE_STARVATION:
            return lambda: self._resource_effect(scenario)
        elif scenario.scenario_type == ChaosScenarioType.NETWORK_PARTITION:
            return lambda: self._network_effect(scenario)
        elif scenario.scenario_type == ChaosScenarioType.CASCADING_FAILURE:
            return lambda: self._cascading_effect(scenario)

        return lambda: None

    def _latency_effect(self, scenario: ChaosScenario) -> None:
        """Simulate latency injection."""
        self.logger.debug(
            f"Latency injection: +{scenario.intensity * 1000:.0f}ms "
            f"for {scenario.affected_agents}"
        )

    def _error_effect(self, scenario: ChaosScenario) -> None:
        """Simulate error injection."""
        error_rate = scenario.intensity * 100.0
        self.logger.debug(
            f"Error injection: {error_rate:.1f}% error rate for {scenario.affected_agents}"
        )

    def _resource_effect(self, scenario: ChaosScenario) -> None:
        """Simulate resource starvation."""
        self.logger.debug(
            f"Resource starvation: {(1.0 - scenario.intensity) * 100:.0f}% available "
            f"for {scenario.affected_agents}"
        )

    def _network_effect(self, scenario: ChaosScenario) -> None:
        """Simulate network partition."""
        self.logger.debug(
            f"Network partition: {scenario.intensity * 100:.0f}% packet loss "
            f"for {scenario.affected_agents}"
        )

    def _cascading_effect(self, scenario: ChaosScenario) -> None:
        """Simulate cascading failure."""
        self.logger.debug(
            f"Cascading failure: {len(scenario.affected_agents)} agents affected, "
            f"intensity={scenario.intensity:.1f}"
        )

    def _simulate_chaos_effect(self, scenario: ChaosScenario, effect: Callable) -> None:
        """Simulate chaos effect."""
        effect()

    def get_scenario(self, scenario_id: str) -> Optional[ChaosScenario]:
        """Retrieve scenario by ID."""
        with self.scenario_lock:
            return self.scenarios.get(scenario_id)


# ============================================================================
# SLOMonitor Class
# ============================================================================

class SLOMonitor:
    """
    Monitors Service Level Objectives (SLOs) per agent class with
    different latency/availability targets.
    """

    def __init__(self, logger_instance=None):
        """Initialize SLO monitor."""
        self.logger = logger_instance or logger
        self.slos: Dict[str, ServiceLevelObjective] = {}
        self.samples: Dict[str, Deque[MetricSample]] = defaultdict(lambda: deque(maxlen=1000))
        self.violations: Dict[str, List[SLOViolation]] = defaultdict(list)
        self.monitor_lock = threading.RLock()
        self._initialize_slos()

    def _initialize_slos(self) -> None:
        """Initialize SLOs for all agent classes."""
        for agent_class, config in AGENT_CLASSES.items():
            slo = ServiceLevelObjective(
                agent_class=agent_class,
                availability_slo=config["availability_slo"],
                latency_slo_ms=config["latency_slo_ms"],
                error_rate_slo=config["error_rate_slo"],
            )
            with self.monitor_lock:
                self.slos[agent_class] = slo

            self.logger.info(
                f"Initialized SLO for {agent_class}: "
                f"{config['availability_slo']:.2f}% availability, "
                f"{config['latency_slo_ms']}ms latency"
            )

    def record_metric(self, agent_id: str, agent_class: str,
                     latency_ms: Optional[float] = None,
                     is_error: bool = False,
                     is_available: bool = True) -> None:
        """
        Record metric sample for agent.

        Args:
            agent_id: Agent identifier
            agent_class: Agent class (STRATEGIC, TACTICAL, etc.)
            latency_ms: Request latency in milliseconds
            is_error: Whether request resulted in error
            is_available: Whether agent is available
        """
        sample = MetricSample(
            timestamp=datetime.utcnow(),
            latency_ms=latency_ms,
            is_error=is_error,
            is_available=is_available,
            metadata={"agent_id": agent_id, "agent_class": agent_class},
        )

        with self.monitor_lock:
            self.samples[agent_id].append(sample)

        # Check SLO compliance
        self._check_slo_violation(agent_id, agent_class)

    def get_slo_status(self, agent_id: str, agent_class: str) -> Dict[str, Any]:
        """Get current SLO compliance status."""
        with self.monitor_lock:
            if agent_id not in self.samples:
                return {"status": "no_data"}

            samples = list(self.samples[agent_id])
            if not samples:
                return {"status": "no_data"}

            slo = self.slos.get(agent_class)
            if not slo:
                return {"status": "unknown_class"}

            # Calculate metrics
            latencies = [s.latency_ms for s in samples if s.latency_ms is not None]
            errors = sum(1 for s in samples if s.is_error)
            available = sum(1 for s in samples if s.is_available)

            p50_latency = statistics.median(latencies) if latencies else None
            p99_latency = sorted(latencies)[int(len(latencies) * 0.99)] if len(latencies) > 0.01 * len(samples) else None
            availability = (available / len(samples)) * 100.0 if samples else 0.0
            error_rate = (errors / len(samples)) * 100.0 if samples else 0.0

            return {
                "agent_id": agent_id,
                "agent_class": agent_class,
                "sample_count": len(samples),
                "p50_latency_ms": p50_latency,
                "p99_latency_ms": p99_latency,
                "latency_slo_ms": slo.latency_slo_ms,
                "latency_violated": p99_latency and p99_latency > slo.latency_slo_ms,
                "availability_percent": availability,
                "availability_slo": slo.availability_slo,
                "availability_violated": availability < slo.availability_slo,
                "error_rate_percent": error_rate,
                "error_rate_slo": slo.error_rate_slo,
                "error_rate_violated": error_rate > slo.error_rate_slo,
            }

    def _check_slo_violation(self, agent_id: str, agent_class: str) -> None:
        """Check and record SLO violations."""
        status = self.get_slo_status(agent_id, agent_class)

        violations = []
        if status.get("latency_violated"):
            violations.append("latency")
        if status.get("availability_violated"):
            violations.append("availability")
        if status.get("error_rate_violated"):
            violations.append("error_rate")

        if violations:
            violation = SLOViolation(
                violation_id=f"slo-{uuid.uuid4().hex[:12]}",
                agent_id=agent_id,
                agent_class=agent_class,
                timestamp=datetime.utcnow(),
                slo_type=",".join(violations),
                current_value=status.get("p99_latency_ms", 0.0),
                slo_target=self.slos[agent_class].latency_slo_ms,
                duration_seconds=60,
            )

            with self.monitor_lock:
                self.violations[agent_id].append(violation)

            self.logger.warning(
                f"SLO violation for {agent_id}: {', '.join(violations)}"
            )


# ============================================================================
# AdamSREIntegration Class (Main SRE Orchestrator)
# ============================================================================

class AdamSREIntegration:
    """
    Full SRE lifecycle management bridging AGT Agent SRE with ADAM
    Stability & Drift Plane.
    """

    def __init__(self, logger_instance=None):
        """Initialize ADAM SRE Integration."""
        self.logger = logger_instance or logger
        self.error_budget_manager = ErrorBudgetManager(self.logger)
        self.circuit_breaker_manager = CircuitBreakerManager(self.logger)
        self.chaos_engineer = ChaosEngineer(self.logger)
        self.slo_monitor = SLOMonitor(self.logger)
        self.incidents: Dict[str, IncidentRecord] = {}
        self.incident_lock = threading.RLock()

    def setup_agent_class(self, agent_id: str, agent_class: str) -> None:
        """Setup SRE monitoring for agent."""
        # Register circuit breaker
        config = CircuitBreakerConfig(
            agent_id=agent_id,
            boss_activation_threshold=BOSS_THRESHOLDS["ELEVATED"][0],
        )
        self.circuit_breaker_manager.register_breaker(config)

        self.logger.info(f"Setup SRE monitoring for {agent_id} ({agent_class})")

    def evaluate_agent_health(self, agent_id: str, agent_class: str,
                             boss_score: int) -> Dict[str, Any]:
        """
        Comprehensive health evaluation for agent.

        Args:
            agent_id: Agent identifier
            agent_class: Agent class
            boss_score: Current BOSS score

        Returns:
            Health evaluation summary
        """
        # Get SLO status
        slo_status = self.slo_monitor.get_slo_status(agent_id, agent_class)

        # Get error budget status
        budget_status = self.error_budget_manager.get_budget_status(agent_class)

        # Get circuit breaker status
        cb_status = self.circuit_breaker_manager.get_breaker_status(agent_id)

        # Evaluate overall health
        health_score = 100.0
        issues = []

        if slo_status.get("latency_violated"):
            health_score -= 20.0
            issues.append("Latency SLO violated")

        if slo_status.get("availability_violated"):
            health_score -= 25.0
            issues.append("Availability SLO violated")

        if slo_status.get("error_rate_violated"):
            health_score -= 15.0
            issues.append("Error rate SLO violated")

        if budget_status.get("in_emergency_mode"):
            health_score -= 10.0
            issues.append("Error budget in emergency mode")

        if cb_status.get("state") == "OPEN":
            health_score -= 30.0
            issues.append("Circuit breaker OPEN")

        if boss_score >= BOSS_THRESHOLDS["HIGH"][0]:
            health_score -= 15.0
            issues.append(f"BOSS score HIGH ({boss_score})")

        return {
            "agent_id": agent_id,
            "agent_class": agent_class,
            "health_score": max(0.0, health_score),
            "boss_score": boss_score,
            "slo_status": slo_status,
            "budget_status": budget_status,
            "circuit_breaker_status": cb_status,
            "issues": issues,
        }

    def create_incident(self, agent_id: str, agent_class: str,
                       incident_type: str, description: str,
                       severity: int) -> IncidentRecord:
        """Create incident record."""
        incident_id = f"incident-{uuid.uuid4().hex[:12]}"

        incident = IncidentRecord(
            incident_id=incident_id,
            timestamp=datetime.utcnow(),
            agent_id=agent_id,
            agent_class=agent_class,
            incident_type=incident_type,
            description=description,
            severity=severity,
        )

        with self.incident_lock:
            self.incidents[incident_id] = incident

        self.logger.critical(
            f"Incident created {incident_id}: {incident_type} (severity={severity})"
        )

        return incident

    def shutdown(self) -> None:
        """Graceful shutdown of SRE integration."""
        self.logger.info("Shutting down ADAM SRE Integration")


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
    logger.info("ADAM SRE Integration module loaded")
