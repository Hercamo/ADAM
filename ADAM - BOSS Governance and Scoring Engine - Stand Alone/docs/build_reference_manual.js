/**
 * BOSS Engine Reference Manual v3.2 (generated)
 *
 * Produces BOSS-Engine-Reference-Manual.docx covering:
 *   1  Executive summary
 *   2  ADAM context & BOSS positioning
 *   3  Architecture
 *   4  Dimension catalog
 *   5  Priority Tier weighting & composite formula
 *   6  SOAP..OHSHAT escalation router
 *   7  Exception packets, decision receipts, Flight Recorder
 *   8  API contract (every endpoint)
 *   9  Data graph (frameworks x dimensions)
 *  10  Governance alignment (EU AI Act, DORA, NIS2, GDPR, ISO 42001,
 *      NIST CSF 2.0, NIST AI RMF, OECD, Singapore MAS FEAT)
 *  11  Deployment (Docker, Helm, raw K8s)
 *  12  Adapter integration guide (LangGraph, OpenAI Agents, AI Foundry,
 *      CrewAI, generic)
 *  13  Worked examples (NetStreamX: SOAP, ELEVATED, OHSHAT)
 *  14  Security, observability, operations
 *  15  Appendix A: full REST reference
 *  16  Appendix B: glossary & acronym list
 */

const fs = require("fs");
const {
  Document,
  Packer,
  Paragraph,
  TextRun,
  Table,
  TableRow,
  TableCell,
  Header,
  Footer,
  AlignmentType,
  LevelFormat,
  HeadingLevel,
  BorderStyle,
  WidthType,
  ShadingType,
  TableOfContents,
  PageNumber,
  PageBreak,
  PageOrientation,
  TabStopType,
  TabStopPosition,
  ExternalHyperlink,
} = require("docx");

// ---------------------------------------------------------------------------
// Style helpers
// ---------------------------------------------------------------------------

const FONT = "Arial";
const MONO = "Consolas";

const BODY_SIZE = 22; // 11pt
const SMALL_SIZE = 20; // 10pt
const CODE_SIZE = 18; // 9pt

const BRAND = "1F3864"; // dark blue
const ACCENT = "2E75B6"; // mid blue
const MUTED = "595959"; // slate

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text, bold: true, color: BRAND, font: FONT })],
    spacing: { before: 360, after: 200 },
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text, bold: true, color: BRAND, font: FONT })],
    spacing: { before: 280, after: 160 },
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    children: [new TextRun({ text, bold: true, color: ACCENT, font: FONT })],
    spacing: { before: 220, after: 120 },
  });
}

function p(...runs) {
  return new Paragraph({
    children: runs.map((r) =>
      typeof r === "string"
        ? new TextRun({ text: r, font: FONT, size: BODY_SIZE })
        : r,
    ),
    spacing: { after: 140 },
  });
}

function t(text, opts = {}) {
  return new TextRun({ text, font: FONT, size: BODY_SIZE, ...opts });
}

function strong(text) {
  return new TextRun({ text, font: FONT, size: BODY_SIZE, bold: true });
}

function em(text) {
  return new TextRun({ text, font: FONT, size: BODY_SIZE, italics: true });
}

function code(text) {
  return new TextRun({ text, font: MONO, size: CODE_SIZE });
}

function bullet(runs) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    children: (Array.isArray(runs) ? runs : [runs]).map((r) =>
      typeof r === "string"
        ? new TextRun({ text: r, font: FONT, size: BODY_SIZE })
        : r,
    ),
    spacing: { after: 80 },
  });
}

function numbered(runs) {
  return new Paragraph({
    numbering: { reference: "numbers", level: 0 },
    children: (Array.isArray(runs) ? runs : [runs]).map((r) =>
      typeof r === "string"
        ? new TextRun({ text: r, font: FONT, size: BODY_SIZE })
        : r,
    ),
    spacing: { after: 80 },
  });
}

function codeBlock(text) {
  const lines = text.split("\n");
  return lines.map(
    (line) =>
      new Paragraph({
        shading: { type: ShadingType.CLEAR, fill: "F2F2F2" },
        spacing: { after: 0 },
        children: [
          new TextRun({
            text: line === "" ? " " : line,
            font: MONO,
            size: CODE_SIZE,
          }),
        ],
      }),
  );
}

function callout(title, body) {
  const border = {
    style: BorderStyle.SINGLE,
    size: 8,
    color: ACCENT,
  };
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [9360],
    rows: [
      new TableRow({
        children: [
          new TableCell({
            width: { size: 9360, type: WidthType.DXA },
            shading: { type: ShadingType.CLEAR, fill: "EAF2FA" },
            borders: {
              top: border,
              bottom: border,
              left: border,
              right: border,
            },
            margins: { top: 120, bottom: 120, left: 180, right: 180 },
            children: [
              new Paragraph({
                children: [
                  new TextRun({
                    text: title,
                    bold: true,
                    color: BRAND,
                    font: FONT,
                    size: BODY_SIZE,
                  }),
                ],
                spacing: { after: 80 },
              }),
              new Paragraph({
                children: [
                  new TextRun({ text: body, font: FONT, size: BODY_SIZE }),
                ],
              }),
            ],
          }),
        ],
      }),
    ],
  });
}

// ---------------------------------------------------------------------------
// Table helpers
// ---------------------------------------------------------------------------

const CELL_BORDER = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const CELL_BORDERS = {
  top: CELL_BORDER,
  bottom: CELL_BORDER,
  left: CELL_BORDER,
  right: CELL_BORDER,
};

function tableHeaderCell(text, width) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: BRAND },
    borders: CELL_BORDERS,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [
      new Paragraph({
        children: [
          new TextRun({
            text,
            bold: true,
            color: "FFFFFF",
            font: FONT,
            size: SMALL_SIZE,
          }),
        ],
      }),
    ],
  });
}

function tableCell(text, width, opts = {}) {
  const runs = Array.isArray(text)
    ? text
    : [new TextRun({ text: String(text), font: FONT, size: SMALL_SIZE })];
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: opts.fill
      ? { type: ShadingType.CLEAR, fill: opts.fill }
      : undefined,
    borders: CELL_BORDERS,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({ children: runs })],
  });
}

function buildTable(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map((h, i) => tableHeaderCell(h, widths[i])),
      }),
      ...rows.map(
        (row) =>
          new TableRow({
            children: row.map((cell, i) => {
              const fill = i === 0 ? "F7F9FC" : undefined;
              return tableCell(cell, widths[i], { fill });
            }),
          }),
      ),
    ],
  });
}

// ---------------------------------------------------------------------------
// Content builders
// ---------------------------------------------------------------------------

