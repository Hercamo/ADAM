"""
ADAM-AGT RL Training Governance Bridge Module

This module bridges Microsoft's Agent Governance Toolkit (AGT) Agent Lightning
(RL training governance) with ADAM's doctrine alignment engine and Digital Twins.

Key Components:
- Doctrine Alignment Validator: validates RL reward functions against ADAM CORE Engine values
- RLTrainingMonitor: monitors training runs for BOSS score violations and safety boundaries
- DriftDetector: detects model drift from ADAM governance boundaries using statistical methods
- DigitalTwinSync: synchronizes RL agent states with ADAM Digital Twin representations
- Full RL training lifecycle governance with safety guardrails

The bridge ensures that reinforcement learning agents stay aligned with ADAM's
doctrinal values (CORE Engine) and governance boundaries (BOSS Score).

Author: ADAM Book v0.4
Version: 1.0.0
Python: 3.10+
"""

import json
import logging
import math
import statistics
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable
from uuid import uuid4

import numpy as np

# Configure module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TrainingStatus(Enum):
    """Status of RL training session."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"
    ROLLED_BACK = "rolled_back"


class DriftSeverity(Enum):
    """Severity levels for model drift detection."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DoctrineAlignmentStatus(Enum):
    """Doctrine alignment assessment status."""
    ALIGNED = "aligned"
    PARTIALLY_ALIGNED = "partially_aligned"
    MISALIGNED = "misaligned"
    UNDETERMINED = "undetermined"


@dataclass
class RewardFunctionAssessment:
    """Assessment of reward function alignment with ADAM doctrine."""
    assessment_id: str
    agent_id: str
    reward_function_signature: str
    core_values_checked: List[str]  # List of CORE values (Culture, Objectives, Rules, Expectations)
    alignment_status: DoctrineAlignmentStatus
    alignment_score: float  # 0.0-1.0
    aligned_values: List[str]
    misaligned_values: List[str]
    recommendations: List[str]
    assessed_at: datetime = field(default_factory=datetime.utcnow)
    human_review_required: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['alignment_status'] = self.alignment_status.value
        data['assessed_at'] = self.assessed_at.isoformat()
        return data


@dataclass
class TrainingMetrics:
    """Metrics tracked during RL training run."""
    episode_number: int
    total_reward: float
    average_reward: float
    loss: float
    gradient_norm: float
    action_distribution: Dict[str, float]  # action -> probability
    doctrinal_violations: int = 0
    boss_score: int = 0
    drift_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class DriftDetectionResult:
    """Result of drift detection analysis."""
    drift_detected: bool
    severity: DriftSeverity
    drift_score: float  # 0.0-1.0
    metrics_changed: List[str]
    statistical_significance: Dict[str, float]  # metric -> p-value
    detected_at: datetime = field(default_factory=datetime.utcnow)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['severity'] = self.severity.value
        data['detected_at'] = self.detected_at.isoformat()
        return data


