/*
 * BOSS AI Governance & Risk Engine — Reference Manual (v3.2)
 *
 * Single-file docx-js builder. Produces a publication-ready Word
 * document covering architecture, formulas, API reference, adapters,
 * deployment, operations, and compliance mapping.
 */

"use strict";

const fs = require("fs");
const path = require("path");

const docxLib = "/usr/local/lib/node_modules_global/lib/node_modules/docx";
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
  PageOrientation,
  LevelFormat,
  TabStopType,
  TabStopPosition,
  HeadingLevel,
  BorderStyle,
  WidthType,
  ShadingType,
  VerticalAlign,
  PageNumber,
  PageBreak,
  TableOfContents,
  ExternalHyperlink,
  InternalHyperlink,
  Bookmark,
} = require(docxLib);

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PAGE = { width: 12240, height: 15840 };
const MARGIN = { top: 1080, right: 1080, bottom: 1080, left: 1080 }; // ~0.75"
const CONTENT_WIDTH = PAGE.width - MARGIN.left - MARGIN.right;

const COLOR = {
  ink: "1F2937",
  mute: "4B5563",
  accent: "0F766E", // teal (ADAM palette)
  accentAlt: "1D4ED8",
  border: "D1D5DB",
  fillHead: "E0F2F1",
  fillRow: "F3F4F6",
  codeBg: "F9FAFB",
  codeFrame: "D1D5DB",
  warn: "B45309",
};

const FONT = { body: "Calibri", mono: "Consolas" };

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const border = {
  top: { style: BorderStyle.SINGLE, size: 4, color: COLOR.border },
  bottom: { style: BorderStyle.SINGLE, size: 4, color: COLOR.border },
  left: { style: BorderStyle.SINGLE, size: 4, color: COLOR.border },
  right: { style: BorderStyle.SINGLE, size: 4, color: COLOR.border },
};

const cellMargins = { top: 100, bottom: 100, left: 140, right: 140 };

function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: opts.after ?? 120, before: opts.before ?? 0 },
    alignment: opts.alignment,
    heading: opts.heading,
    pageBreakBefore: opts.pageBreakBefore,
    children: [
      new TextRun({
        text,
        bold: opts.bold,
        italics: opts.italics,
        size: opts.size,
        color: opts.color,
        font: opts.font,
      }),
    ],
  });
}

function mix(runs, opts = {}) {
  return new Paragraph({
    spacing: { after: opts.after ?? 120, before: opts.before ?? 0 },
    alignment: opts.alignment,
    children: runs,
  });
}

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    pageBreakBefore: true,
    spacing: { before: 240, after: 180 },
    children: [new TextRun({ text, bold: true })],
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 120 },
    children: [new TextRun({ text, bold: true })],
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 180, after: 100 },
    children: [new TextRun({ text, bold: true })],
  });
}

function bullet(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "bullets", level },
    spacing: { after: 80 },
    children: [new TextRun({ text })],
  });
}

function number(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "numbers", level },
    spacing: { after: 80 },
    children: [new TextRun({ text })],
  });
}

function code(text) {
  // Render a monospace block inside a single-cell bordered table.
  return new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: [CONTENT_WIDTH],
    rows: [
      new TableRow({
        children: [
          new TableCell({
            borders: {
              top: { style: BorderStyle.SINGLE, size: 4, color: COLOR.codeFrame },
              bottom: { style: BorderStyle.SINGLE, size: 4, color: COLOR.codeFrame },
              left: { style: BorderStyle.SINGLE, size: 4, color: COLOR.codeFrame },
              right: { style: BorderStyle.SINGLE, size: 4, color: COLOR.codeFrame },
            },
            width: { size: CONTENT_WIDTH, type: WidthType.DXA },
            shading: { fill: COLOR.codeBg, type: ShadingType.CLEAR },
            margins: { top: 120, bottom: 120, left: 180, right: 180 },
            children: text.split("\n").map(
              (line) =>
                new Paragraph({
                  spacing: { after: 0 },
                  children: [
                    new TextRun({
                      text: line.length ? line : " ",
                      font: FONT.mono,
                      size: 18, // 9pt — keeps long lines on page
                      color: COLOR.ink,
                    }),
                  ],
                })
            ),
          }),
        ],
      }),
    ],
  });
}

function headerCell(text, width) {
  return new TableCell({
    borders: border,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: COLOR.fillHead, type: ShadingType.CLEAR },
    margins: cellMargins,
    verticalAlign: VerticalAlign.CENTER,
    children: [
      new Paragraph({
        spacing: { after: 0 },
        children: [new TextRun({ text, bold: true, color: COLOR.ink })],
      }),
    ],
  });
}

function cell(text, width, opts = {}) {
  return new TableCell({
    borders: border,
    width: { size: width, type: WidthType.DXA },
    shading: opts.fill ? { fill: opts.fill, type: ShadingType.CLEAR } : undefined,
    margins: cellMargins,
    verticalAlign: VerticalAlign.CENTER,
    children: (Array.isArray(text) ? text : [text]).map((line) =>
      new Paragraph({
        spacing: { after: 0 },
        children: [
          new TextRun({
            text: line,
            bold: opts.bold,
            font: opts.mono ? FONT.mono : undefined,
            size: opts.mono ? 18 : undefined,
          }),
        ],
      })
    ),
  });
}

function tableOf(headers, rows, colWidths) {
  const totalWidth = colWidths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: totalWidth, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map((h, i) => headerCell(h, colWidths[i])),
      }),
      ...rows.map((row, idx) =>
        new TableRow({
          children: row.map((txt, i) =>
            cell(txt, colWidths[i], {
              fill: idx % 2 === 1 ? COLOR.fillRow : undefined,
            })
          ),
        })
      ),
    ],
  });
}

function blank(after = 120) {
  return new Paragraph({ spacing: { after }, children: [new TextRun("")] });
}

function hr() {
  return new Paragraph({
    spacing: { before: 80, after: 80 },
    border: {
      bottom: { style: BorderStyle.SINGLE, size: 6, color: COLOR.accent, space: 1 },
    },
    children: [new TextRun({ text: "" })],
  });
}

// ---------------------------------------------------------------------------
// Document body
// ---------------------------------------------------------------------------

const sections = [];

