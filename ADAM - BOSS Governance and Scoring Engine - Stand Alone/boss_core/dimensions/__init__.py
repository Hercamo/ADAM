"""Dimension-specific scorers for BOSS v3.2.

Each scorer takes a free-form input dict (validated at the dimension
level) and returns a :class:`DimensionScore` in the 0-100 risk scale.
Sub-component mathematics match the sections defined in
``ADAM — BOSS Score Formulas v3.2``.
"""

from boss_core.dimensions.base import Scorer, register_scorer, scorer_for
from boss_core.dimensions.doctrinal import DoctrinalAlignmentScorer
from boss_core.dimensions.financial import FinancialExposureScorer
from boss_core.dimensions.regulatory import RegulatoryImpactScorer
from boss_core.dimensions.reputational import ReputationalRiskScorer
from boss_core.dimensions.rights import RightsCertaintyScorer
from boss_core.dimensions.security import SecurityImpactScorer
from boss_core.dimensions.sovereignty import SovereigntyActionScorer

__all__ = [
    "DoctrinalAlignmentScorer",
    "FinancialExposureScorer",
    "RegulatoryImpactScorer",
    "ReputationalRiskScorer",
    "RightsCertaintyScorer",
    "Scorer",
    "SecurityImpactScorer",
    "SovereigntyActionScorer",
    "register_scorer",
    "scorer_for",
]