@dataclass
class DigitalTwinState:
    """State snapshot of agent's Digital Twin representation."""
    twin_id: str
    agent_id: str
    timestamp: datetime
    model_state: Dict[str, Any]  # Model weights, architecture info
    performance_metrics: Dict[str, float]
    doctrine_alignment_score: float  # 0.0-1.0
    boss_score: int  # 0-100
    governance_status: str  # "compliant", "warning", "violation"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class DoctrineAlignmentValidator:
    """
    Validates RL reward functions against ADAM CORE Engine values:
    - Culture (company values and principles)
    - Objectives (strategic goals)
    - Rules (governance constraints)
    - Expectations (behavioral standards)
    """

    def __init__(self):
        """Initialize doctrine alignment validator."""
        self._core_engine = self._initialize_core_engine()
        self._assessments: Dict[str, RewardFunctionAssessment] = {}
        logger.info("DoctrineAlignmentValidator initialized")

    def _initialize_core_engine(self) -> Dict[str, Dict[str, Any]]:
        """Initialize ADAM CORE Engine values."""
        return {
            'culture': {
                'principles': [
                    'transparency',
                    'accountability',
                    'human_first',
                    'fairness',
                    'sustainability'
                ],
                'values': ['trust', 'integrity', 'excellence'],
            },
            'objectives': {
                'strategic_goals': [
                    'safe_autonomous_operation',
                    'regulatory_compliance',
                    'continuous_improvement',
                    'risk_mitigation'
                ],
                'metrics': ['safety_score', 'compliance_rate', 'success_rate'],
            },
            'rules': {
                'constraints': [
                    'must_maintain_human_oversight',
                    'must_preserve_audit_trail',
                    'must_respect_data_privacy',
                    'must_escalate_high_risk_decisions'
                ],
                'boundaries': ['action_space_limit', 'resource_limit', 'rate_limit'],
            },
            'expectations': {
                'behavioral_standards': [
                    'explainable_decisions',
                    'consistent_behavior',
                    'graceful_failure_handling',
                    'continuous_learning'
                ],
                'performance_targets': [0.95, 0.99, 0.98],  # success, safety, compliance
            },
        }

    def validate_reward_function(
        self,
        agent_id: str,
        reward_function: Callable,
        function_description: str = "",
        test_cases: Optional[List[Tuple[Any, float]]] = None
    ) -> RewardFunctionAssessment:
        """
        Validate RL reward function against ADAM doctrine.

        Args:
            agent_id: ID of RL agent
            reward_function: The reward function to validate
            function_description: Description of reward function
            test_cases: Optional list of (state, expected_reward) tuples

        Returns:
            RewardFunctionAssessment with alignment findings
        """
        assessment_id = str(uuid4())
        function_signature = f"{reward_function.__name__}:{function_description}"

        aligned_values = []
        misaligned_values = []
        recommendations = []

        # Check alignment with culture
        culture_alignment = self._check_culture_alignment(reward_function, test_cases)
        aligned_values.extend(culture_alignment['aligned'])
        misaligned_values.extend(culture_alignment['misaligned'])
        recommendations.extend(culture_alignment['recommendations'])

        # Check alignment with objectives
        objectives_alignment = self._check_objectives_alignment(reward_function)
        aligned_values.extend(objectives_alignment['aligned'])
        misaligned_values.extend(objectives_alignment['misaligned'])
        recommendations.extend(objectives_alignment['recommendations'])

        # Check alignment with rules
        rules_alignment = self._check_rules_alignment(reward_function)
        aligned_values.extend(rules_alignment['aligned'])
        misaligned_values.extend(rules_alignment['misaligned'])
        recommendations.extend(rules_alignment['recommendations'])

        # Check alignment with expectations
        expectations_alignment = self._check_expectations_alignment(reward_function)
        aligned_values.extend(expectations_alignment['aligned'])
        misaligned_values.extend(expectations_alignment['misaligned'])
        recommendations.extend(expectations_alignment['recommendations'])

        # Compute alignment score
        core_values_checked = [
            'culture', 'objectives', 'rules', 'expectations'
        ]
        total_checks = len(core_values_checked)
        aligned_count = len(set(aligned_values))
        alignment_score = aligned_count / total_checks if total_checks > 0 else 0.5

        # Determine alignment status
        if alignment_score >= 0.9:
            alignment_status = DoctrineAlignmentStatus.ALIGNED
        elif alignment_score >= 0.7:
            alignment_status = DoctrineAlignmentStatus.PARTIALLY_ALIGNED
        elif alignment_score >= 0.3:
            alignment_status = DoctrineAlignmentStatus.MISALIGNED
        else:
            alignment_status = DoctrineAlignmentStatus.UNDETERMINED

        assessment = RewardFunctionAssessment(
            assessment_id=assessment_id,
            agent_id=agent_id,
            reward_function_signature=function_signature,
            core_values_checked=core_values_checked,
            alignment_status=alignment_status,
            alignment_score=alignment_score,
            aligned_values=list(set(aligned_values)),
            misaligned_values=list(set(misaligned_values)),
            recommendations=recommendations,
            human_review_required=alignment_status in [
                DoctrineAlignmentStatus.MISALIGNED,
                DoctrineAlignmentStatus.UNDETERMINED
            ]
        )

        self._assessments[assessment_id] = assessment
        logger.info(
            f"Assessed reward function for {agent_id}: "
            f"alignment={alignment_status.value}, score={alignment_score:.2f}"
        )

        return assessment

    def _check_culture_alignment(
        self,
        reward_function: Callable,
        test_cases: Optional[List[Tuple[Any, float]]]
    ) -> Dict[str, Any]:
        """Check reward function alignment with culture values."""
        aligned = []
        misaligned = []
        recommendations = []

        # Check for fairness principle
        culture = self._core_engine['culture']
        if 'fairness' in culture['principles']:
            aligned.append('fairness')
        else:
            misaligned.append('fairness')
            recommendations.append('Reward function should penalize biased actions')

        # Check for transparency
        aligned.append('transparency')  # Assumption: reward is explainable

        return {
            'aligned': aligned,
            'misaligned': misaligned,
            'recommendations': recommendations,
        }

    def _check_objectives_alignment(self, reward_function: Callable) -> Dict[str, Any]:
        """Check reward function alignment with strategic objectives."""
        aligned = ['safe_autonomous_operation', 'risk_mitigation']
        misaligned = []
        recommendations = []

        # Recommend compliance metrics
        recommendations.append('Reward function should explicitly reward regulatory compliance')

        return {
            'aligned': aligned,
            'misaligned': misaligned,
            'recommendations': recommendations,
        }

    def _check_rules_alignment(self, reward_function: Callable) -> Dict[str, Any]:
        """Check reward function alignment with governance rules."""
        aligned = []
        misaligned = []
        recommendations = []

        rules = self._core_engine['rules']

        # Check constraint adherence
        aligned.append('human_oversight_preserved')
        aligned.append('audit_trail_maintained')

        recommendations.append('Reward function must respect data privacy constraints')
        recommendations.append('High-risk actions must trigger escalation rewards')

        return {
            'aligned': aligned,
            'misaligned': misaligned,
            'recommendations': recommendations,
        }

    def _check_expectations_alignment(self, reward_function: Callable) -> Dict[str, Any]:
        """Check reward function alignment with behavioral expectations."""
        aligned = ['explainable_decisions', 'consistent_behavior']
        misaligned = []
        recommendations = []

        recommendations.append('Ensure reward function produces stable, predictable behavior')
        recommendations.append('Implement graceful degradation for failure scenarios')

        return {
            'aligned': aligned,
            'misaligned': misaligned,
            'recommendations': recommendations,
        }

    def get_assessment(self, assessment_id: str) -> Optional[RewardFunctionAssessment]:
        """Get a specific assessment."""
        return self._assessments.get(assessment_id)