// ---- Title page --------------------------------------------------------------
sections.push(
  p("ADAM Autonomy Doctrine & Architecture Model", {
    bold: true,
    size: 28,
    color: COLOR.accent,
    alignment: AlignmentType.CENTER,
    after: 80,
  }),
  p("BOSS AI Governance & Risk Engine", {
    bold: true,
    size: 56,
    color: COLOR.ink,
    alignment: AlignmentType.CENTER,
    after: 80,
  }),
  p("Reference Manual", {
    bold: true,
    size: 40,
    color: COLOR.mute,
    alignment: AlignmentType.CENTER,
    after: 600,
  }),
  p("Engine v3.2.0 — BOSS Formulas v3.2 — ADAM reference v1.6", {
    italics: true,
    alignment: AlignmentType.CENTER,
    color: COLOR.mute,
    after: 240,
  }),
  p("A standalone implementation of the ADAM BOSS scoring, Exception", {
    alignment: AlignmentType.CENTER,
    after: 0,
  }),
  p("Economy, and Flight Recorder, independent of any specific agent", {
    alignment: AlignmentType.CENTER,
    after: 0,
  }),
  p("framework — Azure AI Foundry, LangGraph, OpenAI Agents, CrewAI.", {
    alignment: AlignmentType.CENTER,
    after: 600,
  }),
  hr(),
  p("Michael Herchenbach — ADAM Author", {
    alignment: AlignmentType.CENTER,
    bold: true,
    after: 0,
  }),
  p("Updated 22 April 2026", {
    alignment: AlignmentType.CENTER,
    color: COLOR.mute,
    after: 240,
  }),
);

// ---- Table of Contents ------------------------------------------------------
sections.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    pageBreakBefore: true,
    spacing: { before: 240, after: 180 },
    children: [new TextRun({ text: "Table of Contents", bold: true })],
  }),
  new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-3" }),
);

// ---- Part I: Foundations ---------------------------------------------------
sections.push(h1("1. Foundations"));
sections.push(h2("1.1 About this document"));
sections.push(
  p(
    "This reference manual describes the BOSS AI Governance & Risk Engine — a standalone Python service that implements the ADAM Business Operations Sovereignty Score. It covers the scoring formulas, REST API, data graph, framework adapters, deployment artifacts, and compliance mapping. A reader should leave with enough context to deploy the engine in any environment that supports a Linux container runtime and a Kubernetes-compatible scheduler."
  )
);
sections.push(
  p(
    "The document is organised so that the earliest parts are the most doctrinal: the formulas, the composite, the SOAP→OHSHAT routing. Later parts are operational: how to run the engine, how to attach it to an agent framework, how to keep the Flight Recorder intact."
  )
);

sections.push(h2("1.2 What the BOSS Engine is"));
sections.push(
  p(
    "BOSS is a single responsibility: given a proposed agentic action — an intent — score it across seven doctrinal dimensions, route it to an escalation tier, and record the decision in a hash-chained audit log. Nothing more. The engine deliberately does not make the action happen; that is the agent framework's job. BOSS decides whether the action should happen, and who needs to authorise it if it should not be executed unattended."
  )
);
sections.push(
  p(
    "This boundary is load-bearing. Any organisation can run BOSS in front of Azure AI Foundry, LangGraph, OpenAI Agents, or CrewAI without touching the framework's runtime. The adapters translate each framework's native tool-call shape into an ADAM Intent Object and submit it to BOSS. The agent only proceeds when BOSS decides the action is within the SOAP band (autonomous) or MODERATE (logged but autonomous)."
  )
);

sections.push(h2("1.3 Design principles"));
sections.push(
  bullet(
    "Doctrine first. Every score is a projection of the seven BOSS dimensions, never a heuristic."
  )
);
sections.push(
  bullet(
    "Evidence always. Every decision emits a Flight Recorder event; every event is hash-chained; every chain is verifiable."
  )
);
sections.push(
  bullet(
    "Framework-agnostic. The core has zero imports from LangGraph, Azure AI, OpenAI, or CrewAI. Adapters live outside the core."
  )
);
sections.push(
  bullet(
    "Graceful degradation. Neo4j is optional. Without it, the engine runs against an in-memory graph — perfect for local development and CI."
  )
);
sections.push(
  bullet(
    "Deterministic. The same intent + tier config always produces the same score. No randomness, no model calls inside BOSS itself."
  )
);

sections.push(h2("1.4 What BOSS is NOT"));
sections.push(
  p(
    "BOSS is not an agent. It does not call tools, does not generate text, and does not learn. Its only outputs are a BOSSResult, an ExceptionPacket, a DecisionReceipt, and a FlightRecorderEvent."
  )
);
sections.push(
  p(
    "BOSS is not a replacement for legal review. It is a projection of doctrine onto a numeric scale so a human director can make a decision quickly and with evidence. If the director disagrees with the projection, the record says so; the Flight Recorder captures the decision and the reason."
  )
);
sections.push(
  p(
    "BOSS does not persist intents for you. A production deployment should ship Flight Recorder events to a SIEM, receipts to a write-once store, and scored intents to whatever system of record is already in play. The engine makes these streams exist — retention and analytics live elsewhere."
  )
);

// ---- Part II: BOSS Formulas v3.2 -------------------------------------------
sections.push(h1("2. BOSS Score Formulas v3.2"));

sections.push(h2("2.1 The seven dimensions"));
sections.push(
  p(
    "BOSS scores every intent along seven dimensions. Each dimension is anchored to at least one public framework so the score can be defended to an auditor without recourse to proprietary methodology."
  )
);
sections.push(
  tableOf(
    ["Dimension", "Anchoring frameworks", "What it measures"],
    [
      [
        "Security",
        "NIST CSF 2.0, CVSS 4.0, MITRE ATT&CK",
        "Prompt-injection risk, CVE exposure, observed tactics.",
      ],
      [
        "Sovereignty",
        "SEAL, EU data-residency rules",
        "Data residency, cross-border transfers, lawful basis.",
      ],
      [
        "Financial",
        "FAIR, COSO ERM",
        "Revenue/cost projections, SLE × ARO vs. risk appetite.",
      ],
      [
        "Regulatory",
        "EU AI Act, GDPR, DORA, NIS2",
        "Applicable regulations, control pass rate, severity of findings.",
      ],
      [
        "Reputational",
        "RepTrak, RepRisk, SASB",
        "RepTrak delta, material topics touched, ESG severity.",
      ],
      [
        "Rights",
        "ISO 31000, NIST AI RMF",
        "Authorization certainty, ownership, consent lineage.",
      ],
      [
        "Doctrinal",
        "ISO/IEC 42001, US EO 14110, UK DSIT",
        "Alignment with declared doctrine, mission fit, explicit conflicts.",
      ],
    ],
    [2400, 3200, 3760]
  )
);
sections.push(blank());

