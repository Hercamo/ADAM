// BOSS Data Graph — seed data (frameworks, regulations, dimensions,
// priority tiers, escalation tiers, and ADAM default director roles).
//
// All statements are idempotent — they use MERGE and SET so running the
// loader repeatedly is safe. The contents mirror boss_core.frameworks,
// boss_core.tiers, and boss_core.router so a single source of truth can
// be materialized into a property graph for querying and audit.

// ---------------------------------------------------------------------------
// Frameworks (nist_csf_2, cvss, mitre_attack, ... 19 total)
// ---------------------------------------------------------------------------

MERGE (f:Framework {key: "nist_csf_2"})
  SET f.name = "NIST Cybersecurity Framework",
      f.publisher = "NIST",
      f.url = "https://www.nist.gov/cyberframework",
      f.version = "2.0";

MERGE (f:Framework {key: "cvss"})
  SET f.name = "Common Vulnerability Scoring System",
      f.publisher = "FIRST",
      f.url = "https://www.first.org/cvss/",
      f.version = "4.0";

MERGE (f:Framework {key: "mitre_attack"})
  SET f.name = "MITRE ATT&CK",
      f.publisher = "MITRE",
      f.url = "https://attack.mitre.org/";

MERGE (f:Framework {key: "nist_ai_rmf"})
  SET f.name = "NIST AI Risk Management Framework",
      f.publisher = "NIST",
      f.url = "https://www.nist.gov/itl/ai-risk-management-framework",
      f.version = "1.0";

MERGE (f:Framework {key: "iso_42001"})
  SET f.name = "ISO/IEC 42001 AI Management System",
      f.publisher = "ISO/IEC",
      f.url = "https://www.iso.org/standard/81230.html",
      f.version = "2023";

MERGE (f:Framework {key: "iso_31000"})
  SET f.name = "ISO 31000 Risk Management",
      f.publisher = "ISO",
      f.url = "https://www.iso.org/iso-31000-risk-management.html",
      f.version = "2018";

MERGE (f:Framework {key: "fair"})
  SET f.name = "Factor Analysis of Information Risk",
      f.publisher = "The Open Group",
      f.url = "https://www.opengroup.org/forum/security-forum-0/risk-analysis";

MERGE (f:Framework {key: "coso_erm"})
  SET f.name = "COSO Enterprise Risk Management",
      f.publisher = "COSO",
      f.url = "https://www.coso.org/Pages/erm.aspx",
      f.version = "2017";

MERGE (f:Framework {key: "seal"})
  SET f.name = "SEAL EU Cloud Sovereignty Framework",
      f.publisher = "European Cloud Industrial Alliance",
      f.url = "https://www.code-eu.org/seal";

MERGE (f:Framework {key: "reprisk"})
  SET f.name = "RepRisk Risk Index",
      f.publisher = "RepRisk AG",
      f.url = "https://www.reprisk.com/";

MERGE (f:Framework {key: "reptrak"})
  SET f.name = "RepTrak ESG Reputation Index",
      f.publisher = "The RepTrak Company",
      f.url = "https://www.reptrak.com/";

MERGE (f:Framework {key: "sasb"})
  SET f.name = "Sustainability Accounting Standards Board",
      f.publisher = "IFRS Foundation",
      f.url = "https://sasb.ifrs.org/";

MERGE (f:Framework {key: "eu_ai_act"})
  SET f.name = "EU AI Act (Regulation (EU) 2024/1689)",
      f.publisher = "European Union",
      f.url = "https://eur-lex.europa.eu/eli/reg/2024/1689/oj";

MERGE (f:Framework {key: "dora"})
  SET f.name = "Digital Operational Resilience Act (EU 2022/2554)",
      f.publisher = "European Union",
      f.url = "https://eur-lex.europa.eu/eli/reg/2022/2554/oj";

MERGE (f:Framework {key: "nis2"})
  SET f.name = "NIS2 Directive (EU 2022/2555)",
      f.publisher = "European Union",
      f.url = "https://eur-lex.europa.eu/eli/dir/2022/2555/oj";

MERGE (f:Framework {key: "gdpr"})
  SET f.name = "General Data Protection Regulation (EU 2016/679)",
      f.publisher = "European Union",
      f.url = "https://eur-lex.europa.eu/eli/reg/2016/679/oj";