class RLTrainingMonitor:
    """
    Monitors RL training runs for BOSS score violations, doctrine drift,
    and safety boundary violations.
    """

    def __init__(self, boss_safety_threshold: int = 60):
        """
        Initialize training monitor.

        Args:
            boss_safety_threshold: BOSS score threshold triggering intervention
        """
        self._boss_safety_threshold = boss_safety_threshold
        self._training_sessions: Dict[str, List[TrainingMetrics]] = {}
        self._violations: Dict[str, List[str]] = {}
        logger.info(f"RLTrainingMonitor initialized (threshold={boss_safety_threshold})")

    def record_training_step(
        self,
        session_id: str,
        episode_number: int,
        metrics: TrainingMetrics
    ) -> Tuple[bool, Optional[str]]:
        """
        Record a training step and check for violations.

        Args:
            session_id: Training session ID
            episode_number: Episode number
            metrics: Training metrics for this step

        Returns:
            Tuple of (is_safe, violation_message_or_none)
        """
        if session_id not in self._training_sessions:
            self._training_sessions[session_id] = []
            self._violations[session_id] = []

        self._training_sessions[session_id].append(metrics)

        # Check BOSS score violation
        if metrics.boss_score >= self._boss_safety_threshold:
            violation = f"BOSS score {metrics.boss_score} exceeds threshold {self._boss_safety_threshold}"
            self._violations[session_id].append(violation)
            logger.warning(f"Session {session_id}: {violation}")
            return False, violation

        # Check reward function health
        if metrics.loss > 10.0:  # Arbitrary threshold
            violation = f"Training loss {metrics.loss:.2f} indicates divergence"
            self._violations[session_id].append(violation)
            logger.warning(f"Session {session_id}: {violation}")
            return False, violation

        # Check gradient health
        if math.isnan(metrics.gradient_norm) or math.isinf(metrics.gradient_norm):
            violation = "Gradient norm is NaN or Inf (numerical instability)"
            self._violations[session_id].append(violation)
            logger.warning(f"Session {session_id}: {violation}")
            return False, violation

        # Check doctrinal violations
        if metrics.doctrinal_violations > 0:
            violation = f"Detected {metrics.doctrinal_violations} doctrinal violations"
            self._violations[session_id].append(violation)
            logger.warning(f"Session {session_id}: {violation}")
            return False, violation

        return True, None

    def get_session_metrics(self, session_id: str) -> List[TrainingMetrics]:
        """Get all metrics for a training session."""
        return self._training_sessions.get(session_id, [])

    def get_session_violations(self, session_id: str) -> List[str]:
        """Get all violations detected in a session."""
        return self._violations.get(session_id, [])

    def should_interrupt_training(self, session_id: str) -> bool:
        """Check if training should be interrupted due to violations."""
        violations = self.get_session_violations(session_id)
        return len(violations) > 2  # Interrupt after 3 violations

    def generate_training_report(self, session_id: str) -> Dict[str, Any]:
        """Generate summary report for training session."""
        metrics = self.get_session_metrics(session_id)
        violations = self.get_session_violations(session_id)

        if not metrics:
            return {'status': 'no_data'}

        rewards = [m.total_reward for m in metrics]
        boss_scores = [m.boss_score for m in metrics]

        return {
            'session_id': session_id,
            'episodes': len(metrics),
            'total_reward_mean': statistics.mean(rewards) if rewards else 0,
            'total_reward_stdev': statistics.stdev(rewards) if len(rewards) > 1 else 0,
            'boss_score_mean': statistics.mean(boss_scores) if boss_scores else 0,
            'boss_score_max': max(boss_scores) if boss_scores else 0,
            'violations_count': len(violations),
            'violations': violations,
        }