sections.push(h2("2.2 Priority Tier weighting"));
sections.push(
  p(
    "Each dimension is assigned to one of six Priority Tiers. Every tier maps to a fixed numeric weight. This replaces the arbitrary decimal weights used in earlier BOSS revisions — now a director can say 'security is Top, regulatory is High' and a regulator can reproduce the contribution without knowing any implementation details."
  )
);
sections.push(
  tableOf(
    ["Priority Tier", "Weight", "Contribution (ADAM defaults)"],
    [
      ["Top", "5.0", "20.83 % (Security only)"],
      ["Very High", "4.0", "16.67 % (Sovereignty, Financial)"],
      ["High", "3.0", "12.50 % (Regulatory, Reputational, Rights)"],
      ["Medium", "2.0", "8.33 % (Doctrinal)"],
      ["Low", "1.0", "—"],
      ["Very Low", "0.5", "—"],
    ],
    [3200, 1800, 4360]
  )
);
sections.push(blank());
sections.push(
  p(
    "The only structural constraint is that exactly one dimension must carry Top. This keeps the denominator anchored and prevents the 'everything is highest priority' failure mode. ADAM's default is Security at Top — directors may override this through the /v1/config/tiers endpoint, with the change appended to the Flight Recorder as a CONFIG_CHANGED event."
  )
);

sections.push(h2("2.3 The composite formula"));
sections.push(
  p(
    "Given per-dimension scores S_d ∈ [0, 100] and tier-derived weights W_d, the composite BOSS score C is the weighted average:"
  )
);
sections.push(code("C = Σ (S_d × W_d) / Σ W_d"));
sections.push(
  p(
    "Under ADAM defaults (Σ W_d = 24), an intent with S_security = 80 and all other dimensions at 20 produces C ≈ (80·5 + 20·19) / 24 = (400 + 380) / 24 ≈ 32.5 — inside the ELEVATED tier."
  )
);
sections.push(
  p(
    "Three modifiers are then applied in a fixed order so the output is deterministic regardless of input order."
  )
);

sections.push(h3("2.3.1 Critical Dimension Override"));
sections.push(
  p(
    "If any dimension scores above 75, the composite is raised to at least (max dimension − 10). This prevents a single catastrophic risk from being diluted by six well-scored dimensions. The override never decreases the composite — it only pulls it upward."
  )
);

sections.push(h3("2.3.2 Non-Idempotent Penalty"));
sections.push(
  p(
    "If the intent is marked non-idempotent — that is, the action cannot be safely retried or undone — BOSS adds a flat +15 to the composite. The purpose is to guarantee at least one tier of escalation for anything irreversible, so that a human at least sees the decision before it becomes fact."
  )
);

sections.push(h3("2.3.3 Cap at 100"));
sections.push(
  p(
    "After override and penalty have been applied, the composite is clamped into [0, 100]. A cap_100 modifier is emitted if the raw sum exceeded 100, so the audit trail shows the amount that was clipped off."
  )
);

sections.push(h2("2.4 SOAP → OHSHAT routing"));
sections.push(
  p(
    "The composite is routed to one of five escalation tiers. The tier names are intentionally blunt — 'Safe & Optimum Autonomous Performance' at one end, 'Operational Hell, Send Humans Act Today' at the other — so that non-technical stakeholders understand the semantics without a glossary."
  )
);
sections.push(
  tableOf(
    ["Tier", "Composite range", "SLA", "Semantics"],
    [
      ["SOAP", "0 – 10", "0 min", "Execute. Autonomous."],
      ["MODERATE", "10 – 30", "0 min", "Execute, with enhanced logging."],
      ["ELEVATED", "30 – 50", "60 min", "Domain Governor reviews within one hour."],
      ["HIGH", "50 – 75", "240 min", "Director approval within four hours."],
      ["OHSHAT", "75 – 100", "15 min", "CEO + directors; safe-mode engaged."],
    ],
    [1800, 2400, 1200, 3960]
  )
);
sections.push(blank());
sections.push(
  p(
    "Boundary rule: each range is closed on the upper side. A composite that lands exactly on 30 is MODERATE, not ELEVATED. A composite that lands exactly on 75 is HIGH, not OHSHAT. The router chooses the lower tier on ties."
  )
);

sections.push(h2("2.5 Worked example — NetStreamX Amber Coast"));
sections.push(
  p(
    "NetStreamX is the fictional streaming company used as the canonical example throughout the ADAM manuscript. The 'Amber Coast' launch is a co-marketing push that takes a reality series into eight EU countries with partner platforms. It is the single best example of a realistically structured ELEVATED intent."
  )
);
sections.push(
  p(
    "The inputs (condensed): prompt-injection risk 0.08; CVE max CVSS 4.2; three cross-border transfers (all with lawful basis); revenue €42 M, cost €17.5 M, SLE €9 M, ARO 0.08, risk appetite €5 M; GDPR and EU AI Act both in scope, 43/48 controls passing, medium-severity finding still open; RepTrak delta −4; doctrine alignment 0.78; reversible."
  )
);
sections.push(
  p(
    "Under ADAM defaults, the per-dimension scores land roughly as follows (actual values depend on the calibrated scorer parameters; this is an illustrative band):"
  )
);
sections.push(
  tableOf(
    ["Dimension", "Score band", "Primary driver"],
    [
      ["Security", "10 – 20", "Moderate injection risk; no open CVE."],
      ["Sovereignty", "25 – 35", "Three cross-border transfers despite compliance."],
      ["Financial", "40 – 55", "SLE × ARO above single-loss appetite."],
      ["Regulatory", "45 – 60", "Open medium finding under GDPR + EU AI Act."],
      ["Reputational", "35 – 50", "RepTrak delta plus media-ethics topic."],
      ["Rights", "10 – 20", "Consent lineage verified; some ownership uncertainty."],
      ["Doctrinal", "15 – 25", "Alignment adequate, mission fit good."],
    ],
    [2400, 2000, 4960]
  )
);
sections.push(blank());
sections.push(
  p(
    "Composite lands inside 30 – 50 → tier ELEVATED. The Exception Economy triggers a Domain Governor review with a 60-minute SLA. The exception packet carries 'Financial', 'Regulatory', and 'Reputational' as the three named drivers, alongside two alternatives: 'Launch in four countries instead of eight' (projected composite ≈ 28, would drop to MODERATE) and 'Delay launch until open finding closed' (projected composite ≈ 22)."
  )
);
sections.push(
  p(
    "The director signs APPROVE_WITH_CONSTRAINTS: EU residency only, €10 M spend cap, open finding tracked. Receipt, decision, and constraints are hash-chained into the Flight Recorder, the Critical Dimension Override does not fire (no dimension above 75), and the engine's composite_final is recorded alongside the director's human decision. This round-trip is a unit-tested invariant — test_api_receipts.py walks it end-to-end."
  )
);

