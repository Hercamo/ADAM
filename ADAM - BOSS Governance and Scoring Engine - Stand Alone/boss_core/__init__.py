"""BOSS AI Governance & Risk Engine — core scoring library.

Business Operations Sovereignty Score (BOSS) is a multi-dimensional risk
scoring and governance model extracted from the ADAM — Autonomy Doctrine &
Architecture Model. This package provides a self-contained scoring engine,
independent of any specific agent framework, suitable for embedding in or
fronting any AI agent workflow.

Seven independent dimensions are evaluated per proposed action:

    Security Impact     (NIST CSF 2.0 + CVSS v4.0 + MITRE ATT&CK)
    Sovereignty Action  (SEAL EU Cloud Sovereignty + Eurotechguide)
    Financial Exposure  (FAIR + COSO ERM)
    Regulatory Impact   (EU AI Act + GRC Compliance Scoring)
    Reputational Risk   (RepRisk RRI + RepTrak ESG)
    Rights Certainty    (ISO 31000 + NIST AI RMF)
    Doctrinal Alignment (COSO ERM Governance + ADAM CORE Engine)

Each dimension is scored 0-100 on a risk scale (higher = more risky) and
combined with director-assigned Priority Tier weights into a composite
0-100 that routes every action to one of five escalation tiers
(SOAP, MODERATE, ELEVATED, HIGH, OHSHAT).
"""

from boss_core.version import __version__

__all__ = ["__version__"]
