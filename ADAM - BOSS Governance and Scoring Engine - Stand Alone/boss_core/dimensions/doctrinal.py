"""Doctrinal Alignment scorer — COSO ERM Governance + ADAM CORE Engine.

Sub-components (BOSS Formulas v3.2, Section 5.7):
    A. Culture Alignment       — 0 to 25  (inverted)
    B. Objective Alignment     — 0 to 25  (inverted)
    C. Rules Compliance        — 0 to 30
    D. Expectations Conformity — 0 to 20  (inverted)

Canonical input fields (operational):
    * ``doctrine_alignment`` — float in ``[0, 1]`` for overall alignment
      with the organisation's doctrine (culture + values).
    * ``mission_fit`` — float in ``[0, 1]`` for alignment with the
      declared business objective of the agent mesh.
    * ``conflicts_with_declared_constraints`` — bool. ``True`` means the
      intent directly violates a hard policy constraint.
    * ``rules_violations`` — optional integer count of active rule
      violations. If omitted, ``conflicts_with_declared_constraints``
      drives the ``C`` sub-component.
    * ``expectation_conformity`` — optional ``[0, 1]`` override for the
      ``D`` sub-component; otherwise inferred from alignment signals.
"""

from __future__ import annotations

from typing import Any

from boss_core.dimensions.base import Scorer, register_scorer
from boss_core.schemas import DimensionScore, SubComponentScore
from boss_core.tiers import DimensionKey


class DoctrinalAlignmentScorer(Scorer):
    """Doctrinal alignment risk — low alignment drives the score upward."""

    dimension = DimensionKey.DOCTRINAL

    def score(self, payload: dict[str, Any]) -> DimensionScore:
        doctrine_alignment = self._cap(float(payload.get("doctrine_alignment", 1.0)), 1.0)
        mission_fit = self._cap(float(payload.get("mission_fit", 1.0)), 1.0)
        conflicts = bool(payload.get("conflicts_with_declared_constraints", False))

        rules_violations_override = payload.get("rules_violations")
        expectation_override = payload.get("expectation_conformity")

        a_value = self._cap((1.0 - doctrine_alignment) * 25.0, 25.0)
        b_value = self._cap((1.0 - mission_fit) * 25.0, 25.0)

        if rules_violations_override is not None:
            c_value = self._cap(int(rules_violations_override) * 10.0, 30.0)
            rules_rationale = f"{int(rules_violations_override)} active rule violations."
        elif conflicts:
            c_value = 30.0
            rules_rationale = (
                "Intent conflicts with declared constraints; rules sub-component pegged to max."
            )
        else:
            c_value = 0.0
            rules_rationale = "No rule violations declared."

        if expectation_override is not None:
            conformity = self._cap(float(expectation_override), 1.0)
        else:
            conformity = (doctrine_alignment + mission_fit) / 2.0
        d_value = self._cap((1.0 - conformity) * 20.0, 20.0)

        subs = [
            SubComponentScore(
                name="Culture / Doctrine Alignment (inverted)",
                value=round(a_value, 4),
                max_value=25.0,
                rationale=f"Doctrine alignment {doctrine_alignment:.2f}.",
            ),
            SubComponentScore(
                name="Objective / Mission Alignment (inverted)",
                value=round(b_value, 4),
                max_value=25.0,
                rationale=f"Mission fit {mission_fit:.2f}.",
            ),
            SubComponentScore(
                name="Rules Compliance",
                value=round(c_value, 4),
                max_value=30.0,
                rationale=rules_rationale,
            ),
            SubComponentScore(
                name="Expectations Conformity (inverted)",
                value=round(d_value, 4),
                max_value=20.0,
                rationale=f"Inferred conformity {conformity:.2f}.",
            ),
        ]
        return self._assemble(subs)


register_scorer(DoctrinalAlignmentScorer())