// ---- Part III: Architecture ------------------------------------------------
sections.push(h1("3. Architecture"));
sections.push(h2("3.1 System map"));
sections.push(
  p(
    "The engine is a single Python package exposing four logical subsystems through a narrow FastAPI interface."
  )
);
sections.push(
  tableOf(
    ["Component", "Package", "Responsibility"],
    [
      [
        "Scoring Core",
        "boss_core",
        "Pydantic schemas, dimension scorers, composite formula, tier config.",
      ],
      [
        "REST API",
        "boss_api",
        "FastAPI app, routers, dependency wiring, telemetry, auth.",
      ],
      [
        "Data Graph",
        "boss_graph",
        "Cypher schema/seed, idempotent loader, GraphQL view for read-only UI.",
      ],
      [
        "Framework Adapters",
        "boss_adapters",
        "LangGraph, OpenAI Agents, AI Foundry, CrewAI, generic.",
      ],
      [
        "Evidence Console",
        "boss_console",
        "React 18 + Vite SPA, plus single-file CDN fallback.",
      ],
    ],
    [2000, 1600, 5760]
  )
);
sections.push(blank());

sections.push(h2("3.2 Data flow for one scored intent"));
sections.push(
  number("Caller POSTs an ADAM Intent Object to /v1/score.")
);
sections.push(
  number(
    "The app dispatches to each dimension scorer, producing seven DimensionScore objects."
  )
);
sections.push(
  number(
    "compute_composite weighs the seven scores against the current TierConfig, applies override + penalty + cap, and picks an EscalationTier."
  )
);
sections.push(
  number(
    "A BOSSResult is assembled and a SCORED event is appended to the Flight Recorder, hash-chained to the prior event."
  )
);
sections.push(
  number(
    "The router returns the BOSSResult to the caller. If the tier is ELEVATED or higher, the caller typically POSTs /v1/exceptions to generate an ExceptionPacket."
  )
);
sections.push(
  number(
    "When the director resolves the exception, /v1/receipts signs and appends a DecisionReceipt. The Flight Recorder chain stays intact."
  )
);

sections.push(h2("3.3 Flight Recorder and hash chain"));
sections.push(
  p(
    "Each event carries: event_id, event_type, timestamp, signer, prior_hash, payload, and event_hash. The hash is SHA-256 over the concatenation of the prior hash and a canonical JSON serialisation of the envelope (keys sorted, no whitespace). The first event links to GENESIS_HASH (64 zeros)."
  )
);
sections.push(
  p(
    "Because each event commits to the entire prior chain, any retroactive edit — a payload tweak, a deletion, a reorder — breaks verification. FlightRecorder.verify() walks the chain and raises IntegrityError on the first mismatch. The default JsonlSink stores events as JSON Lines for local dev; production deployments replace it with a Postgres- or SIEM-backed sink."
  )
);
sections.push(code(
  "def hash_event(prior_hash: str, payload: dict[str, Any]) -> str:\n" +
    '    """Return hex SHA-256 over (prior_hash || canonical(payload))."""\n' +
    "    hasher = hashlib.sha256()\n" +
    "    hasher.update(prior_hash.encode(\"utf-8\"))\n" +
    "    hasher.update(_canonical_bytes(payload))\n" +
    "    return hasher.hexdigest()"
));

sections.push(h2("3.4 Graph model"));
sections.push(
  p(
    "The BOSS Data Graph encodes the seven dimensions, the frameworks that anchor each one, and the controls/regulations each framework exposes. It lives in Neo4j when one is available; otherwise boss_core.graph_client.InMemoryGraph offers a compatible subset for tests and local runs. The loader (python -m boss_graph.loader) is idempotent — running it twice is safe."
  )
);
sections.push(
  tableOf(
    ["Node label", "Purpose"],
    [
      ["Framework", "A published framework (NIST CSF 2.0, EU AI Act, GDPR, …)."],
      ["Dimension", "One of the seven BOSS dimensions."],
      ["Control", "A specific control or article referenced by a framework."],
      ["Regulation", "A top-level regulation (GDPR, DORA, NIS2, …)."],
      ["TierAssignment", "Snapshot of a director-approved tier config."],
    ],
    [3000, 6360]
  )
);
sections.push(blank());

// ---- Part IV: REST API Reference -------------------------------------------
sections.push(h1("4. REST API Reference"));
sections.push(h2("4.1 Versioning and auth"));
sections.push(
  p(
    "The API is versioned with a path prefix — /v1 by default, override with BOSS_API_PREFIX. Every non-health endpoint accepts an optional bearer token; when BOSS_AUTH_ENABLED=true the token is required and must match one of BOSS_ADMIN_TOKENS (or be a valid JWT signed by BOSS_JWT_SECRET)."
  )
);
sections.push(
  p(
    "The OpenAPI schema is served at /v1/openapi.json and the interactive docs at /v1/docs (Swagger UI) and /v1/redoc. Both are disabled in production by setting BOSS_DOCS_ENABLED=false."
  )
);

sections.push(h2("4.2 Health, readiness, version, metrics"));
sections.push(
  tableOf(
    ["Method", "Path", "Purpose"],
    [
      ["GET", "/v1/healthz", "Liveness probe. Always 200 if the process is up."],
      [
        "GET",
        "/v1/readyz",
        "Readiness probe. Returns Flight Recorder head hash + graph healthcheck.",
      ],
      ["GET", "/v1/version", "Engine version, BOSS formula version, ADAM reference."],
      ["GET", "/v1/metrics", "Prometheus text-format metrics."],
    ],
    [1200, 3000, 5160]
  )
);
sections.push(blank());

sections.push(h2("4.3 POST /v1/intents"));
sections.push(
  p(
    "Register an intent without scoring it. Used when a framework wants to record its intent before a slow tool finishes producing inputs. The payload is an ADAM Intent Object; the response is {intent_id, status: 'received'}. An INTENT_RECEIVED Flight Recorder event is appended."
  )
);

sections.push(h2("4.4 POST /v1/score"));
sections.push(
  p(
    "The primary endpoint. Accepts an Intent Object and returns a BOSSResult. Appends a SCORED event."
  )
);
sections.push(code(
  "POST /v1/score HTTP/1.1\n" +
    "Authorization: Bearer <token>\n" +
    "Content-Type: application/json\n\n" +
    "{\n" +
    "  \"schema_version\": \"1.0\",\n" +
    "  \"source\": {\"user_id\": \"agent.launch.amber_coast\", \"role\": \"system\"},\n" +
    "  \"headline\": \"Launch Amber Coast EU campaign\",\n" +
    "  \"is_non_idempotent\": false,\n" +
    "  \"dimension_inputs\": {\n" +
    "    \"security\": {\"prompt_injection_risk\": 0.08, \"cve_exposure_max_cvss\": 4.2, \"mitre_tactics_detected\": 0},\n" +
    "    \"...\": \"...\"\n" +
    "  }\n" +
    "}"
));
sections.push(
  p(
    "A successful response contains the per-dimension scores, the composite (raw and final), every modifier that fired, and the escalation tier. GET /v1/score/{intent_id}/explain returns the Flight Recorder trail for an intent — useful for the Evidence Console's 'receipt drill-down' view."
  )
);

