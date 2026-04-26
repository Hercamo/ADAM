"""Sovereignty Action scorer — SEAL EU Cloud Sovereignty Framework.

The SEAL framework lists eight objectives (SOV-1 through SOV-8) each
scored on a 0-4 maturity scale. When an operator provides an explicit
``seal_objectives`` mapping the scorer uses that detailed view. When
only high-level operational signals are provided — the normal path for
agent-driven intents — the scorer infers per-objective maturity from
``data_residency_compliant``, ``cross_border_transfers``, and
``lawful_basis_documented``.

A "critical violation floor" of 60 applies when any fundamental SEAL
objective (SOV-1..SOV-4) is at maturity 0 or 1; see BOSS Formulas v3.2,
Section 5.2.
"""

from __future__ import annotations

from typing import Any

from boss_core.dimensions.base import Scorer, register_scorer
from boss_core.schemas import DimensionScore, SubComponentScore
from boss_core.tiers import DimensionKey

SEAL_OBJECTIVES: tuple[tuple[str, str], ...] = (
    ("SOV-1", "Data Residency"),
    ("SOV-2", "Operational Control"),
    ("SOV-3", "Provider Independence"),
    ("SOV-4", "Cryptographic Sovereignty"),
    ("SOV-5", "Personnel Sovereignty"),
    ("SOV-6", "Regulatory Jurisdiction"),
    ("SOV-7", "Supply-Chain Transparency"),
    ("SOV-8", "Reversibility"),
)
FUNDAMENTAL_OBJECTIVES = frozenset({"SOV-1", "SOV-2", "SOV-3", "SOV-4"})


def _infer_maturities(payload: dict[str, Any]) -> dict[str, int]:
    """Map operational fixture signals to SEAL objective maturities.

    Every objective starts at maturity 3 (managed); residency and
    lawful-basis issues drag the matching objectives down, while large
    cross-border transfer counts drag the jurisdictional objectives.
    """
    data_residency = bool(payload.get("data_residency_compliant", True))
    lawful_basis = bool(payload.get("lawful_basis_documented", True))
    transfers = max(0, int(payload.get("cross_border_transfers", 0)))

    maturities: dict[str, int] = {oid: 3 for oid, _ in SEAL_OBJECTIVES}
    if not data_residency:
        maturities["SOV-1"] = 0  # fundamental — triggers the floor
    if not lawful_basis:
        maturities["SOV-6"] = 1
    # Cross-border pressure degrades operational control and reversibility.
    if transfers >= 5:
        maturities["SOV-2"] = 1
        maturities["SOV-6"] = min(maturities["SOV-6"], 1)
        maturities["SOV-8"] = 1
    elif transfers >= 3:
        maturities["SOV-2"] = 2
        maturities["SOV-6"] = min(maturities["SOV-6"], 2)
        maturities["SOV-8"] = 2
    elif transfers >= 1:
        maturities["SOV-6"] = min(maturities["SOV-6"], 2)
    return maturities


class SovereigntyActionScorer(Scorer):
    """Sovereignty risk derived from SEAL objective maturity."""

    dimension = DimensionKey.SOVEREIGNTY

    def score(self, payload: dict[str, Any]) -> DimensionScore:
        seal_raw: dict[str, Any] = dict(payload.get("seal_objectives", {}) or {})
        if seal_raw:
            maturities = {
                oid: max(0, min(4, int(seal_raw.get(oid, 2)))) for oid, _ in SEAL_OBJECTIVES
            }
        else:
            maturities = _infer_maturities(payload)

        per_obj = 100.0 / len(SEAL_OBJECTIVES)
        subs: list[SubComponentScore] = []
        for oid, name in SEAL_OBJECTIVES:
            mat = maturities[oid]
            risk_contrib = per_obj * ((4 - mat) / 4.0)
            subs.append(
                SubComponentScore(
                    name=f"{oid} {name}",
                    value=round(risk_contrib, 4),
                    max_value=per_obj,
                    rationale=f"Maturity level {mat} / 4.",
                )
            )

        base = sum(sc.value for sc in subs)

        floor_triggered = any(maturities[oid] <= 1 for oid in FUNDAMENTAL_OBJECTIVES)
        raw = max(base, 60.0) if floor_triggered else base
        notes: str | None = None
        if floor_triggered:
            notes = (
                "Critical violation floor applied: a fundamental SEAL "
                "objective is at maturity <= 1, forcing the risk score to "
                "at least 60."
            )
        return DimensionScore(
            dimension=self.dimension,
            raw_score=round(min(raw, 100.0), 4),
            sub_components=subs,
            frameworks=list(self.framework_keys()),
            notes=notes,
        )


register_scorer(SovereigntyActionScorer())
