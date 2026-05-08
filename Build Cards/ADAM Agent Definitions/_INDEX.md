# ADAM Agent Definitions — 81-Agent Mesh (v0.3, Day-1 PQC)

81 cards covering the canonical 81-agent mesh exactly as registered in
`deployment/NetStreamX/agents/agent-registry.json`.

Each card is a 2-4 page production specification and now includes:
  * Day-1 PQC posture (Ed25519 + ML-DSA-65 + ML-KEM-768; SLH-DSA long-term
    anchor) - dual-signature is enforced from the very first call.
  * Doctrine Cross-Refs row in Section 1 citing every supporting v0.3
    document.
  * Section 19 "Adapters Used" — explicit canonical adapter IDs that the
    agent depends on (or "None - internal-only agent").
  * Section 20 "Acceptance Criteria (DoD)".

Class breakdown:
  Human Interface (3) + Domain Governors (5) + Orchestration (4) +
  Corporate Work Groups (39) + AI-Centric (23) + Digital Twins (4) +
  Meta-Governance (3) = 81.

QA: structural qa_all.py + cross-mesh qa_360.py — 0 failures, 0 warnings
across:
  - Inventory completeness
  - Bidirectional adapter↔agent symmetry
  - Schema awareness for every adapter
  - Doctrine alignment (BOSS dims, mandates M1-M6, RGI-01..05, 5+2
    Director Constitution)
  - 10 real-world flow traces walked end-to-end through the mesh
  - All 20 canonical sections present
  - Day-1 PQC enforced; forward-dated PQC phrases forbidden

Companion deliverables:
  - ../ADAMPLUS Agent Definitions/  (34 extension agents for AR/AP, HR,
    CRM, Operations verticals, ITSM, Procurement)
  - ../ADAM Integration Adapters/   (20 adapter cards: Salesforce, SAP
    S/4HANA, Workday, Stripe, Adyen, Plaid, SWIFT/ISO 20022, HubSpot,
    Dynamics, Oracle ERP, NetStreamX CMS, HL7/FHIR, OPC-UA, BambooHR,
    ServiceNow, Coupa/Ariba, Okta, FIX Protocol, Twilio+SendGrid, Zendesk)