sections.push(h2("4.5 POST /v1/exceptions"));
sections.push(
  p(
    "Generate an ExceptionPacket for an intent that routes above SOAP. If the intent would route to SOAP the endpoint returns 409 — SOAP actions need no exception. The body is {intent, alternatives}; alternatives are optional."
  )
);
sections.push(
  p(
    "The ExceptionPacket carries: packet_id, intent_id, result_id, escalation_tier, summary, drivers, required_approvers, alternatives, response_sla_minutes, recommended_alternative. An EXCEPTION_RAISED event is appended. The director UI typically displays this alongside the BOSS composite and per-dimension breakdown."
  )
);

sections.push(h2("4.6 POST /v1/receipts"));
sections.push(
  p(
    "Sign a director decision. Input: packet_id, intent_id, result_id, director_id, decision (APPROVE / APPROVE_WITH_CONSTRAINTS / REJECT / DEFER / ESCALATE), selected_alternative, applied_constraints, director_note. Output: a DecisionReceipt with both prior_hash (the Flight Recorder head at signing time) and receipt_hash (SHA-256 over the receipt's canonical form)."
  )
);
sections.push(
  p(
    "A DECISION_RECORDED event is appended to the Flight Recorder. The chain now includes INTENT_RECEIVED → SCORED → EXCEPTION_RAISED → DECISION_RECORDED for every governed action."
  )
);

sections.push(h2("4.7 Tier configuration"));
sections.push(
  p(
    "GET /v1/config/tiers returns the currently active TierConfig. PUT /v1/config/tiers replaces it; the body must include an author and optional reason. A CONFIG_CHANGED event is appended. Zero-Top or multi-Top requests are rejected at 422."
  )
);

sections.push(h2("4.8 Graph introspection"));
sections.push(
  p(
    "GET /v1/graph/frameworks returns the registered frameworks. GET /v1/graph/dimensions returns each dimension's framework attribution. GET /v1/graph/ping returns whether the graph backend is reachable (in-memory always, Neo4j only when configured)."
  )
);

sections.push(h2("4.9 Flight Recorder tail"));
sections.push(
  p(
    "GET /v1/flightrecorder returns the most recent events, newest first. Disabled by default; set BOSS_FLIGHT_RECORDER_TAIL=1 to enable. Parameters: event_type (filter), limit (1 – 2000, default 200). Production deployments typically route operator traffic through a SIEM instead of this endpoint."
  )
);

// ---- Part V: Adapters -------------------------------------------------------
sections.push(h1("5. Framework Adapters"));
sections.push(
  p(
    "Adapters live in boss_adapters. Each one translates a framework-native action into a BOSS payload and calls evaluate_payload. Every adapter returns an AdapterDecision with a single high-level action — ALLOW, ALLOW_WITH_LOGGING, ESCALATE, BLOCK, or EMERGENCY_STOP — plus the full BOSSResult for callers that want the breakdown."
  )
);

sections.push(h2("5.1 LangGraph — deep integration"));
sections.push(
  p(
    "LangGraph is the reference integration. Four entry points:"
  )
);
sections.push(
  bullet(
    "normalize_tool_call(call) — turns a LangChain ToolCall dict into an IntentObject."
  )
);
sections.push(
  bullet(
    "score_tool_call(call) — runs the whole scoring pipeline and returns an AdapterDecision."
  )
);
sections.push(
  bullet(
    "boss_guard_node(...) — factory returning a LangGraph node callable. Drop it between the planner and the tool executor. Raises BossGovernanceError on OHSHAT; on ESCALATE the optional on_escalate callback fires."
  )
);
sections.push(
  bullet(
    "BossGuardTool(wrapped) — wraps any LangChain BaseTool so its _run and _arun consult BOSS first. Requires langchain-core."
  )
);
sections.push(code(
  "from langgraph.graph import StateGraph\n" +
    "from boss_adapters.langgraph_adapter import boss_guard_node\n\n" +
    "graph = StateGraph(AgentState)\n" +
    "graph.add_node(\"plan\", planner)\n" +
    "graph.add_node(\"boss_guard\", boss_guard_node(tenant=\"netstreamx\"))\n" +
    "graph.add_node(\"tools\", ToolNode(my_tools))\n" +
    "graph.add_edge(\"plan\", \"boss_guard\")\n" +
    "graph.add_edge(\"boss_guard\", \"tools\")"
));

sections.push(h2("5.2 OpenAI Agents (Assistants / Responses)"));
sections.push(
  p(
    "Thin translator. normalize_function_call accepts either the Responses-style top-level function_call dict ({type, name, arguments, call_id}) or the Assistants-style nested function dict ({id, function: {name, arguments}}). score_function_call runs the full pipeline and returns an AdapterDecision; gate submit_tool_outputs on its decision.action."
  )
);

sections.push(h2("5.3 Azure AI Foundry"));
sections.push(
  p(
    "Thin translator with a Foundry-specific courtesy: if the payload carries an evaluators block (PII, Indirect Attack, Protected Material, Hate/Unfairness, Groundedness), the adapter promotes those numbers into the BOSS security / rights / reputational dimension inputs. data_residency and region hints flow through to sovereignty. A tool can then rely on the evaluator already run by Foundry without re-scoring from scratch."
  )
);

sections.push(h2("5.4 CrewAI"));
sections.push(
  p(
    "Thin translator for both CrewAI Tasks and Tools. A Task becomes a BOSS payload whose headline is the task description truncated; a Tool becomes a BOSS payload whose headline is the tool name. boss_inputs may still be passed through the task/tool args for explicit dimension inputs."
  )
);

sections.push(h2("5.5 Generic / custom frameworks"));
sections.push(
  p(
    "boss_adapters.base.evaluate_payload is the public entry point. Any framework that can produce a payload dict with a headline (or a tool/name) can use it directly — framework-specific adapters just pre-shape the dict before handing it over."
  )
);

// ---- Part VI: Evidence Console ---------------------------------------------
sections.push(h1("6. Evidence Console"));
sections.push(
  p(
    "The Evidence Console is a thin React 18 SPA that reads the BOSS API. Two distributions are shipped:"
  )
);
sections.push(
  bullet(
    "Vite + TypeScript + Tailwind project under boss_console/ — npm ci && npm run dev to develop, npm run build to emit static assets served by the FastAPI app at /console."
  )
);
sections.push(
  bullet(
    "boss_console/standalone.html — a single file that loads React, ReactDOM, Babel-standalone, Recharts, and Tailwind Play CDN. Useful for air-gapped demos or environments where a Node build step is undesirable."
  )
);
sections.push(
  p(
    "Both versions cover the same four panels: Dashboard (tier distribution, composite histogram, latency), Scoring (submit an intent, see the per-dimension radar, log output), Frameworks (what each dimension is anchored to), Flight Recorder (reverse-chronological event tail, integrity badge). The Vite build adds a typed client, theming, keyboard navigation, and a settings drawer for BOSS_API_URL plus the bearer token (stored in sessionStorage, never localStorage)."
  )
);