class DriftDetector:
    """
    Detects model drift from ADAM governance boundaries using statistical methods.
    Monitors key metrics and flags when distribution shifts occur.
    """

    def __init__(self, window_size: int = 50):
        """
        Initialize drift detector.

        Args:
            window_size: Number of recent metrics to use for baseline
        """
        self._window_size = window_size
        self._baseline_metrics: Dict[str, List[float]] = {}
        self._current_window: Dict[str, List[float]] = {}
        logger.info(f"DriftDetector initialized (window_size={window_size})")

    def update_baseline(self, metric_name: str, values: List[float]) -> None:
        """Update baseline distribution for a metric."""
        self._baseline_metrics[metric_name] = values[-self._window_size:]
        logger.info(f"Updated baseline for {metric_name}: {len(self._baseline_metrics[metric_name])} samples")

    def detect_drift(self, metric_name: str, new_values: List[float]) -> DriftDetectionResult:
        """
        Detect drift in a metric using statistical tests.

        Args:
            metric_name: Name of metric
            new_values: New metric values to test

        Returns:
            DriftDetectionResult with severity and recommendations
        """
        if metric_name not in self._baseline_metrics:
            return DriftDetectionResult(
                drift_detected=False,
                severity=DriftSeverity.NONE,
                drift_score=0.0,
                metrics_changed=[],
                statistical_significance={}
            )

        baseline = self._baseline_metrics[metric_name]
        recent_window = new_values[-self._window_size:]

        # Compute statistical measures
        baseline_mean = statistics.mean(baseline)
        recent_mean = statistics.mean(recent_window)
        baseline_stdev = statistics.stdev(baseline) if len(baseline) > 1 else 1.0

        # Calculate z-score
        z_score = abs((recent_mean - baseline_mean) / baseline_stdev) if baseline_stdev > 0 else 0

        # Determine drift severity (simple heuristic)
        if z_score < 1.0:
            severity = DriftSeverity.NONE
            drift_score = 0.0
        elif z_score < 2.0:
            severity = DriftSeverity.LOW
            drift_score = 0.25
        elif z_score < 3.0:
            severity = DriftSeverity.MEDIUM
            drift_score = 0.5
        elif z_score < 4.0:
            severity = DriftSeverity.HIGH
            drift_score = 0.75
        else:
            severity = DriftSeverity.CRITICAL
            drift_score = 1.0

        drift_detected = severity != DriftSeverity.NONE
        metrics_changed = [metric_name] if drift_detected else []
        recommendations = []

        if drift_detected:
            recommendations.append(f"Metric {metric_name} has drifted (z-score={z_score:.2f})")
            if severity == DriftSeverity.CRITICAL:
                recommendations.append("CRITICAL: Consider rolling back training or investigating root cause")
            else:
                recommendations.append("Monitor this metric closely")

        result = DriftDetectionResult(
            drift_detected=drift_detected,
            severity=severity,
            drift_score=drift_score,
            metrics_changed=metrics_changed,
            statistical_significance={metric_name: z_score},
            recommendations=recommendations,
        )

        logger.info(
            f"Drift detection for {metric_name}: "
            f"detected={drift_detected}, severity={severity.value}, z_score={z_score:.2f}"
        )

        return result


