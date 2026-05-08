# ADAMPLUS Agent Definitions (v0.3, Day-1 PQC)

ADAMPLUS = extensions to the canonical 81-agent mesh required by real-world
enterprise flows. ADAMPLUS agents inherit ADAM doctrine and flow through
the same six-stage pipeline; they are NOT an alternate governance model.

34 cards in 6 clusters:

Financial Operations Extension (12):
  ap-vendor-invoice, ap-payment-run, ap-3way-match,
  ar-invoice, ar-collections, ar-credit, ar-revrec,
  fin-treasury, fin-fx, fin-tax-calc, fin-tax-file, fin-gl

HR Extension (workforce <= 50, mostly outsourced) (7):
  hr-onboarding, hr-offboarding, hr-payroll, hr-benefits,
  hr-time, hr-performance, hr-compliance

CRM Extension (5):
  crm-360, crm-lead, crm-pipeline, crm-success, crm-cases

Operations Extension - NetStreamX Media (3):
  ops-content-catalog, ops-streaming, ops-subscription

Operations Extension - Industry Verticals (3):
  ops-mes (Manufacturing), ops-ehr (Healthcare),
  ops-trading (Financial Services)

ITSM (2) + Procurement (2):
  itsm-incident, itsm-change, proc-sourcing, proc-po

Each card includes Real-World Flow Walkthrough (Section 3), Base-mesh
Anchors (in identity), Day-1 PQC posture, Doctrine Cross-Refs, and
Section 20 "Adapters Used" listing canonical adapter IDs.

QA: 34/34, 0 failures across qa_all.py + qa_360.py (cross-mesh).