// ---- Part VII: Deployment --------------------------------------------------
sections.push(h1("7. Deployment"));

sections.push(h2("7.1 Python package"));
sections.push(
  p(
    "pyproject.toml declares the package. Install with pip install . for runtime, or pip install -e .[dev] for a full developer setup. The optional extras [neo4j], [adapters], [metrics], [test], [lint] map exactly to the dependency groups used by the build."
  )
);
sections.push(code(
  "pip install boss-engine\n" +
    "pip install boss-engine[neo4j,metrics]\n" +
    "pip install boss-engine[dev]   # for contributors"
));

sections.push(h2("7.2 Docker"));
sections.push(
  p(
    "A multi-stage Dockerfile ships with the repository:"
  )
);
sections.push(
  bullet(
    "ui-builder — Node 20 Alpine. Runs npm ci && npm run build in boss_console to produce the Vite bundle."
  )
);
sections.push(
  bullet(
    "python-builder — python:3.12-slim. Builds a wheel via python -m build."
  )
);
sections.push(
  bullet(
    "runtime — python:3.12-slim with tini, non-root UID 1000, read-only rootfs friendly, HEALTHCHECK hitting /v1/healthz. CMD is uvicorn boss_api.app:create_app --factory --workers 2."
  )
);
sections.push(code(
  "docker build -t boss-engine:3.2.0 .\n" +
    "docker run --rm -p 8080:8080 \\\n" +
    "  -e BOSS_AUTH_ENABLED=true \\\n" +
    "  -e BOSS_ADMIN_TOKENS=$(openssl rand -hex 32) \\\n" +
    "  -v $(pwd)/recorder:/var/lib/boss \\\n" +
    "  boss-engine:3.2.0"
));

sections.push(h2("7.3 docker-compose"));
sections.push(
  p(
    "docker-compose.yml declares five services behind profiles so a developer can pick the subset they need:"
  )
);
sections.push(
  tableOf(
    ["Service", "Profile", "Purpose"],
    [
      ["engine", "(default)", "FastAPI app with read-only rootfs."],
      ["console", "console", "Node dev server at :5173."],
      ["neo4j", "graph, full", "Neo4j 5.20 with persistent volume."],
      [
        "graph-seed",
        "graph, full",
        "Runs python -m boss_graph.loader once against Neo4j.",
      ],
      [
        "langgraph-demo",
        "adapters, full",
        "Example LangGraph agent wired through the engine.",
      ],
    ],
    [2400, 1800, 5160]
  )
);
sections.push(blank());
sections.push(code(
  "docker compose up engine                    # minimal\n" +
    "docker compose --profile full up            # everything"
));

sections.push(h2("7.4 Kubernetes"));
sections.push(
  p(
    "deploy/k8s/ carries plain manifests for operators who don't use Helm. Twelve files cover namespace, service account, role-based access, pod security admission (restricted), deployment, service, network policy, horizontal pod autoscaler, pod disruption budget, service monitor for Prometheus, and a job that runs the graph loader."
  )
);
sections.push(
  p(
    "The Pod Security Admission setting is restricted — the deployment runs as UID 1000 with seccomp RuntimeDefault, all capabilities dropped, allowPrivilegeEscalation false, readOnlyRootFilesystem true. An emptyDir volume at /var/lib/boss holds the JsonlSink between restarts (use a PVC if the sink is meant to survive pod eviction)."
  )
);

sections.push(h2("7.5 Helm chart"));
sections.push(
  p(
    "deploy/helm/boss-engine/ is a Helm v2 chart. values.yaml exposes every tunable: image repository, tag, resources, HPA, PDB, probes, environment, optional Neo4j StatefulSet, optional ServiceMonitor, optional TLS via cert-manager. helm lint + kubeconform run in CI against both Kubernetes 1.28 and 1.29."
  )
);
sections.push(code(
  "helm install boss-engine ./deploy/helm/boss-engine \\\n" +
    "  --namespace boss --create-namespace \\\n" +
    "  --set auth.adminTokens={your-token} \\\n" +
    "  --set neo4j.enabled=true"
));

sections.push(h2("7.6 Configuration reference"));
sections.push(
  tableOf(
    ["Variable", "Default", "Purpose"],
    [
      ["BOSS_ENV", "development", "Free-form environment label (test, staging, prod)."],
      ["BOSS_API_PREFIX", "/v1", "Path prefix for every endpoint."],
      ["BOSS_LOG_LEVEL", "INFO", "Python log level."],
      ["BOSS_CORS_ORIGINS", "*", "Comma-separated list of allowed origins."],
      ["BOSS_AUTH_ENABLED", "false", "Turn on bearer-token auth."],
      ["BOSS_ADMIN_TOKENS", "(empty)", "Comma-separated list of admin tokens."],
      ["BOSS_JWT_SECRET", "(empty)", "JWT HMAC secret, if using JWT auth."],
      [
        "BOSS_FLIGHT_RECORDER_PATH",
        "/var/lib/boss/flight-recorder.jsonl",
        "JsonlSink path.",
      ],
      [
        "BOSS_FLIGHT_RECORDER_TAIL",
        "0",
        "Enable the /flightrecorder tail endpoint.",
      ],
      ["BOSS_NEO4J_URI", "(empty)", "If set, use Neo4j instead of InMemoryGraph."],
      ["BOSS_METRICS_ENABLED", "true", "Expose Prometheus metrics at /v1/metrics."],
      ["BOSS_OTEL_ENDPOINT", "(empty)", "Send traces/metrics to an OTLP endpoint."],
    ],
    [3400, 2800, 3160]
  )
);
sections.push(blank());