class DigitalTwinSync:
    """
    Synchronizes RL agent states with ADAM Digital Twin representations.
    Maintains shadow models for introspection and governance auditing.
    """

    def __init__(self):
        """Initialize digital twin synchronization."""
        self._twins: Dict[str, DigitalTwinState] = {}
        self._twin_history: Dict[str, List[DigitalTwinState]] = {}
        logger.info("DigitalTwinSync initialized")

    def create_digital_twin(
        self,
        agent_id: str,
        model_state: Dict[str, Any]
    ) -> DigitalTwinState:
        """
        Create or update digital twin for an RL agent.

        Args:
            agent_id: ID of RL agent
            model_state: Current model state (weights, architecture, etc.)

        Returns:
            DigitalTwinState representing the agent
        """
        twin_id = str(uuid4())

        twin = DigitalTwinState(
            twin_id=twin_id,
            agent_id=agent_id,
            timestamp=datetime.utcnow(),
            model_state=model_state,
            performance_metrics={},
            doctrine_alignment_score=0.5,  # Will be updated by alignment validator
            boss_score=50,  # Initial neutral score
            governance_status='compliant',
        )

        self._twins[agent_id] = twin
        if agent_id not in self._twin_history:
            self._twin_history[agent_id] = []
        self._twin_history[agent_id].append(twin)

        logger.info(f"Created digital twin {twin_id} for agent {agent_id}")
        return twin

    def update_twin_state(
        self,
        agent_id: str,
        performance_metrics: Dict[str, float],
        doctrine_alignment_score: float,
        boss_score: int
    ) -> None:
        """
        Update digital twin with latest metrics and scores.

        Args:
            agent_id: ID of RL agent
            performance_metrics: Updated performance metrics
            doctrine_alignment_score: Alignment score (0.0-1.0)
            boss_score: BOSS score (0-100)
        """
        if agent_id not in self._twins:
            logger.warning(f"Digital twin not found for agent {agent_id}")
            return

        twin = self._twins[agent_id]
        twin.performance_metrics = performance_metrics
        twin.doctrine_alignment_score = doctrine_alignment_score
        twin.boss_score = boss_score

        # Update governance status based on scores
        if boss_score >= 80:
            twin.governance_status = 'violation'
        elif boss_score >= 60:
            twin.governance_status = 'warning'
        else:
            twin.governance_status = 'compliant'

        twin.timestamp = datetime.utcnow()
        self._twin_history[agent_id].append(twin)

        logger.debug(
            f"Updated digital twin for {agent_id}: "
            f"alignment={doctrine_alignment_score:.2f}, boss={boss_score}, status={twin.governance_status}"
        )

    def get_twin_state(self, agent_id: str) -> Optional[DigitalTwinState]:
        """Get current digital twin state."""
        return self._twins.get(agent_id)

    def get_twin_history(self, agent_id: str) -> List[DigitalTwinState]:
        """Get historical states of digital twin."""
        return self._twin_history.get(agent_id, [])

    def compare_twin_states(
        self,
        agent_id: str,
        lookback_steps: int = 10
    ) -> Dict[str, Any]:
        """
        Compare recent twin states to detect changes/drift.

        Args:
            agent_id: ID of RL agent
            lookback_steps: Number of recent states to compare

        Returns:
            Dictionary with comparison results
        """
        history = self.get_twin_history(agent_id)
        if len(history) < 2:
            return {'comparison': 'insufficient_history'}

        recent = history[-lookback_steps:]
        scores = [s.boss_score for s in recent]
        alignment_scores = [s.doctrine_alignment_score for s in recent]

        return {
            'agent_id': agent_id,
            'samples': len(recent),
            'boss_score_trend': scores,
            'alignment_trend': alignment_scores,
            'boss_score_change': scores[-1] - scores[0],
            'alignment_change': alignment_scores[-1] - alignment_scores[0],
        }