MERGE (f:Framework {key: "us_eo_14110"})
  SET f.name = "US Executive Order 14110 on Safe, Secure, and Trustworthy AI",
      f.publisher = "The White House",
      f.url = "https://www.whitehouse.gov/briefing-room/presidential-actions/2023/10/30/";

MERGE (f:Framework {key: "uk_dsit_ai"})
  SET f.name = "UK DSIT / AI Safety Institute Guidance",
      f.publisher = "UK Government",
      f.url = "https://www.gov.uk/government/publications/ai-safety-institute";

MERGE (f:Framework {key: "adam_core"})
  SET f.name = "ADAM CORE Engine and Doctrine",
      f.publisher = "Michael Lamb (ADAM)",
      f.url = "https://github.com/Hercamo/ADAM";

// ---------------------------------------------------------------------------
// Regulations — specific instruments that compliance officers must cite
// ---------------------------------------------------------------------------

MERGE (r:Regulation {key: "eu_ai_act_art_5"})
  SET r.name = "EU AI Act Article 5 — Prohibited Practices",
      r.jurisdiction = "EU",
      r.instrument = "Regulation (EU) 2024/1689";

MERGE (r:Regulation {key: "eu_ai_act_art_6"})
  SET r.name = "EU AI Act Article 6 — High-Risk Classification",
      r.jurisdiction = "EU",
      r.instrument = "Regulation (EU) 2024/1689";

MERGE (r:Regulation {key: "gdpr_art_22"})
  SET r.name = "GDPR Article 22 — Automated Decision-Making",
      r.jurisdiction = "EU",
      r.instrument = "Regulation (EU) 2016/679";

MERGE (r:Regulation {key: "gdpr_art_35"})
  SET r.name = "GDPR Article 35 — Data Protection Impact Assessment",
      r.jurisdiction = "EU",
      r.instrument = "Regulation (EU) 2016/679";

MERGE (r:Regulation {key: "dora_art_6"})
  SET r.name = "DORA Article 6 — ICT Risk Management Framework",
      r.jurisdiction = "EU",
      r.instrument = "Regulation (EU) 2022/2554";

MERGE (r:Regulation {key: "nis2_art_21"})
  SET r.name = "NIS2 Article 21 — Cybersecurity Risk-Management Measures",
      r.jurisdiction = "EU",
      r.instrument = "Directive (EU) 2022/2555";

MERGE (r:Regulation {key: "us_eo_14110_sec_4"})
  SET r.name = "EO 14110 Section 4 — Safety and Security of AI",
      r.jurisdiction = "US",
      r.instrument = "Executive Order 14110";

// Link regulations to their umbrella frameworks
MATCH (reg:Regulation {key: "eu_ai_act_art_5"}), (fw:Framework {key: "eu_ai_act"})
MERGE (reg)-[:DERIVED_FROM]->(fw);
MATCH (reg:Regulation {key: "eu_ai_act_art_6"}), (fw:Framework {key: "eu_ai_act"})
MERGE (reg)-[:DERIVED_FROM]->(fw);
MATCH (reg:Regulation {key: "gdpr_art_22"}), (fw:Framework {key: "gdpr"})
MERGE (reg)-[:DERIVED_FROM]->(fw);
MATCH (reg:Regulation {key: "gdpr_art_35"}), (fw:Framework {key: "gdpr"})
MERGE (reg)-[:DERIVED_FROM]->(fw);
MATCH (reg:Regulation {key: "dora_art_6"}), (fw:Framework {key: "dora"})
MERGE (reg)-[:DERIVED_FROM]->(fw);
MATCH (reg:Regulation {key: "nis2_art_21"}), (fw:Framework {key: "nis2"})
MERGE (reg)-[:DERIVED_FROM]->(fw);
MATCH (reg:Regulation {key: "us_eo_14110_sec_4"}), (fw:Framework {key: "us_eo_14110"})
MERGE (reg)-[:DERIVED_FROM]->(fw);

// ---------------------------------------------------------------------------
// Priority Tiers (Top .. Very Low) with their canonical weights
// ---------------------------------------------------------------------------

