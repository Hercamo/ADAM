"""Framework and regulatory attribution catalog.

Every BOSS dimension draws from internationally recognized, publicly
documented frameworks. This module keeps the attribution explicit so
that every score returned by the engine carries a defensible provenance
chain back to the published methodology that informed it.

Regulations explicitly supported
--------------------------------
* EU AI Act (Regulation (EU) 2024/1689)
* Digital Operational Resilience Act (DORA, Regulation (EU) 2022/2554)
* NIS2 Directive ((EU) 2022/2555)
* GDPR (Regulation (EU) 2016/679)
* NIST Cybersecurity Framework 2.0
* NIST AI Risk Management Framework (AI 100-1)
* ISO/IEC 42001 (AI Management System)
* ISO 31000 (Risk Management)
* CVSS v4.0 (FIRST)
* MITRE ATT&CK (Enterprise and AI matrices)
* FAIR (Factor Analysis of Information Risk)
* COSO ERM 2017
* SEAL — EU Cloud Sovereignty Framework
* RepRisk RRI, RepTrak, SASB
* US Executive Order 14110 (for deployers operating in the US)
* UK DSIT AI Safety Framework / AI Safety Institute Guidance
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from boss_core.tiers import DimensionKey


@dataclass(frozen=True)
class Framework:
    """Immutable descriptor for a framework or regulation used in scoring."""

    key: str
    name: str
    publisher: str
    url: str
    version: str | None = None


# ---------------------------------------------------------------------------
# Framework catalog
# ---------------------------------------------------------------------------

FRAMEWORKS: Final[tuple[Framework, ...]] = (
    Framework(
        key="nist_csf_2",
        name="NIST Cybersecurity Framework",
        publisher="NIST",
        url="https://www.nist.gov/cyberframework",
        version="2.0",
    ),
    Framework(
        key="cvss",
        name="Common Vulnerability Scoring System",
        publisher="FIRST",
        url="https://www.first.org/cvss/",
        version="4.0",
    ),
    Framework(
        key="mitre_attack",
        name="MITRE ATT&CK",
        publisher="MITRE",
        url="https://attack.mitre.org/",
    ),
    Framework(
        key="nist_ai_rmf",
        name="NIST AI Risk Management Framework",
        publisher="NIST",
        url="https://www.nist.gov/itl/ai-risk-management-framework",
        version="1.0",
    ),
    Framework(
        key="iso_42001",
        name="ISO/IEC 42001 AI Management System",
        publisher="ISO/IEC",
        url="https://www.iso.org/standard/81230.html",
        version="2023",
    ),
    Framework(
        key="iso_31000",
        name="ISO 31000 Risk Management",
        publisher="ISO",
        url="https://www.iso.org/iso-31000-risk-management.html",
        version="2018",
    ),
    Framework(
        key="fair",
        name="Factor Analysis of Information Risk",
        publisher="The Open Group",
        url="https://www.opengroup.org/forum/security-forum-0/risk-analysis",
    ),
    Framework(
        key="coso_erm",
        name="COSO Enterprise Risk Management",
        publisher="COSO",
        url="https://www.coso.org/Pages/erm.aspx",
        version="2017",
    ),
    Framework(
        key="seal",
        name="SEAL EU Cloud Sovereignty Framework",
        publisher="European Cloud Industrial Alliance",
        url="https://www.code-eu.org/seal",
    ),
    Framework(
        key="reprisk",
        name="RepRisk Risk Index",
        publisher="RepRisk AG",
        url="https://www.reprisk.com/",
    ),
    Framework(
        key="reptrak",
        name="RepTrak ESG Reputation Index",
        publisher="The RepTrak Company",
        url="https://www.reptrak.com/",
    ),
    Framework(
        key="sasb",
        name="Sustainability Accounting Standards Board",
        publisher="IFRS Foundation",
        url="https://sasb.ifrs.org/",
    ),
    Framework(
        key="eu_ai_act",
        name="EU AI Act (Regulation (EU) 2024/1689)",
        publisher="European Union",
        url="https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
    ),
    Framework(
        key="dora",
        name="Digital Operational Resilience Act (EU 2022/2554)",
        publisher="European Union",
        url="https://eur-lex.europa.eu/eli/reg/2022/2554/oj",
    ),
    Framework(
        key="nis2",
        name="NIS2 Directive (EU 2022/2555)",
        publisher="European Union",
        url="https://eur-lex.europa.eu/eli/dir/2022/2555/oj",
    ),
    Framework(
        key="gdpr",
        name="General Data Protection Regulation (EU 2016/679)",
        publisher="European Union",
        url="https://eur-lex.europa.eu/eli/reg/2016/679/oj",
    ),
    Framework(
        key="us_eo_14110",
        name="US Executive Order 14110 on Safe, Secure, and Trustworthy AI",
        publisher="The White House",
        url="https://www.whitehouse.gov/briefing-room/presidential-actions/2023/10/30/",
    ),
    Framework(
        key="uk_dsit_ai",
        name="UK DSIT / AI Safety Institute Guidance",
        publisher="UK Government",
        url="https://www.gov.uk/government/publications/ai-safety-institute",
    ),
    Framework(
        key="adam_core",
        name="ADAM CORE Engine and Doctrine",
        publisher="Michael Lamb (ADAM)",
        url="https://github.com/Hercamo/ADAM",
    ),
)

FRAMEWORK_INDEX: Final[dict[str, Framework]] = {f.key: f for f in FRAMEWORKS}


# ---------------------------------------------------------------------------
# Attribution per BOSS dimension (v3.2 Appendix A)
# ---------------------------------------------------------------------------

DIMENSION_FRAMEWORKS: Final[dict[DimensionKey, tuple[str, ...]]] = {
    DimensionKey.SECURITY: ("nist_csf_2", "cvss", "mitre_attack"),
    DimensionKey.SOVEREIGNTY: ("seal",),
    DimensionKey.FINANCIAL: ("fair", "coso_erm"),
    DimensionKey.REGULATORY: ("eu_ai_act", "gdpr", "dora", "nis2"),
    DimensionKey.REPUTATIONAL: ("reprisk", "reptrak", "sasb"),
    DimensionKey.RIGHTS: ("iso_31000", "nist_ai_rmf"),
    DimensionKey.DOCTRINAL: ("coso_erm", "iso_42001", "adam_core"),
}


def attribution_for(dimension: DimensionKey) -> tuple[Framework, ...]:
    """Return the canonical framework attribution tuple for a dimension."""
    return tuple(FRAMEWORK_INDEX[k] for k in DIMENSION_FRAMEWORKS[dimension])