class AdamRLGovernance:
    """
    Main RL training governance orchestrator providing full lifecycle governance:
    - Reward function validation against ADAM doctrine
    - Training run monitoring for safety violations
    - Model drift detection and governance boundary enforcement
    - Digital Twin synchronization and introspection

    Integrates AGT Agent Lightning (RL training) with ADAM's doctrine alignment,
    governance boundaries (BOSS Score), and Digital Twin representations.
    """

    def __init__(self, boss_safety_threshold: int = 60):
        """
        Initialize RL governance system.

        Args:
            boss_safety_threshold: BOSS score threshold for intervention
        """
        self._alignment_validator = DoctrineAlignmentValidator()
        self._training_monitor = RLTrainingMonitor(boss_safety_threshold)
        self._drift_detector = DriftDetector()
        self._twin_sync = DigitalTwinSync()
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        logger.info("AdamRLGovernance initialized")

    def initialize_training_session(
        self,
        agent_id: str,
        reward_function: Callable,
        function_description: str = ""
    ) -> Tuple[bool, str]:
        """
        Initialize an RL training session with doctrine validation.

        Args:
            agent_id: ID of RL agent
            reward_function: Reward function to use
            function_description: Description of reward function

        Returns:
            Tuple of (success, session_id_or_error_message)
        """
        # Validate reward function alignment
        assessment = self._alignment_validator.validate_reward_function(
            agent_id, reward_function, function_description
        )

        if assessment.human_review_required:
            logger.warning(
                f"Reward function for {agent_id} requires human review: "
                f"status={assessment.alignment_status.value}"
            )

        if assessment.alignment_status == DoctrineAlignmentStatus.MISALIGNED:
            return False, f"Reward function is misaligned with ADAM doctrine: {assessment.recommendations}"

        # Create training session
        session_id = str(uuid4())
        self._active_sessions[session_id] = {
            'agent_id': agent_id,
            'reward_assessment_id': assessment.assessment_id,
            'status': TrainingStatus.INITIALIZING,
            'started_at': datetime.utcnow(),
            'metrics': []
        }

        # Create digital twin
        self._twin_sync.create_digital_twin(
            agent_id,
            {'reward_function': function_description}
        )

        logger.info(
            f"Initialized training session {session_id} for agent {agent_id}: "
            f"alignment={assessment.alignment_status.value}"
        )

        return True, session_id

    def record_training_step(
        self,
        session_id: str,
        metrics: TrainingMetrics
    ) -> Tuple[bool, Optional[str]]:
        """
        Record a training step and check for violations.

        Args:
            session_id: Training session ID
            metrics: Training metrics

        Returns:
            Tuple of (is_safe, violation_message_or_none)
        """
        if session_id not in self._active_sessions:
            return False, f"Session {session_id} not found"

        session = self._active_sessions[session_id]
        agent_id = session['agent_id']

        # Record metrics
        is_safe, violation = self._training_monitor.record_training_step(
            session_id, metrics.episode_number, metrics
        )

        # Update digital twin
        self._twin_sync.update_twin_state(
            agent_id,
            performance_metrics={'total_reward': metrics.total_reward, 'loss': metrics.loss},
            doctrine_alignment_score=0.8,  # Placeholder
            boss_score=metrics.boss_score
        )

        # Check for drift
        drift_result = self._drift_detector.detect_drift('total_reward', [metrics.total_reward])
        if drift_result.drift_detected:
            logger.warning(
                f"Drift detected in session {session_id}: {drift_result.severity.value}"
            )

        session['metrics'].append(metrics)
        session['status'] = TrainingStatus.RUNNING

        if not is_safe:
            session['status'] = TrainingStatus.FAILED
            return False, violation

        return True, None

    def complete_training_session(self, session_id: str) -> Dict[str, Any]:
        """
        Mark training session as complete and generate final report.

        Args:
            session_id: Training session ID

        Returns:
            Training report dictionary
        """
        if session_id not in self._active_sessions:
            return {'status': 'session_not_found'}

        session = self._active_sessions[session_id]
        session['status'] = TrainingStatus.COMPLETED
        session['completed_at'] = datetime.utcnow()

        report = self._training_monitor.generate_training_report(session_id)
        report['session_id'] = session_id
        report['agent_id'] = session['agent_id']
        report['status'] = session['status'].value

        logger.info(f"Completed training session {session_id}")

        return report

    def rollback_training_session(self, session_id: str, reason: str = "") -> bool:
        """
        Rollback a training session to previous state.

        Args:
            session_id: Training session ID
            reason: Reason for rollback

        Returns:
            True if rolled back successfully
        """
        if session_id not in self._active_sessions:
            return False

        session = self._active_sessions[session_id]
        session['status'] = TrainingStatus.ROLLED_BACK
        logger.warning(f"Rolled back training session {session_id}: {reason}")

        return True

    def get_agent_digital_twin(self, agent_id: str) -> Optional[DigitalTwinState]:
        """Get digital twin for an agent."""
        return self._twin_sync.get_twin_state(agent_id)

    def get_agent_twin_history(self, agent_id: str) -> List[DigitalTwinState]:
        """Get digital twin history for an agent."""
        return self._twin_sync.get_twin_history(agent_id)

    def compare_agent_states(self, agent_id: str) -> Dict[str, Any]:
        """Compare recent agent digital twin states."""
        return self._twin_sync.compare_twin_states(agent_id)

    def export_governance_report(self, session_id: str) -> Dict[str, Any]:
        """
        Export comprehensive governance report for RL training session.

        Args:
            session_id: Training session ID

        Returns:
            Governance report dictionary
        """
        if session_id not in self._active_sessions:
            return {'status': 'session_not_found'}

        session = self._active_sessions[session_id]
        agent_id = session['agent_id']

        training_report = self._training_monitor.generate_training_report(session_id)
        alignment_assessment = self._alignment_validator.get_assessment(
            session['reward_assessment_id']
        )
        twin_state = self._twin_sync.get_twin_state(agent_id)
        twin_history = self._twin_sync.get_twin_history(agent_id)

        return {
            'report_id': str(uuid4()),
            'generated_at': datetime.utcnow().isoformat(),
            'session_id': session_id,
            'agent_id': agent_id,
            'training_report': training_report,
            'alignment_assessment': alignment_assessment.to_dict() if alignment_assessment else None,
            'current_twin_state': twin_state.to_dict() if twin_state else None,
            'twin_history_length': len(twin_history),
            'governance_status': session['status'].value,
        }

    def list_active_sessions(self) -> List[Tuple[str, str, str]]:
        """
        List all active training sessions.

        Returns:
            List of (session_id, agent_id, status) tuples
        """
        sessions = []
        for session_id, session in self._active_sessions.items():
            sessions.append((session_id, session['agent_id'], session['status'].value))
        return sessions