MERGE (t:Tier {name: "Top"})        SET t.weight = 5.0, t.description = "Highest priority — only one dimension permitted.";
MERGE (t:Tier {name: "Very High"})  SET t.weight = 4.0, t.description = "Strategic priority — major directorate attention.";
MERGE (t:Tier {name: "High"})       SET t.weight = 3.0, t.description = "Significant priority — managed routinely.";
MERGE (t:Tier {name: "Medium"})     SET t.weight = 2.0, t.description = "Standard priority — baseline oversight.";
MERGE (t:Tier {name: "Low"})        SET t.weight = 1.0, t.description = "Monitored priority — periodic review.";
MERGE (t:Tier {name: "Very Low"})   SET t.weight = 0.5, t.description = "Background priority — policy review only.";

// ---------------------------------------------------------------------------
// BOSS Dimensions and their default ADAM tier assignments + attribution
// ---------------------------------------------------------------------------

MERGE (d:Dimension {key: "security"})
  SET d.name = "Security Impact",
      d.description = "Attack surface, control maturity, threat intel, AI-specific exposure.";
MATCH (d:Dimension {key: "security"}), (t:Tier {name: "Top"})
MERGE (d)-[:DEFAULT_TIER]->(t);
MATCH (d:Dimension {key: "security"}), (f:Framework)
  WHERE f.key IN ["nist_csf_2", "cvss", "mitre_attack"]
MERGE (d)-[:ATTRIBUTED_TO]->(f);

MERGE (d:Dimension {key: "sovereignty"})
  SET d.name = "Sovereignty Action",
      d.description = "SEAL EU cloud sovereignty and data-locality objectives.";
MATCH (d:Dimension {key: "sovereignty"}), (t:Tier {name: "Very High"})
MERGE (d)-[:DEFAULT_TIER]->(t);
MATCH (d:Dimension {key: "sovereignty"}), (f:Framework {key: "seal"})
MERGE (d)-[:ATTRIBUTED_TO]->(f);

MERGE (d:Dimension {key: "financial"})
  SET d.name = "Financial Exposure",
      d.description = "Monetary value, budget exposure, FAIR severity, cascading beta.";
MATCH (d:Dimension {key: "financial"}), (t:Tier {name: "Very High"})
MERGE (d)-[:DEFAULT_TIER]->(t);
MATCH (d:Dimension {key: "financial"}), (f:Framework)
  WHERE f.key IN ["fair", "coso_erm"]
MERGE (d)-[:ATTRIBUTED_TO]->(f);

MERGE (d:Dimension {key: "regulatory"})
  SET d.name = "Regulatory Impact",
      d.description = "EU AI Act class, GDPR, DORA, NIS2 applicability.";
MATCH (d:Dimension {key: "regulatory"}), (t:Tier {name: "High"})
MERGE (d)-[:DEFAULT_TIER]->(t);
MATCH (d:Dimension {key: "regulatory"}), (f:Framework)
  WHERE f.key IN ["eu_ai_act", "gdpr", "dora", "nis2"]
MERGE (d)-[:ATTRIBUTED_TO]->(f);

MERGE (d:Dimension {key: "reputational"})
  SET d.name = "Reputational Risk",
      d.description = "ESG severity, reach × amplification, stakeholder concern, novelty.";
MATCH (d:Dimension {key: "reputational"}), (t:Tier {name: "High"})
MERGE (d)-[:DEFAULT_TIER]->(t);
MATCH (d:Dimension {key: "reputational"}), (f:Framework)
  WHERE f.key IN ["reprisk", "reptrak", "sasb"]
MERGE (d)-[:ATTRIBUTED_TO]->(f);

MERGE (d:Dimension {key: "rights"})
  SET d.name = "Rights Certainty",
      d.description = "Authorization, ownership, entitlement, conflict index.";
MATCH (d:Dimension {key: "rights"}), (t:Tier {name: "High"})
MERGE (d)-[:DEFAULT_TIER]->(t);
MATCH (d:Dimension {key: "rights"}), (f:Framework)
  WHERE f.key IN ["iso_31000", "nist_ai_rmf"]
MERGE (d)-[:ATTRIBUTED_TO]->(f);

MERGE (d:Dimension {key: "doctrinal"})
  SET d.name = "Doctrinal Alignment",
      d.description = "Culture, objective, rules violations, expectation conformity.";