// ---- Part VIII: Operations -------------------------------------------------
sections.push(h1("8. Operations"));
sections.push(h2("8.1 Logging"));
sections.push(
  p(
    "boss_api.telemetry.configure_logging sets up structured JSON logging on stdout. Every request is logged with trace_id, span_id, status_code, path, and latency_ms. The Flight Recorder is intentionally separate: business events go to the recorder, operational events go to stdout."
  )
);
sections.push(h2("8.2 Metrics"));
sections.push(
  p(
    "Prometheus metrics are emitted at /v1/metrics: boss_score_total{tier=}, boss_exception_total{tier=}, boss_score_latency_seconds, boss_flight_recorder_events_total. A ServiceMonitor manifest ships with the Helm chart."
  )
);
sections.push(h2("8.3 Tracing"));
sections.push(
  p(
    "Set BOSS_OTEL_ENDPOINT to an OTLP collector URL and the engine emits per-request spans plus a custom span per scoring pipeline. Trace IDs are also logged on every request so operators can jump from a log line to a trace without manual correlation."
  )
);
sections.push(h2("8.4 Integrity monitoring"));
sections.push(
  p(
    "A simple operational pattern: every N minutes, a sidecar calls FlightRecorder.verify() and publishes the result as a Prometheus counter. Any increment of boss_flight_recorder_integrity_break_total is a page. In production the recorder is backed by a SIEM or Postgres write-once table — the in-process sink is a fallback."
  )
);
sections.push(h2("8.5 Scaling"));
sections.push(
  p(
    "The scoring pipeline is stateless; horizontal scaling is uncomplicated provided every pod writes to a shared, append-only Flight Recorder sink. The bottleneck in high-volume deployments is the sink, not the scoring. Partition by tenant and assign each tenant a dedicated sink for the cleanest story."
  )
);

// ---- Part IX: Compliance Mapping -------------------------------------------
sections.push(h1("9. Compliance Mapping"));
sections.push(
  p(
    "BOSS is not a compliance certification. It is an implementation of a risk-projection doctrine that aligns with the following frameworks — every dimension is attributed to at least one of them so an auditor can cross-reference."
  )
);
sections.push(
  tableOf(
    ["Framework", "Aligned BOSS dimension(s)", "How"],
    [
      [
        "NIST CSF 2.0",
        "Security, Regulatory",
        "Govern-Identify-Protect-Detect-Respond-Recover functions contribute to security scoring.",
      ],
      [
        "CVSS 4.0",
        "Security",
        "cve_exposure_max_cvss is scored against the v4 base vector.",
      ],
      [
        "MITRE ATT&CK",
        "Security",
        "Tactic and technique detection count feeds the security score.",
      ],
      [
        "SEAL",
        "Sovereignty",
        "Data residency and cross-border transfer features map to SEAL metrics.",
      ],
      [
        "FAIR",
        "Financial",
        "SLE × ARO vs. risk appetite drives the loss-exposure score.",
      ],
      [
        "COSO ERM",
        "Financial, Doctrinal",
        "Enterprise risk context sets the appetite-versus-exposure frame.",
      ],
      [
        "EU AI Act",
        "Regulatory, Rights",
        "Risk-category mapping influences the regulatory score; Article 14 human-oversight obligations anchor Rights.",
      ],
      [
        "GDPR",
        "Regulatory, Rights, Sovereignty",
        "Lawful basis, consent lineage, data subject rights.",
      ],
      [
        "DORA",
        "Regulatory",
        "Operational resilience checks for financial-services actions.",
      ],
      [
        "NIS2",
        "Regulatory",
        "Incident reporting thresholds feed the regulatory score.",
      ],
      [
        "ISO 31000",
        "Rights, Doctrinal",
        "Reference framing for ADAM risk definitions.",
      ],
      [
        "NIST AI RMF",
        "Rights, Doctrinal",
        "Govern-Map-Measure-Manage anchors the AI-specific risk treatment.",
      ],
      [
        "ISO/IEC 42001",
        "Doctrinal",
        "AI management-system controls align with declared doctrine checks.",
      ],
      [
        "RepRisk / RepTrak",
        "Reputational",
        "Delta and incident severity drive the reputational score.",
      ],
      ["SASB", "Reputational", "Material-topic attribution."],
      [
        "US EO 14110 / UK DSIT",
        "Doctrinal",
        "Policy alignment and safety commitments.",
      ],
    ],
    [2400, 2400, 4560]
  )
);
sections.push(blank());
sections.push(
  p(
    "Every framework above is registered in the graph (GET /v1/graph/frameworks) with a key, publisher, URL, and version field. The Evidence Console's 'Frameworks' panel is a direct read of this graph."
  )
);

// ---- Part X: Development ---------------------------------------------------
sections.push(h1("10. Development"));
sections.push(h2("10.1 Test suite"));
sections.push(
  p(
    "The tests/ directory holds 14 test files covering 109 test functions across 23 classes. The most load-bearing invariants — one-Top rule, weighted-mean identity, Critical Dimension Override, Non-Idempotent Penalty, cap-at-100, hash-chain tamper detection, Amber Coast ELEVATED assertion, OHSHAT emergency-stop — are each covered by at least one named test. tests/TESTING.md lists every invariant with a file + test-name pointer."
  )
);
sections.push(code(
  "make check            # ruff + mypy + pytest unit lane\n" +
    "make test-integration # includes Neo4j + schemathesis\n" +
    "make check-all        # everything, the full CI matrix"
));
sections.push(h2("10.2 Linting and typing"));
sections.push(
  p(
    "Ruff is configured in pyproject.toml with the rule families E, F, W, I, UP, B, C4, SIM, RUF, ASYNC, S, PTH, TID, T20, N. Mypy runs in strict mode; tests are allowed untyped defs as a practical concession. Bandit runs in CI against the runtime packages (not tests)."
  )
);
sections.push(h2("10.3 Release"));
sections.push(
  p(
    "Three workflows under .github/workflows/:"
  )
);
sections.push(
  bullet("ci.yml — lint, test matrix (py3.11, py3.12), schemathesis, security (bandit + pip-audit + trivy), console build, helm lint + kubeconform, docker buildx build.")
);
sections.push(
  bullet(
    "release.yml — publishes the container image (amd64 + arm64 with SBOM and provenance), the Helm chart to GHCR, and the wheel to the configured PyPI target."
  )
);
sections.push(
  bullet(
    "codeql.yml — CodeQL for Python + JavaScript/TypeScript."
  )
);
sections.push(
  p(
    "Semantic versioning: the major version tracks BOSS_FORMULA_VERSION, the minor tracks API-compatible feature additions, the patch tracks bug-fixes. A formula bump is a major version bump by definition — the numbers computed by v3.x will differ from v4.x because the weights differ."
  )
);