function cover() {
  return [
    new Paragraph({
      spacing: { before: 3600, after: 200 },
      alignment: AlignmentType.CENTER,
      children: [
        new TextRun({
          text: "BOSS",
          bold: true,
          color: BRAND,
          font: FONT,
          size: 96,
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [
        new TextRun({
          text: "AI Governance & Risk Engine",
          color: BRAND,
          font: FONT,
          size: 40,
        }),
      ],
      spacing: { after: 200 },
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [
        new TextRun({
          text: "Reference Manual",
          bold: true,
          color: MUTED,
          font: FONT,
          size: 32,
        }),
      ],
      spacing: { after: 120 },
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [
        new TextRun({
          text: "ADAM Book v0.2  |  BOSS Score v3.2 — Priority Tier Edition",
          color: MUTED,
          font: FONT,
          size: 24,
        }),
      ],
      spacing: { after: 2400 },
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [
        new TextRun({
          text: "An ADAM (Autonomy Doctrine & Architecture Model) component",
          italics: true,
          color: MUTED,
          font: FONT,
          size: 22,
        }),
      ],
      spacing: { after: 200 },
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [
        new TextRun({
          text: "Engineered for EU AI Act, DORA, NIS2, GDPR, ISO/IEC 42001, NIST CSF 2.0 and NIST AI RMF",
          color: MUTED,
          font: FONT,
          size: 20,
        }),
      ],
      spacing: { after: 2000 },
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [
        new TextRun({
          text: "Apache License 2.0",
          color: MUTED,
          font: FONT,
          size: 22,
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [
        new TextRun({
          text: "April 2026",
          color: MUTED,
          font: FONT,
          size: 22,
        }),
      ],
    }),
    new Paragraph({ children: [new PageBreak()] }),
  ];
}

function tocSection() {
  return [
    h1("Contents"),
    new TableOfContents("Table of Contents", {
      hyperlink: true,
      headingStyleRange: "1-3",
    }),
    new Paragraph({ children: [new PageBreak()] }),
  ];
}

// ---------------------------------------------------------------------------
// Section 1 - Executive summary
// ---------------------------------------------------------------------------

function executiveSummary() {
  return [
    h1("1. Executive summary"),
    p(
      "The BOSS Engine is the real-time AI governance and risk scoring service at the heart of the ADAM (Autonomy Doctrine & Architecture Model). Every proposed agent action — whether it originates in a LangGraph workflow, an OpenAI Agents tool-call, an Azure AI Foundry connector, a CrewAI task or any bespoke framework — is transformed into a canonical ",
      em("Intent Object"),
      ", scored across seven governance dimensions, and routed to a deterministic escalation tier between ",
      strong("SOAP"),
      " (autonomous execute) and ",
      strong("OHSHAT"),
      " (emergency stop, full cabinet escalation).",
    ),
    p(
      "BOSS replaces opaque confidence scores with a weighted, auditable composite on the 0–100 scale. It is engineered to pass regulatory audit under the EU AI Act Title IV obligations for high-risk and limited-risk AI systems, DORA ICT-risk and third-party register requirements, NIS2 incident classification, GDPR Article 22 automated-decision safeguards, ISO/IEC 42001 AI management systems, NIST CSF 2.0 and NIST AI RMF. Every decision produces a hash-chained ",
      strong("Decision Receipt"),
      " in the Flight Recorder, so a supervisor, an auditor, or a court-appointed reviewer can reconstruct exactly what was proposed, what BOSS scored, who approved it, and under which doctrine version.",
    ),
    p(
      "The engine ships as a FastAPI service with a Pydantic v2 data graph, a React 18 operator console, a Helm chart that deploys cleanly on AKS, EKS, GKE or k3d, and four framework adapters that require a single function call to govern an existing agent. A reference manual, an OpenAPI contract, a Schemathesis property-test suite and a zero-warning CODEX-ready Python codebase round out the release.",
    ),
    callout(
      "Design stance",
      "BOSS is deliberately conservative. When data is missing, scorers default to baseline-low but non-zero risk, so an under-specified intent still lands on the operator's desk rather than silently executing. A director can always loosen; BOSS never quietly tightens without a receipt.",
    ),
    h3("1.1 Key capabilities"),
    bullet([
      strong("Seven-dimension scoring "),
      t(
        "(Security, Sovereignty, Financial, Regulatory, Reputational, Rights, Doctrinal) with priority-tier weighting so every director can inspect influence at a glance.",
      ),
    ]),
    bullet([
      strong("Deterministic escalation "),
      t(
        "— SOAP, MODERATE, ELEVATED, HIGH, OHSHAT tiers with fixed SLA windows and pre-defined approver sets.",
      ),
    ]),
    bullet([
      strong("Hash-chained Flight Recorder "),
      t(
        "— immutable SHA-256 chain over every intent, score, exception and decision, exposed over REST.",
      ),
    ]),
    bullet([
      strong("Plug-in adapters "),
      t(
        "— LangGraph, OpenAI Agents, AI Foundry, CrewAI and a generic mapper. One-line integration: evaluate_payload(payload, framework=...).",
      ),
    ]),
    bullet([
      strong("Exception Economy "),
      t(
        "— ADAM-native packets, alternative-action surfacing, configurable approver cabinets, signed receipts.",
      ),
    ]),
    bullet([
      strong("Portable deployment "),
      t(
        "— multi-stage Docker image (non-root, read-only root FS, distroless-friendly), Helm chart with NetworkPolicy, HPA, PDB, ServiceMonitor, optional Neo4j StatefulSet.",
      ),
    ]),
    bullet([
      strong("Full observability "),
      t(
        "— Prometheus metrics, OpenTelemetry-ready, structured JSON logging, Grafana dashboards, /healthz and /readyz probes.",
      ),
    ]),
  ];
}

// ---------------------------------------------------------------------------
// Section 2 - ADAM context
// ---------------------------------------------------------------------------

function adamContext() {
  return [
    h1("2. ADAM context and BOSS positioning"),
    p(
      "ADAM is a reference architecture for governed autonomy: a five-director constitution, a doctrine-first control plane, an Exception Economy that routes human approvals, a Flight Recorder that makes every decision replayable, and an 81-agent mesh that executes bounded work inside dimension-specific doctrines. BOSS is ADAM's scoring organ. It consumes intents, produces composite scores and escalation tiers, and hands the Exception Economy a structured packet when human judgement is required.",
    ),
    h3("2.1 Where BOSS fits"),
    p(
      "In ADAM, an action proposal flows through five control stages: ",
      strong("Intent"),
      " -> ",
      strong("BOSS score"),
      " -> ",
      strong("Router"),
      " -> ",
      strong("Exception Economy"),
      " -> ",
      strong("Flight Recorder"),
      ". BOSS owns stages two and three; it publishes the score and the tier, then delegates any human-in-the-loop steps to the Exception Economy. Because the same scoring service is used by every agent on the mesh, policy changes propagate to every automation path simultaneously and can be proven to have done so via the Flight Recorder.",
    ),
    h3("2.2 Relationship to the ADAM 81-agent mesh"),
    p(
      "The 81-agent mesh (nine agents per dimension plus nine cross-cutting Doctrine agents) calls BOSS through the adapters at the framework boundary. Each adapter pins the agent's framework identity (LangGraph, OpenAI Agents, AI Foundry, CrewAI) on the intent for audit attribution, and rejects or escalates based on the returned ",
      code("DecisionAction"),
      ".",
    ),
    h3("2.3 Supported director cabinets"),
    p(
      "BOSS's Exception Economy approver map is configurable, but ships with the ADAM-default five-director cabinet:",
    ),
    buildTable(
      ["Director", "Dimensions", "SLA (OHSHAT)"],
      [
        ["CEO", "Doctrinal, cross-cutting", "15 min"],
        ["CFO", "Financial", "15 min"],
        ["CISO", "Security, Sovereignty", "15 min"],
        ["Legal Director", "Regulatory, Rights", "15 min"],
        ["Market Director", "Reputational", "15 min"],
      ],
      [1800, 5160, 2400],
    ),
    p(
      "For a High-tier exception the map reduces to one domain director; for Elevated it reduces to a domain governor. Moderate exceptions execute with enhanced logging; SOAP tier executes autonomously.",
    ),
  ];
}

// ---------------------------------------------------------------------------
// Section 3 - Architecture
// ---------------------------------------------------------------------------

function architecture() {
  return [
    h1("3. Architecture"),
    p(
      "BOSS is a stateless HTTP service over a small, explicit Python core. It has three logical layers:",
    ),
    numbered([
      strong("Core (boss_core). "),
      t(
        "Pure-functional dimension scorers, composite math, router, exception builder, Flight Recorder, hash-chain signer. No framework code. No I/O other than the optional Neo4j loader.",
      ),
    ]),
    numbered([
      strong("API (boss_api). "),
      t(
        "FastAPI app exposing REST endpoints under a configurable prefix (default /v1). Emits Prometheus metrics and JSON logs. Delegates persistence to a pluggable Flight Recorder sink (JSONL, Postgres, S3).",
      ),
    ]),
    numbered([
      strong("Adapters (boss_adapters). "),
      t(
        "Thin translators from framework-native payloads to the canonical IntentObject. No framework is imported at module load; adapters duck-type their inputs.",
      ),
    ]),
    p(
      "Two optional companions live in the same repo: a React 18 console (boss_console) for operators, and a data graph (boss_graph) that maps dimensions to regulatory frameworks (GDPR Article 5(1)f to Security, DORA Article 28 to Sovereignty, etc.) so audit teams can trace every score to a citable clause.",
    ),
    h3("3.1 Package layout"),
    ...codeBlock(
      [
        "boss-engine/",
        "|- boss_core/              # pure core: schemas, dimensions, composite, router, receipts",
        "|  |- schemas.py           # Pydantic v2 models (Intent, Result, Packet, Receipt, Event)",
        "|  |- tiers.py             # Priority Tier weighting (Top..Very Low)",
        "|  |- composite.py         # C = SUM(S*W) / SUM(W) + modifiers",
        "|  |- router.py            # SOAP..OHSHAT routing and SLA windows",
        "|  |- receipts.py          # Exception packet + hash-chained decision signer",
        "|  |- flight_recorder.py   # Append-only SHA-256 chain",
        "|  |- frameworks.py        # Regulatory framework registry",
        "|  |- graph_client.py      # Optional Neo4j loader",
        "|  |- dimensions/          # One scorer per dimension",
        "|",
        "|- boss_api/               # FastAPI + routers + middleware + telemetry",
        "|  |- main.py               # app factory",
        "|  |- settings.py           # pydantic-settings, BOSS_* env",
        "|  |- telemetry.py          # Prometheus + structured logging",
        "|  |- routers/              # intent, score, exceptions, receipts, config, graph, flight_recorder, health",
        "|",
        "|- boss_adapters/           # langgraph, openai_agents, ai_foundry, crewai, generic",
        "|",
        "|- boss_graph/              # Cypher bootstrap + framework catalog",
        "|- boss_console/            # React 18 operator UI",
        "|- deploy/                  # Helm chart + raw K8s + docker-compose",
        "|- docs/                    # Architecture, formulas, runbooks",
        "|- examples/                # Working adapter snippets",
        "|- tests/                   # unit + integration + property",
      ].join("\n"),
    ),
    h3("3.2 Request lifecycle"),
    p(
      "A governance request flows through the engine as follows:",
    ),
    numbered("The framework adapter receives a native action payload."),
    numbered([
      code("intent_from_payload()"),
      t(" normalises it into an IntentObject."),
    ]),
    numbered([
      code("composite.evaluate(intent, tier_config)"),
      t(
        " runs the seven dimension scorers, applies priority-tier weights, adds the Critical Override and Non-Idempotent modifiers, caps at 100, and routes to a tier.",
      ),
    ]),
    numbered([
      t("If the tier is SOAP, the adapter returns "),
      code("DecisionAction.ALLOW"),
      t("; for MODERATE, ALLOW_WITH_LOGGING; ELEVATED/HIGH, ESCALATE; OHSHAT, EMERGENCY_STOP."),
    ]),
    numbered([
      t(
        "If an exception is raised, the Exception Economy builds a packet naming approvers, alternatives and SLA, logs it, and waits for a signed DecisionReceipt.",
      ),
    ]),
    numbered([
      t(
        "The Flight Recorder appends every stage event with SHA-256 hash chaining, producing a tamper-evident audit trail.",
      ),
    ]),
  ];
}

// ---------------------------------------------------------------------------
// Section 4 - Dimensions
// ---------------------------------------------------------------------------

function dimensionsSection() {
  return [
    h1("4. The seven BOSS dimensions"),
    p(
      "Every intent is scored across exactly seven dimensions. The ordering is canonical — BOSS refuses to return a result that is missing any dimension — and every scorer produces a raw 0..100 score plus sub-component attribution.",
    ),
    buildTable(
      ["Dimension", "Question it answers", "Typical inputs"],
      [
        [
          "Security",
          "Could this breach an adversarial threat model?",
          "CVSS, threat model hit, exploit path, blast radius",
        ],
        [
          "Sovereignty",
          "Does data leave approved jurisdictions or run in non-approved environments?",
          "data residency, provider region, export controls",
        ],
        [
          "Financial",
          "What is the expected monetary exposure relative to director appetite?",
          "cost, loss estimate, recovery factor, appetite",
        ],
        [
          "Regulatory",
          "Does this violate a binding regulation or framework control?",
          "EU AI Act risk class, DORA clauses, GDPR articles",
        ],
        [
          "Reputational",
          "What is the anticipated brand and stakeholder fallout?",
          "media reach, sentiment polarity, stakeholder maps",
        ],
        [
          "Rights",
          "Does this infringe fundamental, contractual or licensing rights?",
          "IP, consent, labor, accessibility, DSR impact",
        ],
        [
          "Doctrinal",
          "Does this contradict the organisation's published doctrine?",
          "policy bundle version, conflict graph, precedent",
        ],
      ],
      [1700, 3560, 4100],
    ),
    h3("4.1 Scorer input contract"),
    p(
      "Every scorer receives a free-form dict under the relevant key of IntentObject.dimension_inputs and is expected to:",
    ),
    bullet("Accept missing fields gracefully and default to baseline-low risk."),
    bullet("Clamp raw_score to [0, 100]."),
    bullet("Emit SubComponentScore rows with name, value, max_value and rationale."),
    bullet("Populate frameworks with keys from boss_core.frameworks.FRAMEWORKS."),
    bullet("Populate evidence_refs so the Flight Recorder can trace what was seen."),
    h3("4.2 Sub-component catalog (abridged)"),
    buildTable(
      ["Dimension", "Key sub-components"],
      [
        ["Security", "cvss_score, threat_model_hit, exploit_path, blast_radius"],
        ["Sovereignty", "data_residency_violation, export_control_flag, region_mismatch"],
        ["Financial", "cost_ratio, loss_ratio, appetite, recovery_factor"],
        ["Regulatory", "eu_ai_act_class, dora_gap, gdpr_conflict, controls_gap_pct"],
        ["Reputational", "media_reach, sentiment_polarity, stakeholder_exposure"],
        ["Rights", "ip_conflict, consent_gap, accessibility_gap, dsr_impact"],
        ["Doctrinal", "policy_conflict_count, doctrine_distance, precedent_alignment"],
      ],
      [1700, 7660],
    ),
    p(
      "Sub-component schemas are declared and validated at the dimension-module level so they remain strongly typed without polluting the IntentObject surface.",
    ),
  ];
}

// ---------------------------------------------------------------------------
// Section 5 - Priority tiers & composite formula
// ---------------------------------------------------------------------------

function formulaSection() {
  return [
    h1("5. Priority Tiers and the composite formula"),
    p(
      "BOSS replaces arbitrary decimal weights with a six-level priority scale that any director, auditor or regulator can interpret at a glance. The tier-to-weight mapping is fixed and deterministic.",
    ),
    buildTable(
      ["Priority Tier", "Weight", "Intent"],
      [
        ["Top", "5.0", "Non-negotiable first-order risk (exactly one allowed)"],
        ["Very High", "4.0", "Second-order existential risks"],
        ["High", "3.0", "Regulated or consequential domains"],
        ["Medium", "2.0", "Operationally material but bounded"],
        ["Low", "1.0", "Bounded risk, tolerable variance"],
        ["Very Low", "0.5", "Informational-only dimensions"],
      ],
      [2200, 1000, 6160],
    ),
    h3("5.1 Composite formula (C)"),
    ...codeBlock(
      [
        "C_raw       = SUM(S_d * W_d) / SUM(W_d)   for d in {Security..Doctrinal}",
        "",
        "Modifiers applied in order:",
        "    (a) Critical Override    — if any S_d > 75,",
        "                                C >= max(S_d) - 10",
        "    (b) Non-Idempotent bump   — +15 if intent.is_non_idempotent",
        "    (c) Cap                   — clamp C to 100",
        "",
        "C_final     = min(max(C_raw_after_modifiers, 0), 100)",
      ].join("\n"),
    ),
    h3("5.2 Why Critical Override exists"),
    p(
      "A single catastrophic dimension can be diluted by six low-scoring dimensions under a pure weighted average. The Critical Override ensures that a >75 score on any dimension cannot be drowned below (max - 10) by the rest of the bundle. In practice this means a Security score of 82 alone will force a composite of at least 72 (HIGH tier), even if every other dimension is zero.",
    ),
    h3("5.3 Why Non-Idempotent penalty exists"),
    p(
      "Reversibility is treated as a first-class risk axis in ADAM. If an action cannot be rolled back (money moved, data exfiltrated, contract signed, agent deregistered) BOSS adds a flat +15 to force at least one tier of escalation. Callers should opt-in by setting ",
      code("is_non_idempotent=true"),
      " on the intent or by letting the adapter infer it from payload hints like ",
      code("irreversible"),
      " or ",
      code("reversible=false"),
      ".",
    ),
    h3("5.4 ADAM default tier configuration"),
    buildTable(
      ["Dimension", "Tier", "Weight", "Contribution %"],
      [
        ["Security", "Top", "5.0", "27.03%"],
        ["Sovereignty", "Very High", "4.0", "21.62%"],
        ["Financial", "Very High", "4.0", "21.62%"],
        ["Regulatory", "High", "3.0", "16.22%"],
        ["Reputational", "High", "3.0", "16.22%"],
        ["Rights", "High", "3.0", "16.22%"],
        ["Doctrinal", "Medium", "2.0", "10.81%"],
      ],
      [2000, 1800, 1280, 4280],
    ),
    p(
      "Contribution percentages sum to more than 100 because they are computed against the same denominator (SUM(W) = 18.5) without the weighting being re-normalised — this is a transparency choice: each dimension's contribution is always visible against the same base.",
    ),
    callout(
      "Rule: exactly one Top",
      "BOSS rejects any TierConfig that does not assign exactly one dimension to Top. This enforces the ADAM philosophy that if everything is the highest priority, nothing is — directors must commit to a single, publicly-defensible first-order risk.",
    ),
  ];
}

// ---------------------------------------------------------------------------
// Section 6 - Router
// ---------------------------------------------------------------------------

function routerSection() {
  return [
    h1("6. Escalation router: SOAP to OHSHAT"),
    p(
      "The composite is mapped to one of five tiers. Each tier has a fixed SLA and a fixed approver set.",
    ),
    buildTable(
      ["Tier", "Range", "SLA", "Default action", "Approvers"],
      [
        ["SOAP", "0–10", "none", "ALLOW", "autonomous"],
        ["MODERATE", "11–30", "none", "ALLOW_WITH_LOGGING", "enhanced logging"],
        ["ELEVATED", "31–50", "60 min", "ESCALATE", "domain governor"],
        ["HIGH", "51–75", "4 h", "ESCALATE", "domain director"],
        [
          "OHSHAT",
          "76–100",
          "15 min",
          "EMERGENCY_STOP",
          "CEO + CFO + legal + market + CISO",
        ],
      ],
      [1300, 1100, 1000, 2600, 3360],
    ),
    p(
      "SOAP stands for ",
      em("Safe & Optimum Autonomous Performance"),
      "; OHSHAT stands for ",
      em("Operational Hell, Send Humans — Act Today"),
      ". The humour is intentional: ADAM favours memorable acronyms because they travel well in boardrooms and war-room calls.",
    ),
    h3("6.1 Acting on tier decisions"),
    p(
      "Callers map the tier to a runtime instruction via ",
      code("DecisionAction"),
      " on the AdapterDecision return value:",
    ),
    ...codeBlock(
      [
        "SOAP      -> DecisionAction.ALLOW",
        "MODERATE  -> DecisionAction.ALLOW_WITH_LOGGING",
        "ELEVATED  -> DecisionAction.ESCALATE",
        "HIGH      -> DecisionAction.ESCALATE",
        "OHSHAT    -> DecisionAction.EMERGENCY_STOP",
      ].join("\n"),
    ),
    p(
      "Callers who need finer control (for example, to block on HIGH but escalate on ELEVATED) can introspect ",
      code("AdapterDecision.boss_result"),
      " and build their own mapping while still recording the BOSS tier in their audit trail.",
    ),
  ];
}

// ---------------------------------------------------------------------------
// Section 7 - Exceptions / receipts / Flight Recorder
// ---------------------------------------------------------------------------

function exceptionSection() {
  return [
    h1("7. Exception packets, decision receipts, Flight Recorder"),
    h3("7.1 Exception packet"),
    p(
      "When an intent does not qualify for SOAP, BOSS builds an ExceptionPacket containing:",
    ),
    bullet([strong("intent_id / result_id "), t(" — links to the original intent and score.")]),
    bullet([strong("escalation_tier "), t(" — MODERATE..OHSHAT.")]),
    bullet([strong("summary "), t(" — one-line natural-language description including the headline and composite.")]),
    bullet([strong("drivers "), t(" — the top three scoring dimensions and any modifiers, with contribution percentages.")]),
    bullet([strong("required_approvers "), t(" — the director cabinet subset needed (by role, not person).")]),
    bullet([strong("alternatives "), t(" — a list of AlternativeAction objects with projected composites. Directors may pick one and BOSS re-scores with the alt's inputs.")]),
    bullet([strong("response_sla_minutes "), t(" — driven by the tier.")]),
    bullet([strong("recommended_alternative "), t(" — BOSS's pre-ranked pick (first-in-list).")]),
    h3("7.2 Decision receipt"),
    p(
      "When a director signs an approval, BOSS writes a ",
      strong("DecisionReceipt"),
      " with a SHA-256 hash over the canonical JSON body plus the prior_hash of the last recorded receipt. The chain is per-tenant and per-doctrine-version, so forging a single receipt requires forging every subsequent receipt — exactly the property auditors want.",
    ),
    ...codeBlock(
      [
        "receipt_hash = sha256(",
        '    canonical_json({"packet_id": packet_id,',
        '                     "intent_id": intent_id,',
        '                     "result_id": result_id,',
        '                     "director_id": director_id,',
        '                     "decision": "APPROVE|APPROVE_WITH_CONSTRAINTS|REJECT|DEFER|ESCALATE",',
        '                     "selected_alternative": alt_id or null,',
        '                     "applied_constraints": [...],',
        '                     "director_note": str or null,',
        '                     "signed_at": "...",',
        '                     "prior_hash": prior_hash})',
        ")",
      ].join("\n"),
    ),
    h3("7.3 Flight Recorder"),
    p(
      "The Flight Recorder is an append-only, hash-chained event log with five event types: ",
      code("INTENT_RECEIVED"),
      ", ",
      code("SCORED"),
      ", ",
      code("EXCEPTION_RAISED"),
      ", ",
      code("DECISION_RECORDED"),
      ", ",
      code("CONFIG_CHANGED"),
      ". Each event carries a signer, prior_hash, payload and SHA-256 event_hash. The default sink is JSON-Lines on local disk; Postgres and S3 sinks ship in ",
      code("boss_core.flight_recorder.sinks"),
      " and can be selected via ",
      code("BOSS_FLIGHT_SINK=postgres"),
      " or ",
      code("BOSS_FLIGHT_SINK=s3"),
      ".",
    ),
    callout(
      "Audit guarantee",
      "Replay the entire Flight Recorder and BOSS will re-derive the exact same composite for every intent, because all inputs (dimension payloads, tier config, doctrine version, non-idempotent flag) are captured in the INTENT_RECEIVED event. This is the property that lets a regulator ask \"what would BOSS have done on day X with yesterday's data?\" and get a deterministic answer.",
    ),
  ];
}

// ---------------------------------------------------------------------------
// Section 8 - API contract
// ---------------------------------------------------------------------------

function apiSection() {
  return [
    h1("8. API contract"),
    p(
      "The FastAPI app mounts under a configurable prefix (default ",
      code("/v1"),
      "). OpenAPI is served at ",
      code("/v1/openapi.json"),
      " and the Swagger UI at ",
      code("/v1/docs"),
      ". Every endpoint is JSON-over-HTTPS, every response body is a Pydantic model documented in the OpenAPI schema, and every endpoint emits a Prometheus counter labelled by status code.",
    ),
    buildTable(
      ["Method", "Path", "Purpose"],
      [
        ["GET", "/v1/healthz", "Liveness probe — always 200 while process up."],
        ["GET", "/v1/readyz", "Readiness probe — verifies Flight Recorder sink is writable."],
        ["GET", "/v1/version", "Engine + schema + doctrine versions."],
        ["GET", "/v1/metrics", "Prometheus exposition (text format)."],
        ["POST", "/v1/intents", "Register an intent object without scoring it."],
        ["POST", "/v1/score", "Score an intent; returns BOSSResult and pre-built routing."],
        ["GET", "/v1/score/{intent_id}/explain", "Retrieve the sub-component and modifier breakdown of a prior score."],
        ["POST", "/v1/exceptions", "Build an exception packet from a known intent+result."],
        ["POST", "/v1/receipts", "Submit a signed director decision, returns the hash-chained DecisionReceipt."],
        ["GET", "/v1/config/tiers", "Get the current TierConfig."],
        ["PUT", "/v1/config/tiers", "Replace the TierConfig (author + reason required)."],
        ["GET", "/v1/graph/frameworks", "List regulatory frameworks known to the engine."],
        ["GET", "/v1/graph/dimensions", "List dimensions and their framework attribution."],
        ["GET", "/v1/graph/ping", "Health-check the data graph backend."],
        ["GET", "/v1/flightrecorder", "Tail the Flight Recorder event chain."],
      ],
      [900, 2800, 5660],
    ),
    h3("8.1 POST /v1/score"),
    p(
      "The principal endpoint. Request body is an ",
      code("IntentObject"),
      "; response is a ",
      code("ScoreEnvelope"),
      " wrapping a BOSSResult, the routing verdict and the exception packet when applicable.",
    ),
    ...codeBlock(
      [
        "POST /v1/score HTTP/1.1",
        "content-type: application/json",
        "",
        "{",
        '  "source": {"user_id": "agent-fin-07", "role": "system"},',
        '  "headline": "Move EUR 250,000 from treasury to vendor",',
        '  "urgency": "elevated",',
        '  "is_non_idempotent": true,',
        '  "dimension_inputs": {',
        '    "financial": {"cost_eur": 250000, "appetite_eur": 100000, "loss_eur": 0},',
        '    "regulatory": {"dora_clauses_in_scope": ["Art28"]},',
        '    "sovereignty": {"data_regions": ["EU-NL"], "approved_regions": ["EU"]}',
        "  }",
        "}",
      ].join("\n"),
    ),
    ...codeBlock(
      [
        "HTTP/1.1 200 OK",
        "content-type: application/json",
        "",
        "{",
        '  "result": {',
        '    "composite_final": 61.4,',
        '    "escalation_tier": "HIGH",',
        '    "dimension_scores": { "security": {...}, "financial": {...}, ... },',
        '    "modifiers": [',
        '      {"name": "non_idempotent_penalty", "delta": 15.0, ...}',
        "    ]",
        "  },",
        '  "decision_action": "escalate",',
        '  "exception_packet": { "required_approvers": ["cfo"], ... }',
        "}",
      ].join("\n"),
    ),
    h3("8.2 Authentication"),
    p(
      "The service supports three authentication modes configured through ",
      code("BOSS_AUTH_MODE"),
      ":",
    ),
    bullet([
      strong("none "),
      t(" — for local dev; the service logs a warning at startup."),
    ]),
    bullet([
      strong("bearer "),
      t(" — JWT Bearer, verified against JWKS from "),
      code("BOSS_AUTH_JWKS_URL"),
      t(". Required claims: issuer, audience, expiry, and a "),
      code("boss:roles"),
      t(" claim."),
    ]),
    bullet([
      strong("mTLS "),
      t(" — client-certificate termination at the ingress; BOSS reads "),
      code("X-Client-Cert-Subject"),
      t(" and maps CN to actor identity."),
    ]),
    h3("8.3 Rate limits"),
    p(
      "Default burst limit is 50 req/s per actor; configurable through ",
      code("BOSS_RATE_LIMIT"),
      ". Exceeded limits return 429 with ",
      code("Retry-After"),
      ".",
    ),
  ];
}

// ---------------------------------------------------------------------------
// Section 9 - Data graph
// ---------------------------------------------------------------------------

function graphSection() {
  return [
    h1("9. Data graph: frameworks x dimensions"),
    p(
      "BOSS ships with a regulatory data graph that maps each dimension to the external frameworks it must satisfy. The graph is loaded into an optional Neo4j instance for visualisation, but the in-memory Python catalog is the source of truth and is always available. Every framework entry carries clause-level references so an exception packet can include citations directly.",
    ),
    buildTable(
      ["Dimension", "Frameworks mapped"],
      [
        ["Security", "NIST CSF 2.0, ISO 27001, MITRE ATT&CK, OWASP ASVS"],
        ["Sovereignty", "EU AI Act Title IV, DORA Art 28, Schrems II, GDPR Ch V"],
        [
          "Financial",
          "ISO 31000, COSO ERM, Basel III ICAAP, IFRS 9 (ECL)",
        ],
        [
          "Regulatory",
          "EU AI Act, DORA, NIS2, GDPR, MAR, MiFID II, SOC 2",
        ],
        ["Reputational", "ISO 22301, Edelman Trust Barometer proxy"],
        ["Rights", "EU Charter, UN Guiding Principles, WIPO, WCAG 2.2"],
        [
          "Doctrinal",
          "ADAM Doctrine Manifest (bundle-scoped), ISO/IEC 42001",
        ],
      ],
      [1800, 7560],
    ),
    p(
      "The catalog is exposed at ",
      code("GET /v1/graph/frameworks"),
      ". Each entry includes a ",
      code("clause_anchors"),
      " list of deep-linkable IDs that scorers can attach to evidence_refs so directors see exactly which clause drove the score.",
    ),
    h3("9.1 Neo4j bootstrap"),
    p(
      "The Helm chart includes an optional Neo4j StatefulSet. When enabled, a post-install Job loads the framework catalog via Cypher and creates constraints on ",
      code("(:Framework {id})"),
      ", ",
      code("(:Dimension {key})"),
      " and ",
      code("[:COVERS]"),
      " relationships. The resulting graph is read-only from BOSS's perspective — updates go through the engine's REST API and are then mirrored.",
    ),
  ];
}

// ---------------------------------------------------------------------------
// Section 10 - Governance alignment
// ---------------------------------------------------------------------------

function governanceSection() {
  return [
    h1("10. Governance alignment"),
    p(
      "BOSS is engineered to make regulatory audit mechanical. Each framework below is mapped to specific engine behaviours so a compliance team can walk an auditor from clause to code.",
    ),
    h3("10.1 EU AI Act"),
    buildTable(
      ["Obligation", "BOSS behaviour"],
      [
        [
          "Risk classification (Art 6)",
          "IntentObject.context.policy_bundle carries the risk class; scorers refuse to emit SOAP for any intent tagged 'high-risk' without an explicit override.",
        ],
        [
          "Risk management system (Art 9)",
          "Composite score with seven-dimension attribution and documented modifiers is the 'established, implemented, documented' risk system.",
        ],
        [
          "Transparency & human oversight (Art 13, 14)",
          "Exception packets name approvers; console shows the reasoning chain; every decision receipt records the human signer.",
        ],
        [
          "Technical documentation (Art 11)",
          "This manual + the OpenAPI + the doctrine manifest form the technical file; all three are versioned together.",
        ],
        [
          "Record-keeping (Art 12)",
          "Flight Recorder provides the tamper-evident log covering all events for the operational lifetime.",
        ],
      ],
      [2800, 6560],
    ),
    h3("10.2 DORA (Reg. (EU) 2022/2554)"),
    bullet([strong("Art 5-8 "), t(" ICT risk management — BOSS dimensions Security, Sovereignty and Regulatory directly score ICT-risk inputs.")]),
    bullet([strong("Art 17-22 "), t(" ICT-related incident classification and reporting — OHSHAT tier triggers incident export hooks.")]),
    bullet([strong("Art 28-30 "), t(" Third-party risk — the Sovereignty scorer ingests the TPRM register and escalates non-approved providers.")]),
    bullet([strong("Art 35 "), t(" Threat-led penetration testing — exercised via scripted Schemathesis campaigns against the Security dimension payloads.")]),
    h3("10.3 NIS2 (Dir. (EU) 2022/2555)"),
    p(
      "BOSS OHSHAT outputs are aligned with NIS2 Art 23 incident notification windows: the 24-hour early warning and the 72-hour notification are both achievable from the Flight Recorder's event stream with no additional wiring.",
    ),
    h3("10.4 GDPR"),
    bullet([strong("Art 5(1)f "), t(" Integrity and confidentiality — covered by the Security dimension.")]),
    bullet([strong("Art 22 "), t(" Right to human review of automated decisions — ELEVATED/HIGH/OHSHAT always require human approval; SOAP/MODERATE execute autonomously but can be escalated on request.")]),
    bullet([strong("Ch V "), t(" International transfers — covered by the Sovereignty dimension.")]),
    bullet([strong("Art 30 "), t(" Records of processing — the Flight Recorder doubles as a processing register, filterable per-data-subject via the intent's delegation chain.")]),
    h3("10.5 ISO/IEC 42001"),
    p(
      "The AI Management System standard. BOSS provides the operational scoring substrate; the doctrine manifest and tier configuration provide the management-system artefacts the standard requires. Clauses 6 (planning) and 8 (operation) are satisfied through the Priority Tier configuration workflow; clause 9 (performance evaluation) is fed by the Prometheus + Flight Recorder telemetry.",
    ),
    h3("10.6 NIST CSF 2.0 & NIST AI RMF"),
    bullet([strong("CSF GV, ID, PR "), t(" — satisfied via the Regulatory and Security dimensions and the doctrine manifest.")]),
    bullet([strong("CSF DE, RS, RC "), t(" — satisfied by the OHSHAT flow + Flight Recorder.")]),
    bullet([strong("AI RMF Map, Measure, Manage, Govern "), t(" — cover by scorer attribution, composite scoring, escalation routing and tier configuration, respectively.")]),
    callout(
      "Not legal advice",
      "This section maps engine behaviour to obligations. It does not replace in-house counsel or Notified Body review. Adopters are responsible for confirming their specific deployment meets their specific obligations.",
    ),
  ];
}

// ---------------------------------------------------------------------------
// Section 11 - Deployment
// ---------------------------------------------------------------------------

function deploySection() {
  return [
    h1("11. Deployment"),
    h3("11.1 Quickstart with Docker"),
    ...codeBlock(
      [
        "# Clone and run",
        "git clone https://github.com/adam-os/boss-engine.git",
        "cd boss-engine",
        "docker compose up -d",
        "",
        "# Smoke test",
        "curl -s http://localhost:8080/v1/healthz",
        "curl -s http://localhost:8080/v1/version",
      ].join("\n"),
    ),
    h3("11.2 Helm chart"),
    ...codeBlock(
      [
        "helm repo add adam https://charts.adam.dev",
        "helm repo update",
        "",
        "helm install boss adam/boss-engine \\",
        "  --namespace adam --create-namespace \\",
        "  --values deploy/helm/values-prod.yaml",
      ].join("\n"),
    ),
    p(
      "Chart features: NetworkPolicy default-deny, PodDisruptionBudget (minAvailable=1), HPA (CPU 70%), ServiceMonitor for Prometheus Operator, optional Neo4j StatefulSet, cert-manager integration for TLS. All containers run as UID 1000 with read-only root FS, all caps dropped and seccomp RuntimeDefault.",
    ),
    h3("11.3 Configuration reference"),
    buildTable(
      ["Env var", "Default", "Purpose"],
      [
        ["BOSS_API_PREFIX", "/v1", "REST prefix"],
        ["BOSS_AUTH_MODE", "bearer", "none | bearer | mTLS"],
        ["BOSS_AUTH_JWKS_URL", "-", "JWKS endpoint for JWT verification"],
        ["BOSS_TENANT_ID", "default", "Multi-tenant separator for Flight Recorder"],
        ["BOSS_DOCTRINE_VERSION", "unspecified", "Recorded on every event"],
        ["BOSS_FLIGHT_SINK", "jsonl", "jsonl | postgres | s3"],
        ["BOSS_FLIGHT_PATH", "/var/lib/boss/fr.jsonl", "Path when sink=jsonl"],
        ["BOSS_GRAPH_BACKEND", "memory", "memory | neo4j"],
        ["BOSS_NEO4J_URL", "-", "Bolt URL when backend=neo4j"],
        ["BOSS_METRICS_ENABLED", "true", "Toggle /metrics"],
        ["BOSS_LOG_LEVEL", "INFO", "DEBUG | INFO | WARNING | ERROR"],
      ],
      [2600, 2400, 4360],
    ),
    h3("11.4 Resource sizing"),
    bullet("Baseline: 250m CPU / 256Mi RAM per replica handles ~120 req/s score workload."),
    bullet("Throughput scales linearly with replicas; Flight Recorder is the single shared contention point and should use the Postgres or S3 sink in production."),
    bullet("Recommended: 3 replicas, HPA 3..10, Neo4j sized for 2x framework catalog size."),
    h3("11.5 Multi-cloud notes"),
    bullet([strong("AKS "), t(" — enable workload identity, map BOSS_AUTH_MODE to Entra JWKS, use Azure Files for shared Flight Recorder JSONL if not using Postgres.")]),
    bullet([strong("EKS "), t(" — IRSA for the S3 sink; ALB ingress for mTLS termination; use Aurora Serverless v2 for Postgres sink.")]),
    bullet([strong("GKE "), t(" — Workload Identity; Cloud SQL for Postgres sink; Config Connector for declarative tier config.")]),
    bullet([strong("k3d / local "), t(" — docker-compose is the supported path; Helm chart runs unchanged on k3d for integration testing.")]),
  ];
}

// ---------------------------------------------------------------------------
// Section 12 - Adapter guide
// ---------------------------------------------------------------------------

function adapterSection() {
  return [
    h1("12. Adapter integration guide"),
    p(
      "Every adapter ships with a single-call entry-point that normalises the framework's action payload, constructs an IntentObject, scores it, and returns a typed ",
      code("AdapterDecision"),
      " telling the caller whether to allow, log, escalate or emergency-stop.",
    ),
    h3("12.1 LangGraph"),
    ...codeBlock(
      [
        "from langchain_core.tools import BaseTool",
        "from boss_adapters import evaluate_payload, DecisionAction",
        "",
        "class GovernedTool(BaseTool):",
        '    name = "move_funds"',
        "    def _run(self, **kwargs):",
        '        decision = evaluate_payload({"tool": self.name, **kwargs},',
        '                                    framework="langgraph")',
        "        if decision.action == DecisionAction.BLOCK:",
        "            raise PermissionError(decision.rationale)",
        "        if decision.action == DecisionAction.ESCALATE:",
        "            raise RuntimeError(f\"Escalate: {decision.rationale}\")",
        "        return self._really_move(**kwargs)",
      ].join("\n"),
    ),
    h3("12.2 OpenAI Agents"),
    ...codeBlock(
      [
        "from boss_adapters import evaluate_payload, DecisionAction",
        "",
        "async def guardrail(ctx, tool_name, arguments):",
        '    d = evaluate_payload({"name": tool_name, "arguments": arguments},',
        '                         framework="openai_agents")',
        "    if d.action is not DecisionAction.ALLOW:",
        "        return {\"refused\": True, \"reason\": d.rationale}",
        "    return None  # allow tool to run",
      ].join("\n"),
    ),
    h3("12.3 Azure AI Foundry"),
    p(
      "AI Foundry connectors call out to a governance hook before executing any action. Wire BOSS into that hook:",
    ),
    ...codeBlock(
      [
        "from boss_adapters import evaluate_payload, DecisionAction",
        "",
        "def foundry_hook(action, context):",
        '    d = evaluate_payload({"action": action.name,',
        '                          "args": action.arguments,',
        '                          "boss_inputs": context.get("boss_inputs", {})},',
        '                         framework="ai_foundry",',
        '                         tenant=context["tenant"])',
        "    if d.action is DecisionAction.EMERGENCY_STOP:",
        "        context.set_result(\"halt\")",
        "        return False",
        "    return d.action is not DecisionAction.BLOCK",
      ].join("\n"),
    ),
    h3("12.4 CrewAI"),
    ...codeBlock(
      [
        "from boss_adapters import evaluate_payload, DecisionAction",
        "",
        "def pre_task_checkpoint(task):",
        '    d = evaluate_payload({"task": task.description,',
        '                          "description": task.expected_output},',
        '                         framework="crewai")',
        "    if d.action != DecisionAction.ALLOW:",
        "        task.skip(reason=d.rationale)",
      ].join("\n"),
    ),
    h3("12.5 Generic / custom"),
    p(
      "The generic adapter accepts any dict with at minimum a ",
      code("headline"),
      " or ",
      code("tool"),
      " key. Nest BOSS-specific inputs under ",
      code("boss_inputs"),
      " to pre-populate dimension evidence:",
    ),
    ...codeBlock(
      [
        "from boss_adapters import evaluate_payload",
        "",
        "d = evaluate_payload({",
        '    "headline": "Custom agent performing FX sweep",',
        '    "is_non_idempotent": True,',
        '    "boss_inputs": {',
        '        "financial": {"cost_eur": 42000, "appetite_eur": 50000},',
        '        "regulatory": {"dora_clauses_in_scope": ["Art17"]}',
        "    }",
        '}, framework="generic")',
      ].join("\n"),
    ),
  ];
}

// ---------------------------------------------------------------------------
// Section 13 - Worked examples
// ---------------------------------------------------------------------------

function examplesSection() {
  return [
    h1("13. Worked examples (NetStreamX)"),
    p(
      "NetStreamX is ADAM's fictional Amsterdam-head-quartered streaming platform used as the running example throughout the book. The three scenarios below exercise the engine end-to-end.",
    ),
    h3("13.1 SOAP example: publish cat-video thumbnail"),
    p(
      "A content-ops agent proposes to publish a new thumbnail for a cat-video carousel tile. The action is reversible (thumbnails can be replaced), inside the EU region, has zero financial exposure, and touches no personal data. BOSS scores it cleanly.",
    ),
    buildTable(
      ["Dimension", "Raw", "Weight", "Contribution (weighted)"],
      [
        ["Security", "4.2", "5.0", "21.0"],
        ["Sovereignty", "1.0", "4.0", "4.0"],
        ["Financial", "0.5", "4.0", "2.0"],
        ["Regulatory", "3.0", "3.0", "9.0"],
        ["Reputational", "18.0", "3.0", "54.0"],
        ["Rights", "2.0", "3.0", "6.0"],
        ["Doctrinal", "0.0", "2.0", "0.0"],
      ],
      [1600, 1400, 1400, 4960],
    ),
    p(
      "Sum of weights = 24.0; weighted sum = 96.0; composite_raw = 96.0 / 24.0 = 4.0. No critical override (max dim 18 < 75), not non-idempotent, below cap. ",
      strong("Final: 4.0 -> SOAP -> ALLOW."),
    ),
    h3("13.2 ELEVATED example: Amber Coast campaign launch"),
    p(
      "Marketing proposes a campaign targeted at a new region (\"Amber Coast\"), EUR 140,000 budget, reversible but time-boxed. Regulatory has mid-range exposure because the region has active data-protection enforcement this quarter; Reputational risk is moderate because the campaign is political-adjacent.",
    ),
    buildTable(
      ["Dimension", "Raw", "Weight", "Weighted"],
      [
        ["Security", "10.0", "5.0", "50.0"],
        ["Sovereignty", "22.0", "4.0", "88.0"],
        ["Financial", "28.0", "4.0", "112.0"],
        ["Regulatory", "44.0", "3.0", "132.0"],
        ["Reputational", "55.0", "3.0", "165.0"],
        ["Rights", "18.0", "3.0", "54.0"],
        ["Doctrinal", "12.0", "2.0", "24.0"],
      ],
      [1600, 1400, 1400, 4960],
    ),
    p(
      "SUM(W)=24.0; SUM(S*W)=625.0; composite_raw = 625.0 / 24.0 ~= 26.04. Reversible so no +15 penalty. Max dim 55 < 75 so no critical override. ",
      strong("Final: 26.04 -> MODERATE."),
      " If the team chooses an irreversible buy-out variant (is_non_idempotent=true), +15 pushes the composite to 41.04 -> ",
      strong("ELEVATED -> ESCALATE"),
      " (domain governor, 60-min SLA).",
    ),
    h3("13.3 OHSHAT example: cross-border content takedown"),
    p(
      "A legal-ops agent proposes to takedown a viral political video across multiple jurisdictions at regulator request, without prior director approval. Security ok (internal action), Sovereignty high (multi-region write), Financial low, Regulatory very high (active matter), Reputational extreme, Rights extreme (freedom-of-expression exposure), Doctrinal medium.",
    ),
    buildTable(
      ["Dimension", "Raw", "Weight", "Weighted"],
      [
        ["Security", "12.0", "5.0", "60.0"],
        ["Sovereignty", "82.0", "4.0", "328.0"],
        ["Financial", "14.0", "4.0", "56.0"],
        ["Regulatory", "88.0", "3.0", "264.0"],
        ["Reputational", "94.0", "3.0", "282.0"],
        ["Rights", "92.0", "3.0", "276.0"],
        ["Doctrinal", "66.0", "2.0", "132.0"],
      ],
      [1600, 1400, 1400, 4960],
    ),
    p(
      "SUM(W)=24.0; SUM(S*W)=1398.0; composite_raw ~= 58.25. Critical Override fires (Reputational 94>75; floor = 94 - 10 = 84). Action is non-idempotent (takedowns are hard to reverse) so +15 -> 99. Cap applies -> ",
      strong("Final: 99.0 -> OHSHAT -> EMERGENCY_STOP"),
      ". Exception packet requires CEO + CFO + legal + market + CISO signatures within 15 minutes; recommended alternative: \"delay execution pending injunction review.\" Without director sign-off the engine will not unblock.",
    ),
    callout(
      "What directors see",
      "The Exception Economy packet surfaces the top three drivers in plain English: \"Rights scored 92 (16.22% contribution); Reputational scored 94 (16.22% contribution); Sovereignty scored 82 (21.62% contribution). critical_dimension_override: composite raised to max - 10. non_idempotent_penalty: +15.0 because action is irreversible.\" This language is copy-pasted verbatim into the decision log.",
    ),
  ];
}

// ---------------------------------------------------------------------------
// Section 14 - Security / Ops
// ---------------------------------------------------------------------------

function opsSection() {
  return [
    h1("14. Security, observability, operations"),
    h3("14.1 Threat model"),
    bullet([strong("T1: Malicious actor submits forged intent. "), t("Mitigation: bearer JWT + actor role check; intents signed by the originating adapter service account.")]),
    bullet([strong("T2: Scorer poisoning. "), t("Mitigation: dimension scorers are pure functions of the intent payload; no network egress inside scorers; input schemas strictly validated.")]),
    bullet([strong("T3: Tier-config tampering. "), t("Mitigation: PUT /v1/config/tiers requires author + reason, emits a CONFIG_CHANGED event, and only director roles may call it.")]),
    bullet([strong("T4: Flight Recorder rewrite. "), t("Mitigation: append-only JSONL with SHA-256 hash chain; Postgres/S3 sinks use write-once semantics; daily chain-head snapshot pushed to immutable storage.")]),
    bullet([strong("T5: Replay. "), t("Mitigation: intents carry a UUID and timestamp; duplicate intent_ids within a configurable window are rejected.")]),
    h3("14.2 Metrics"),
    buildTable(
      ["Metric", "Type", "Labels", "Meaning"],
      [
        ["boss_score_total", "counter", "tier", "Number of scores computed, labelled by output tier."],
        ["boss_score_seconds", "histogram", "-", "Latency of composite evaluation."],
        ["boss_exception_total", "counter", "tier", "Exception packets generated."],
        ["boss_flightrecorder_depth", "gauge", "-", "Number of events in the local chain."],
        ["boss_http_requests_total", "counter", "path, code", "Standard FastAPI request counter."],
      ],
      [3000, 1100, 1400, 3860],
    ),
    h3("14.3 Dashboards"),
    p(
      "Grafana dashboards ship under ",
      code("deploy/grafana/"),
      ": ",
      em("Scoring overview"),
      " (tier distribution, latency p50/p95/p99), ",
      em("Exception Economy"),
      " (packet rate, approver SLA burn-down), ",
      em("Compliance"),
      " (GDPR Art 22 escalations, DORA TPRM hits).",
    ),
    h3("14.4 Runbooks"),
    bullet([strong("BOSS-RUN-01 "), t(" OHSHAT page received — verify director cabinet, confirm emergency-stop action propagated to agent runtime, capture Flight Recorder segment for post-mortem.")]),
    bullet([strong("BOSS-RUN-02 "), t(" Flight Recorder sink outage — switch sink to secondary, reconcile chain heads during window, flag for chain-verification scan.")]),
    bullet([strong("BOSS-RUN-03 "), t(" Tier config rollback — GET /v1/config/tiers?at=... returns the prior configuration; PUT it back with reason=\"rollback\" and sign a CONFIG_CHANGED receipt.")]),
  ];
}

// ---------------------------------------------------------------------------
// Section 15 - Appendix A: REST reference
// ---------------------------------------------------------------------------

function restReference() {
  return [
    h1("15. Appendix A — Full REST reference"),
    h3("15.1 Health and metadata"),
    buildTable(
      ["Path", "Response", "Notes"],
      [
        ["GET /v1/healthz", "{status: \"ok\"}", "Always 200 while process is alive."],
        [
          "GET /v1/readyz",
          "{status, flight_recorder_head}",
          "503 if sink unreachable.",
        ],
        [
          "GET /v1/version",
          "{engine, schema, doctrine}",
          "Three-part version tuple.",
        ],
        [
          "GET /v1/metrics",
          "text/plain",
          "Prometheus exposition.",
        ],
      ],
      [2800, 3060, 3500],
    ),
    h3("15.2 Intent and scoring"),
    buildTable(
      ["Path", "Body", "Notes"],
      [
        [
          "POST /v1/intents",
          "IntentObject",
          "Register without scoring; emits INTENT_RECEIVED event.",
        ],
        [
          "POST /v1/score",
          "IntentObject",
          "Returns BOSSResult + routing; emits SCORED event.",
        ],
        [
          "GET /v1/score/{intent_id}/explain",
          "-",
          "Returns sub-component breakdown for a previously scored intent.",
        ],
      ],
      [2800, 2100, 4460],
    ),
    h3("15.3 Exceptions and receipts"),
    buildTable(
      ["Path", "Body", "Notes"],
      [
        [
          "POST /v1/exceptions",
          "{intent_id, result_id, alternatives?}",
          "Builds ExceptionPacket; emits EXCEPTION_RAISED.",
        ],
        [
          "POST /v1/receipts",
          "{packet_id, director_id, decision, ...}",
          "Writes DecisionReceipt; emits DECISION_RECORDED.",
        ],
      ],
      [2800, 3000, 3560],
    ),
    h3("15.4 Configuration and graph"),
    buildTable(
      ["Path", "Body", "Notes"],
      [
        ["GET /v1/config/tiers", "-", "Current TierConfig."],
        [
          "PUT /v1/config/tiers",
          "TierConfigRequest",
          "Author + reason required; emits CONFIG_CHANGED.",
        ],
        ["GET /v1/graph/frameworks", "-", "List regulatory frameworks."],
        [
          "GET /v1/graph/dimensions",
          "-",
          "Framework attribution per dimension.",
        ],
        ["GET /v1/graph/ping", "-", "Health-check graph backend."],
        ["GET /v1/flightrecorder", "-", "Tail events (query: since, limit)."],
      ],
      [2800, 2100, 4460],
    ),
  ];
}

// ---------------------------------------------------------------------------
// Section 16 - Appendix B: Glossary
// ---------------------------------------------------------------------------

function glossarySection() {
  const terms = [
    ["ADAM", "Autonomy Doctrine & Architecture Model — the broader framework BOSS lives inside."],
    ["Adapter", "Thin module translating a framework's native payload into an IntentObject."],
    ["BOSS", "The scoring and routing engine documented here."],
    ["Composite", "The 0–100 weighted average of dimension scores after modifiers."],
    ["Critical Override", "Modifier that prevents a single catastrophic dimension from being diluted."],
    ["Decision Receipt", "Hash-chained director signature over an exception decision."],
    ["Doctrine", "The published, versioned policy bundle the engine enforces against."],
    ["Exception Economy", "The ADAM workflow that turns exceptions into routed approvals."],
    ["Flight Recorder", "Append-only SHA-256 hash chain of engine events."],
    ["Intent Object", "Canonical JSON payload BOSS scores — the wire format for every request."],
    ["Modifier", "Named adjustment applied to the composite (critical override, non-idempotent, cap)."],
    ["Non-Idempotent", "An action that cannot be rolled back; triggers +15 composite penalty."],
    ["OHSHAT", "Operational Hell, Send Humans — Act Today. The top escalation tier."],
    ["Priority Tier", "Fixed six-level scale (Top..Very Low) used for dimension weighting."],
    ["SOAP", "Safe & Optimum Autonomous Performance. The lowest escalation tier."],
    ["Tier Config", "Director-approved mapping of each dimension to a Priority Tier."],
  ];

  return [
    h1("16. Appendix B — Glossary and acronyms"),
    buildTable(
      ["Term", "Definition"],
      terms,
      [2000, 7360],
    ),
  ];
}

// ---------------------------------------------------------------------------
// Final section - Licence and version
// ---------------------------------------------------------------------------

function colophon() {
  return [
    h1("17. Colophon"),
    p(
      strong("Engine version: "),
      code("boss-engine 3.2.0"),
    ),
    p(
      strong("Schema version: "),
      code("ADAM Intent Object v1.0"),
    ),
    p(
      strong("License: "),
      t("Apache License 2.0. Full text in LICENSE; security disclosures in SECURITY.md."),
    ),
    p(
      strong("Contact: "),
      t("boss@adam.dev (non-sensitive) / "),
      code("security@adam.dev"),
      t(" (coordinated disclosure, PGP key in SECURITY.md)."),
    ),
    p(
      "This manual was built from the source tree at git revision ",
      code("HEAD"),
      " and mirrors the OpenAPI spec shipping with that build. For the authoritative contract, pull ",
      code("/v1/openapi.json"),
      " from a running instance.",
    ),
  ];
}

// ---------------------------------------------------------------------------
// Document assembly
// ---------------------------------------------------------------------------

const sections = [
  { children: cover() },
  {
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({
        children: [
          new Paragraph({
            border: {
              bottom: {
                style: BorderStyle.SINGLE,
                size: 6,
                color: ACCENT,
                space: 1,
              },
            },
            tabStops: [
              { type: TabStopType.RIGHT, position: TabStopPosition.MAX },
            ],
            children: [
              new TextRun({
                text: "BOSS Engine Reference Manual — ADAM Book v0.2 (BOSS v3.2)",
                color: MUTED,
                font: FONT,
                size: SMALL_SIZE,
              }),
              new TextRun({
                text: "\tADAM Component",
                color: MUTED,
                font: FONT,
                size: SMALL_SIZE,
              }),
            ],
          }),
        ],
      }),
    },
    footers: {
      default: new Footer({
        children: [
          new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun({
                text: "Page ",
                color: MUTED,
                font: FONT,
                size: SMALL_SIZE,
              }),
              new TextRun({
                children: [PageNumber.CURRENT],
                color: MUTED,
                font: FONT,
                size: SMALL_SIZE,
              }),
              new TextRun({
                text: " of ",
                color: MUTED,
                font: FONT,
                size: SMALL_SIZE,
              }),
              new TextRun({
                children: [PageNumber.TOTAL_PAGES],
                color: MUTED,
                font: FONT,
                size: SMALL_SIZE,
              }),
            ],
          }),
        ],
      }),
    },
    children: [
      ...tocSection(),
      ...executiveSummary(),
      ...adamContext(),
      ...architecture(),
      ...dimensionsSection(),
      ...formulaSection(),
      ...routerSection(),
      ...exceptionSection(),
      ...apiSection(),
      ...graphSection(),
      ...governanceSection(),
      ...deploySection(),
      ...adapterSection(),
      ...examplesSection(),
      ...opsSection(),
      ...restReference(),
      ...glossarySection(),
      ...colophon(),
    ],
  },
];

const doc = new Document({
  creator: "ADAM BOSS Engine",
  title: "BOSS Engine Reference Manual — ADAM Book v0.2",
  description:
    "Reference manual for the ADAM BOSS AI Governance & Risk Engine, ADAM Book v0.2, BOSS Score v3.2 (Priority Tier Edition).",
  styles: {
    default: {
      document: { run: { font: FONT, size: BODY_SIZE } },
    },
    paragraphStyles: [
      {
        id: "Heading1",
        name: "Heading 1",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 36, bold: true, font: FONT, color: BRAND },
        paragraph: {
          spacing: { before: 360, after: 220 },
          outlineLevel: 0,
        },
      },
      {
        id: "Heading2",
        name: "Heading 2",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 28, bold: true, font: FONT, color: BRAND },
        paragraph: {
          spacing: { before: 280, after: 160 },
          outlineLevel: 1,
        },
      },
      {
        id: "Heading3",
        name: "Heading 3",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 24, bold: true, font: FONT, color: ACCENT },
        paragraph: {
          spacing: { before: 220, after: 120 },
          outlineLevel: 2,
        },
      },
    ],
  },
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [
          {
            level: 0,
            format: LevelFormat.BULLET,
            text: "\u2022",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } },
          },
        ],
      },
      {
        reference: "numbers",
        levels: [
          {
            level: 0,
            format: LevelFormat.DECIMAL,
            text: "%1.",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } },
          },
        ],
      },
    ],
  },
  sections,
});

const outPath = process.argv[2] || "BOSS-Engine-Reference-Manual.docx";
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(outPath, buf);
  console.log(`Wrote ${outPath} (${buf.length} bytes)`);
});