MATCH (d:Dimension {key: "doctrinal"}), (t:Tier {name: "Medium"})
MERGE (d)-[:DEFAULT_TIER]->(t);
MATCH (d:Dimension {key: "doctrinal"}), (f:Framework)
  WHERE f.key IN ["coso_erm", "iso_42001", "adam_core"]
MERGE (d)-[:ATTRIBUTED_TO]->(f);

// ---------------------------------------------------------------------------
// Escalation Tiers (SOAP .. OHSHAT) with bounds and SLA
// ---------------------------------------------------------------------------

MERGE (e:EscalationTier {name: "SOAP"})
  SET e.lower = 0.0, e.upper = 10.0, e.sla_minutes = 0,
      e.description = "Safe & Optimum Autonomous Performance. Execute.";

MERGE (e:EscalationTier {name: "MODERATE"})
  SET e.lower = 10.0, e.upper = 30.0, e.sla_minutes = 0,
      e.description = "Constrained execution with enhanced logging.";

MERGE (e:EscalationTier {name: "ELEVATED"})
  SET e.lower = 30.0, e.upper = 50.0, e.sla_minutes = 60,
      e.description = "Exception likely; Domain Governor review.";

MERGE (e:EscalationTier {name: "HIGH"})
  SET e.lower = 50.0, e.upper = 75.0, e.sla_minutes = 240,
      e.description = "Director approval required within 4 hours.";

MERGE (e:EscalationTier {name: "OHSHAT"})
  SET e.lower = 75.0, e.upper = 100.0, e.sla_minutes = 15,
      e.description = "Operational Hell, Send Humans Act Today — CEO + all directors; safe-mode engaged.";

// ---------------------------------------------------------------------------
// 5-Director Constitution (default ADAM roster + optional CPO/CTO)
// ---------------------------------------------------------------------------

MERGE (d:Director {id: "ceo"})
  SET d.title = "Chief Executive Officer",
      d.scope = "Ultimate accountability; OHSHAT approvals.";

MERGE (d:Director {id: "cfo"})
  SET d.title = "Chief Financial Officer",
      d.scope = "Financial exposure and budget governance.";

MERGE (d:Director {id: "legal_director"})
  SET d.title = "Legal Director / General Counsel",
      d.scope = "Regulatory and rights-certainty oversight.";

MERGE (d:Director {id: "market_director"})
  SET d.title = "Market / Chief Marketing Officer",
      d.scope = "Reputational risk and stakeholder trust.";

MERGE (d:Director {id: "ciso"})
  SET d.title = "Chief Information Security Officer",
      d.scope = "Security impact and sovereignty enforcement.";

MERGE (d:Director {id: "cpo"})
  SET d.title = "Chief Product Officer (optional)",
      d.scope = "Doctrinal alignment and product-doctrine conflict.";

MERGE (d:Director {id: "cto"})
  SET d.title = "Chief Technology Officer (optional)",
      d.scope = "Technical feasibility and architectural alignment.";

// Director → Dimension accountability
MATCH (dir:Director {id: "ciso"}), (dim:Dimension {key: "security"})
MERGE (dir)-[:ACCOUNTABLE_FOR]->(dim);
MATCH (dir:Director {id: "ciso"}), (dim:Dimension {key: "sovereignty"})
MERGE (dir)-[:ACCOUNTABLE_FOR]->(dim);
MATCH (dir:Director {id: "cfo"}), (dim:Dimension {key: "financial"})
MERGE (dir)-[:ACCOUNTABLE_FOR]->(dim);
MATCH (dir:Director {id: "legal_director"}), (dim:Dimension {key: "regulatory"})
MERGE (dir)-[:ACCOUNTABLE_FOR]->(dim);
MATCH (dir:Director {id: "legal_director"}), (dim:Dimension {key: "rights"})
MERGE (dir)-[:ACCOUNTABLE_FOR]->(dim);
MATCH (dir:Director {id: "market_director"}), (dim:Dimension {key: "reputational"})
MERGE (dir)-[:ACCOUNTABLE_FOR]->(dim);
MATCH (dir:Director {id: "ceo"}), (dim:Dimension {key: "doctrinal"})
MERGE (dir)-[:ACCOUNTABLE_FOR]->(dim);