// ---- Appendices -------------------------------------------------------------
sections.push(h1("Appendix A. Glossary"));
sections.push(
  tableOf(
    ["Term", "Meaning"],
    [
      [
        "ADAM",
        "Autonomy Doctrine & Architecture Model — the book-level doctrine this engine implements.",
      ],
      [
        "BOSS",
        "Business Operations Sovereignty Score — the composite produced by this engine.",
      ],
      [
        "Intent Object",
        "ADAM v1.0 data structure describing a proposed agentic action.",
      ],
      ["Composite", "Weighted average of the seven dimension scores."],
      [
        "Tier",
        "Priority tier (Top, Very High, High, Medium, Low, Very Low) assigned to a dimension.",
      ],
      [
        "Escalation tier",
        "SOAP, MODERATE, ELEVATED, HIGH, OHSHAT — where the composite routes.",
      ],
      [
        "Exception Packet",
        "Structured escalation artifact handed to directors with alternatives and SLAs.",
      ],
      [
        "Decision Receipt",
        "Hash-chained artifact produced when a director resolves an exception.",
      ],
      [
        "Flight Recorder",
        "Append-only, hash-chained audit log. One line per governed event.",
      ],
      [
        "Director",
        "Human in the loop authorised to resolve an ADAM exception (domain governor, compliance, CEO, …).",
      ],
      [
        "Doctrine",
        "The declared constraints and mission set the engine scores actions against.",
      ],
      [
        "Tenant",
        "A business unit or customer with an isolated Flight Recorder stream and tier config.",
      ],
    ],
    [2400, 6960]
  )
);
sections.push(blank());

sections.push(h1("Appendix B. File inventory"));
sections.push(
  p(
    "High-level directory map of the repository. Full listings are in the source tree."
  )
);
sections.push(
  tableOf(
    ["Path", "Contents"],
    [
      ["boss_core/", "Schemas, scorers, composite, router, flight recorder, frameworks."],
      ["boss_api/", "FastAPI app, routers, config, deps, security, telemetry."],
      ["boss_graph/", "Cypher schema, seed, loader, GraphQL view."],
      ["boss_adapters/", "LangGraph deep adapter + OpenAI / Foundry / CrewAI thin translators + generic."],
      ["boss_console/", "React 18 Vite project + single-file standalone.html."],
      ["deploy/k8s/", "Kubernetes manifests (12 files, PSA restricted)."],
      ["deploy/helm/boss-engine/", "Helm v2 chart (14 templates)."],
      ["tests/", "109 pytest functions + Hypothesis properties + Schemathesis fuzz."],
      ["docs/", "This reference manual and its build script."],
      [".github/", "CI workflows, issue templates, PR template, Dependabot, CodeQL."],
      ["Dockerfile, docker-compose.yml, Makefile, pyproject.toml", "Top-level build + dev ergonomics."],
    ],
    [3000, 6360]
  )
);
sections.push(blank());

sections.push(h1("Appendix C. Acceptance checklist"));
sections.push(
  p(
    "Reviewers — including CODEX — should be able to answer yes to each of the following before the engine ships."
  )
);
sections.push(
  bullet(
    "pyproject.toml defines a single, installable Python package with pinned but non-exotic dependencies."
  )
);
sections.push(
  bullet(
    "ruff, mypy --strict, and pytest (unit lane) all pass locally and in CI."
  )
);
sections.push(
  bullet(
    "Bandit, pip-audit, and Trivy produce no high-severity findings against the runtime image."
  )
);
sections.push(
  bullet(
    "The Amber Coast intent (tests/fixtures/amber_coast_intent.json) routes to ELEVATED via POST /v1/score."
  )
);
sections.push(
  bullet(
    "The OHSHAT variant (security.prompt_injection_risk = 0.85, CVSS 9.6, non-idempotent) routes to OHSHAT, triggers both critical_dimension_override and non_idempotent_penalty modifiers, and causes boss_guard_node to raise BossGovernanceError."
  )
);
sections.push(
  bullet(
    "FlightRecorder.verify() is green after every test file in the tests/ directory executes end-to-end."
  )
);
sections.push(
  bullet(
    "helm lint + kubeconform succeed against Kubernetes 1.28 and 1.29."
  )
);
sections.push(
  bullet(
    "The engine runs end-to-end under docker compose up with no Neo4j (InMemoryGraph fallback)."
  )
);
sections.push(
  bullet(
    "The LangGraph example under examples/ runs through the deep adapter without LangChain-Core being vendored into boss_core."
  )
);
sections.push(
  bullet(
    "The GitHub Actions matrix publishes a signed multi-arch container image and a Helm chart on tag."
  )
);

// ---------------------------------------------------------------------------
// Document assembly
// ---------------------------------------------------------------------------

const doc = new Document({
  creator: "Michael Herchenbach",
  title: "BOSS AI Governance & Risk Engine — Reference Manual v3.2",
  description:
    "Comprehensive reference manual for the ADAM BOSS AI Governance & Risk Engine: formulas, architecture, API, adapters, deployment, compliance mapping.",
  styles: {
    default: {
      document: { run: { font: FONT.body, size: 22 } }, // 11pt
    },
    paragraphStyles: [
      {
        id: "Heading1",
        name: "Heading 1",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 40, bold: true, color: COLOR.accent, font: FONT.body },
        paragraph: { spacing: { before: 240, after: 180 }, outlineLevel: 0 },
      },
      {
        id: "Heading2",
        name: "Heading 2",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 30, bold: true, color: COLOR.ink, font: FONT.body },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 1 },
      },
      {
        id: "Heading3",
        name: "Heading 3",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 26, bold: true, color: COLOR.mute, font: FONT.body },
        paragraph: { spacing: { before: 160, after: 80 }, outlineLevel: 2 },
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
            text: "•",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 540, hanging: 360 } } },
          },
          {
            level: 1,
            format: LevelFormat.BULLET,
            text: "◦",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 900, hanging: 360 } } },
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
            style: { paragraph: { indent: { left: 540, hanging: 360 } } },
          },
        ],
      },
    ],
  },
  sections: [
    {
      properties: {
        page: { size: PAGE, margin: MARGIN },
      },
      headers: {
        default: new Header({
          children: [
            new Paragraph({
              spacing: { after: 0 },
              tabStops: [
                { type: TabStopType.RIGHT, position: TabStopPosition.MAX },
              ],
              children: [
                new TextRun({
                  text: "BOSS AI Governance & Risk Engine — Reference Manual",
                  color: COLOR.mute,
                  size: 18,
                }),
                new TextRun({ text: "\tADAM v1.6 · BOSS v3.2", color: COLOR.mute, size: 18 }),
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
              spacing: { before: 0 },
              children: [
                new TextRun({ text: "Page ", color: COLOR.mute, size: 18 }),
                new TextRun({ children: [PageNumber.CURRENT], color: COLOR.mute, size: 18 }),
                new TextRun({ text: " of ", color: COLOR.mute, size: 18 }),
                new TextRun({
                  children: [PageNumber.TOTAL_PAGES],
                  color: COLOR.mute,
                  size: 18,
                }),
              ],
            }),
          ],
        }),
      },
      children: sections,
    },
  ],
});

const outArg = process.argv[2] || path.join(__dirname, "boss-engine-reference-manual.docx");
Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(outArg, buffer);
  console.log("Wrote", outArg, "(", buffer.length, "bytes )");
});
