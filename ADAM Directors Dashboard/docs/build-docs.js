/* Generates the ADAM Directors Dashboard reference documentation.
 * Run: node build-docs.js
 * Output: ADAM Directors Dashboard — Reference.docx
 */
const fs   = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, PageOrientation, LevelFormat,
  HeadingLevel, BorderStyle, WidthType, ShadingType, TableOfContents,
  PageNumber, PageBreak, TabStopType, TabStopPosition
} = require("/tmp/node_modules/docx");

/* ------------------------- helpers ------------------------- */
const P = (text, opts = {}) => new Paragraph({
  children: [new TextRun({ text, ...opts.run })],
  spacing: { after: 120, ...opts.spacing },
  ...opts.para
});
const H1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1,
  children: [new TextRun({ text })], spacing: { before: 360, after: 180 } });
const H2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2,
  children: [new TextRun({ text })], spacing: { before: 280, after: 140 } });
const H3 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_3,
  children: [new TextRun({ text })], spacing: { before: 220, after: 100 } });

const bullet = (text) => new Paragraph({
  numbering: { reference: "bullets", level: 0 },
  children: [new TextRun({ text })],
  spacing: { after: 80 }
});
const numbered = (text) => new Paragraph({
  numbering: { reference: "numbers", level: 0 },
  children: [new TextRun({ text })],
  spacing: { after: 80 }
});

const code = (text) => new Paragraph({
  children: [new TextRun({ text, font: "Consolas", size: 20, color: "263046" })],
  shading: { fill: "F1F4FA", type: ShadingType.CLEAR },
  spacing: { after: 120 }
});

const rule = () => new Paragraph({
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "A5B4CE", space: 6 } },
  spacing: { before: 120, after: 240 }
});

const border = { style: BorderStyle.SINGLE, size: 4, color: "BFC8D9" };
const borders = { top: border, bottom: border, left: border, right: border };

function tableCell(text, opts = {}) {
  return new TableCell({
    borders,
    width: { size: opts.w || 3120, type: WidthType.DXA },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    shading: opts.header ? { fill: "1a2438", type: ShadingType.CLEAR } : undefined,
    children: [new Paragraph({
      children: [new TextRun({
        text,
        bold: !!opts.header,
        color: opts.header ? "FFFFFF" : "1a2030",
        size: opts.header ? 20 : 20
      })]
    })]
  });
}

function table(headers, rows, widths) {
  const total = widths.reduce((a,b)=>a+b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map((h,i) => tableCell(h, { header: true, w: widths[i] }))
      }),
      ...rows.map(r => new TableRow({
        children: r.map((c,i) => tableCell(String(c), { w: widths[i] }))
      }))
    ]
  });
}

/* ------------------------- document ------------------------ */
const doc = new Document({
  creator: "ADAM",
  title: "ADAM Directors Dashboard — Reference",
  description: "Reference guide for the director-facing dashboard.",
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } }, // 11pt
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run:  { size: 32, bold: true, font: "Arial", color: "121a2b" },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run:  { size: 26, bold: true, font: "Arial", color: "1a2438" },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run:  { size: 22, bold: true, font: "Arial", color: "263046" },
        paragraph: { spacing: { before: 220, after: 100 }, outlineLevel: 2 } }
    ]
  },
  numbering: {
    config: [
      { reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "numbers",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    headers: {
      default: new Header({ children: [new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: "ADAM Directors Dashboard — Reference", size: 18, color: "6a7693" })]
      })]})
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        children: [
          new TextRun({ text: "© ADAM / NetStreamX sovereign test instance", size: 18, color: "6a7693" }),
          new TextRun({ text: "\t", size: 18 }),
          new TextRun({ text: "Page ", size: 18, color: "6a7693" }),
          new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "6a7693" })
        ],
        tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }]
      })]})
    },
    children: [
      /* ---------- COVER ---------- */
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 2000, after: 200 },
        children: [new TextRun({ text: "ADAM", bold: true, size: 96, color: "5aa2ff" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 120 },
        children: [new TextRun({ text: "Directors Dashboard", bold: true, size: 56, color: "121a2b" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 400 },
        children: [new TextRun({ text: "Reference Guide  ·  Version 1.0", size: 26, color: "6a7693" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({
          text: "The director-facing control surface for the Autonomous Decisioning & Adjudication Mesh.",
          italics: true, size: 22, color: "263046"
        })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 1800 },
        children: [new TextRun({ text: "NetStreamX sovereign test instance", size: 20, color: "6a7693" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "ADAM v1.4  ·  BOSS v3.2  ·  Doctrine 1.0.0-test", size: 20, color: "6a7693" })]
      }),
      new Paragraph({ children: [new PageBreak()] }),

      /* ---------- TOC ---------- */
      H1("Contents"),
      new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-3" }),
      new Paragraph({ children: [new PageBreak()] }),

      /* ---------- 1. PURPOSE ---------- */
      H1("1. Purpose"),
      P("The ADAM Directors Dashboard is the director-facing control surface for the 81-agent ADAM mesh. It exists because ADAM enforces a hard separation between \"humans stating intent\" and \"the system deciding how\", and directors need a single, calm view that surfaces every signal they are accountable for without ever inviting them into the workflow itself."),
      P("It consolidates, on one page:", { spacing: { after: 80 } }),
      bullet("The live health of all 81 agents organised by class and sub-group."),
      bullet("Every exception packet currently awaiting a director signature, with full BOSS v3.2 dimensional breakdown and Explain-Back narrative."),
      bullet("A conversational intent interface (the Intent Interpretation Agent) that turns plain language into structured Intent Objects."),
      bullet("A conversational explain-back interface (the Explain-Back Agent) that replays the Flight Recorder in plain English."),
      bullet("Telemetry for the four Digital Twins that ADAM consults before, during, and after every material action."),
      bullet("A rolling tail of the tamper-evident Flight Recorder for at-a-glance situational awareness."),
      P("It is a single-page application with zero runtime dependencies — vanilla HTML, CSS, and ES6 — and works offline from the file system as well as when served alongside the ADAM deployment stack."),
      rule(),

      /* ---------- 2. DOCTRINAL GROUNDING ---------- */
      H1("2. Doctrinal grounding"),
      P("This dashboard is not a management console. Two sentences from the ADAM Governance Charter frame it:"),
      new Paragraph({
        indent: { left: 720, right: 720 },
        spacing: { before: 120, after: 200 },
        border: { left: { style: BorderStyle.SINGLE, size: 18, color: "5aa2ff", space: 8 } },
        children: [new TextRun({ text: "\"Directors manage exceptions and innovation — not workflows. Directors never touch execution.\"", italics: true, size: 24, color: "1a2438" })]
      }),
      P("Every design choice in this dashboard follows from that. There is no \"execute\" button. There is no workflow editor. There is no agent-level override. The only affordances a director has are: state an intent, read the exceptions queued for them, decide on those exceptions (approve / modify / reject), and ask for an explanation of anything in the audit trail."),
      P("Governors never appear as clickable units. Twins are shown only as usage telemetry. Agents are shown as tiles whose colour reflects their state, because a director should care about the shape of the mesh — not the individual agents inside it."),
      rule(),

      /* ---------- 3. LAYOUT ---------- */
      H1("3. Screen layout"),
      P("A four-quadrant grid above 1024 px; a stacked single column below it. Each quadrant is independently resizable via the standard browser corner-drag handle, and a density slider in the toolbar scales every font system-wide so the dashboard remains usable on anything from a 13-inch laptop to a 4 K wall display."),
      H2("Quadrant 1 — Mesh Status"),
      P("Top-left. A grid of 81 agent tiles grouped by the seven canonical classes (Human Interface, Domain Governors, Orchestration, Corporate Work Groups, AI-Centric Division, Digital Twins, Meta-Governance). Sub-groups inside Corporate Work Groups and AI-Centric Division are rolled up so a director can see, for example, that Security & Trust sub-group is trending red without opening anything. Under the mesh: the five-director roster with their pending-queue counts, BOSS routing distribution for the last 24 hours, and a rolling Flight Recorder tail."),
      H2("Quadrant 2 — Director Approval Queue"),
      P("Top-right. The only clickable action surface. Every exception packet awaiting a director's signature is rendered as a row with its tier pill, composite BOSS score, owning director, time-sensitivity, confidence, and the triggers that caused escalation. The three actions (Approve / Modify / Reject) are inline on every row, but the directed flow is to click the row, review the full packet in the modal, then sign from there."),
      H2("Quadrant 3 — Intent Interpretation Agent (hi-intent)"),
      P("Bottom-left. A chat-like input where a director states intent in plain language. The response bubble renders the BOSS v3.2 dimensional breakdown, composite score, routing tier, and — if the intent escalates — a confirmation that a packet has been queued to the responsible director."),
      H2("Quadrant 4 — Explain-Back Agent (hi-explain) + Digital Twin usage"),
      P("Bottom-right. A chat-like input that takes an intent_id (or a prefix, or a natural-language question) and returns a plain-English narrative reconstruction of every Flight Recorder event bound to it. Below the chat, a compact four-card grid of Digital Twin consultation telemetry (calls / 24 h, latency, live simulations, divergence)."),
      rule(),

      /* ---------- 4. THE THREE INTERFACE AGENTS ---------- */
      H1("4. The three human-interface agents"),
      P("ADAM's doctrine requires all human interaction to flow through three named agents. The dashboard surfaces each of them in a purpose-built panel."),
      table(
        ["Agent", "Panel style", "Purpose"],
        [
          ["hi-intent (Intent Interpretation Agent)", "Conversational", "Turns plain-language intent into a structured Intent Object; returns BOSS score + tier."],
          ["hi-explain (Explain-Back Agent)", "Conversational", "Replays Flight Recorder events tied to an intent_id as plain-English narrative."],
          ["orch-exception + hi-gateway (Exception surface)", "Clickable queue", "Lists exception packets awaiting signature; Approve / Modify / Reject writes a Flight Recorder event."]
        ],
        [2880, 1600, 4880]
      ),
      P("The distinction is deliberate: the first two invite free-form engagement, the third deliberately does not. An exception is not a conversation — it is a directed decision with an SLA, and the UI enforces that framing."),
      rule(),

      /* ---------- 5. BOSS ROUTING ---------- */
      H1("5. BOSS v3.2 routing model"),
      P("Every intent is scored against seven weighted dimensions, summed with an optional non-idempotent penalty and a critical-dimension override, and routed by the composite to one of five tiers."),
      H2("5.1 Dimension weights"),
      table(
        ["Dimension", "Weight", "Priority tier"],
        [
          ["security_impact", "5.0", "Top"],
          ["sovereignty_action", "4.0", "Very High"],
          ["financial_exposure", "4.0", "Very High"],
          ["regulatory_impact", "3.0", "High"],
          ["reputational_risk", "3.0", "High"],
          ["rights_certainty", "3.0", "High"],
          ["doctrinal_alignment", "2.0", "Medium"]
        ],
        [4680, 1560, 3120]
      ),
      H2("5.2 Tier routing and colour doctrine"),
      table(
        ["Tier", "Score", "Dashboard colour", "Routing"],
        [
          ["SOAP", "0–10",  "Green",    "Autonomous. Minimal logging."],
          ["MODERATE","11–30","Sage",   "Autonomous. Enhanced logging, post-hoc review queued."],
          ["ELEVATED","31–50","Amber",  "Paused. Domain Governor review."],
          ["HIGH",  "51–75", "Orange",  "Director approval required. 4-hour SLA."],
          ["OHSHAT","76–100","Red",     "CEO + all directors. Immediate. Safe-mode invoked."]
        ],
        [1560, 1200, 2000, 4600]
      ),
      H2("5.3 Agent status mapping"),
      P("Agent tiles reuse the same palette at the individual-agent level:"),
      bullet("Green — agent is executing autonomously within its authority envelope."),
      bullet("Orange — agent has emitted an exception packet and is paused pending resolution."),
      bullet("Red — agent is unreachable or has been safe-moded. Pulses to draw attention."),
      rule(),

      /* ---------- 6. DIRECTORS ---------- */
      H1("6. Directors rendered by default"),
      P("The dashboard ships configured for the 5-director constitution defined in docs/directors.json. It adapts to 6- or 7-director configurations without code changes when those directors appear in the configuration."),
      table(
        ["Director", "Owned BOSS dimensions", "Default cap / authority"],
        [
          ["CEO",             "— (final arbiter across all)",              "$5,000. Doctrine-root. OHSHAT escalation."],
          ["CFO",             "financial_exposure",                         "$500. Financial Governor. Throttle financial autonomy."],
          ["Legal Director",  "regulatory_impact, rights_certainty",        "No cap. Legal & Compliance Governor. Novel interpretation."],
          ["Market Director", "reputational_risk",                          "$2,500. Market & Ecosystem Governor. Brand / crisis comms."],
          ["CISO",            "security_impact, sovereignty_action",        "No cap. Security Governor. Safe-mode / kill-switch."]
        ],
        [2040, 3240, 4080]
      ),
      P("When a director selects their row in the roster (or chooses from the filter dropdown), the queue narrows to the exceptions whose owning dimension they hold."),
      rule(),

      /* ---------- 7. DATA SOURCES ---------- */
      H1("7. Data sources — the three-tier auto-fallback"),
      P("The dashboard probes three data sources in priority order on every load and every refresh. It renders through the same code path regardless of source, so behaviour is identical in all three modes; only the top-bar \"Mode\" chip changes."),
      H2("7.1 Live mode"),
      P("Tried first. A GET to http://localhost:8300/health. If it returns 200, the dashboard flips into Live mode and subsequently uses:"),
      code("GET  /pending                → list queued exception packets"),
      code("POST /intent                 → submit a plain-language intent"),
      code("POST /approve/{intent_id}    → director approval"),
      code("POST /reject/{intent_id}     → director rejection"),
      code("GET  /explain/{intent_id}    → Explain-Back narrative replay"),
      H2("7.2 File mode"),
      P("Tried if Live fails. The dashboard fetches the deployment JSON directly:"),
      bullet("../../deployment/NetStreamX/docs/directors.json"),
      bullet("../../deployment/NetStreamX/agents/agent-registry.json"),
      bullet("../../deployment/NetStreamX/boss/boss-config.json"),
      P("File mode works when the dashboard is served by any HTTP host that can also serve the deployment directory at the expected relative path. It does not work from file:// because browsers block cross-directory file fetches."),
      H2("7.3 Demo mode"),
      P("Final fallback. data/demo-data.js ships a deterministic snapshot that mirrors every schema the live / file modes produce. This is what you see when the dashboard is opened with no backend and no file server — it is suitable for demos, screenshots, training, and offline use, and it does not pretend to be live data (the Mode chip clearly says \"Demo mode\")."),
      rule(),

      /* ---------- 8. USAGE BY ROLE ---------- */
      H1("8. Usage by director role"),
      H2("8.1 CEO"),
      P("See everything. Owned queue: OHSHAT escalations, doctrine-root mutations, and final-arbiter items where two domains conflict. Use the top-bar filter to see \"All directors\" and spot early signals in sub-groups outside your direct ownership."),
      H2("8.2 CFO"),
      P("Filter queue to \"CFO\". You will see every item where financial_exposure is the dominant dimension. Default delegation cap in the test instance is $500 — anything higher routes here by design."),
      H2("8.3 Legal Director"),
      P("Filter queue to \"Legal Director\". Watch for items flagged with regulatory_impact > 55 or rights_certainty < 45. Novel regulatory interpretations (e.g., unprecedented DORA or AI Act reads) cannot be self-resolved by agents and always route here."),
      H2("8.4 Market Director"),
      P("Filter queue to \"Market Director\". Marketing spend above the $2,500 test cap, brand-adjacent campaigns, and anything with reputational_risk > 40 surfaces here. In the default configuration this role also holds product-innovation authority until a CPO is seated."),
      H2("8.5 CISO"),
      P("Filter queue to \"CISO\". Every OHSHAT with a security trigger routes here first. The kill-switch / safe-mode authority lives behind a confirmation dialog (future release). In the test instance, CISO also owns sovereignty_action — anything touching data egress or residency."),
      rule(),

      /* ---------- 9. TYPICAL WORKFLOWS ---------- */
      H1("9. Typical workflows"),
      H2("9.1 Signing an exception"),
      numbered("Panel 2 (top-right) shows the queue sorted by composite score descending."),
      numbered("Click the row whose intent_id you want to review."),
      numbered("The modal opens with: original intent text, dimension bars, alternatives with projected scores, triggers, and the Explain-Back narrative."),
      numbered("Click Approve & Sign, Modify, or Reject."),
      numbered("The dashboard calls POST /approve/{id} or /reject/{id} in live mode, removes the row, toasts confirmation, and appends a director_approval / director_modified / director_rejection event to the Flight Recorder tail in Panel 1."),
      H2("9.2 Testing what a proposed intent would score"),
      numbered("Use Panel 3 (Intent Interpretation Agent) at the bottom-left."),
      numbered("Type a one-sentence description (e.g., \"Approve a $3,200 paid-social burst for Gaming Q3\")."),
      numbered("Check the \"irreversible\" box if the action cannot be undone — this adds the +15 non-idempotent penalty."),
      numbered("The response bubble shows the dimensional breakdown and tier. If it is ELEVATED / HIGH / OHSHAT, a packet is also queued (in live mode) for the owning director."),
      H2("9.3 Asking \"why did that happen?\""),
      numbered("Copy the intent_id (or its first 8 characters) from the queue row, the Flight Recorder tail, or a prior conversation."),
      numbered("Paste it into Panel 4 (Explain-Back Agent) and submit."),
      numbered("In Live mode the dashboard calls GET /explain/{id} which replays every Flight Recorder event tied to the intent. In demo / file mode, the narrative is reconstructed from the local packet."),
      rule(),

      /* ---------- 10. COMPONENT REFERENCE ---------- */
      H1("10. Component reference"),
      table(
        ["Element", "Location", "Behaviour"],
        [
          ["Mode chip",               "Top bar",       "Live / File / Demo. Dot colour matches mode."],
          ["Refresh button",          "Top bar",       "Re-probes the data source chain, refreshes all panels."],
          ["Export button",           "Top bar",       "window.print() with a dashboard-friendly print stylesheet."],
          ["Density slider",          "Toolbar",       "Scales all fonts system-wide between 85% and 125%."],
          ["Director filter",         "Toolbar",       "Narrows approval queue to a specific director."],
          ["Mesh group card",         "Panel 1",       "Sub-group rollups appear for Corporate WG and AI-Centric."],
          ["Agent tile",              "Panel 1",       "Hover for tooltip. Pulsing red means down."],
          ["Director card",           "Panel 1",       "Click to filter queue to that director."],
          ["BOSS routing cells",      "Panel 1",       "Rolling 24-hour counts per tier."],
          ["Flight Recorder tail",    "Panel 1",       "Newest events first. Auto-appends every poll tick."],
          ["Queue item",              "Panel 2",       "Click to open modal, or use inline buttons."],
          ["Detail modal",            "Overlay",       "Shows dimensions, alternatives, triggers, narrative. ESC closes."],
          ["Intent input",            "Panel 3",       "Enter submits. Checkbox adds +15 non-idempotent penalty."],
          ["Example chips",           "Panels 3 & 4",  "Populate the input with a pre-built scenario."],
          ["Explain-Back input",      "Panel 4",       "Accepts intent_id, prefix, or natural-language question."],
          ["Twin card",               "Panel 4",       "24h consultations, latency, live simulations, divergence."]
        ],
        [2400, 1400, 5560]
      ),
      rule(),

      /* ---------- 11. STYLE SYSTEM ---------- */
      H1("11. Style system"),
      P("The dashboard deliberately mirrors the BOSS Console palette so it sits naturally alongside the other ADAM tools. Key tokens:"),
      code(":root { --adam-ink: #0a0f1a; --adam-navy: #121a2b; --adam-navy-2: #1a2438; }"),
      code("       { --tier-soap: #2ecc71; --tier-moderate: #a8e061; }"),
      code("       { --tier-elevated: #f5b042; --tier-high: #ff8c42; --tier-ohshat: #ef4444; }"),
      P("Typography: Inter for UI, JetBrains Mono for Flight Recorder rows and score badges. Both are loaded from Google Fonts with a system-font fallback chain, so the dashboard is legible even on an air-gapped machine with no outbound network."),
      rule(),

      /* ---------- 12. RESPONSIVE ---------- */
      H1("12. Responsive behaviour"),
      table(
        ["Viewport", "Grid", "Behaviour"],
        [
          ["≥ 1440 px (director wall)",       "2 × 2",            "Quadrants widen, twin grid widens to 4 columns."],
          ["1024–1440 px (desktop)",           "2 × 2",            "Default behaviour. Sub-grids auto-fit."],
          ["768–1024 px (tablet / laptop)",   "Single column",    "Each panel full width, scroll within."],
          ["360–768 px (phone / pager)",      "Single column",    "Sub-grids collapse, tiles stay touch-friendly."]
        ],
        [3240, 2040, 4080]
      ),
      P("Additionally: every panel has native CSS resize on its bottom-right corner, and the density slider in the toolbar scales all fonts system-wide. A print stylesheet strips chrome and fits all four quadrants onto a single printed briefing page."),
      rule(),

      /* ---------- 13. ACCESSIBILITY ---------- */
      H1("13. Accessibility"),
      bullet("All inputs carry aria-label."),
      bullet("Modal declares role=\"dialog\" and aria-modal=\"true\"; focus lands on the primary action when opened."),
      bullet("Conversational logs, queue, and Flight Recorder tail declare aria-live=\"polite\"."),
      bullet("Every actionable row and tile has role=\"button\" with Enter / Space handling."),
      bullet("Colour is never the only signal — every tier pill also carries its text label; every agent status is announced in the tooltip."),
      bullet("Focus ring uses the ADAM accent colour and is visible on every focusable control."),
      bullet("All on-dark text passes WCAG AA contrast (≥ 4.5 : 1) against the ink-navy palette."),
      rule(),

      /* ---------- 14. QA ---------- */
      H1("14. Quality assurance"),
      H2("14.1 Automated smoke test"),
      P("qa/headless-smoke.js boots the page in jsdom, stubs fetch into failure so the auto-fallback lands in demo mode, and asserts 31 invariants spanning structural integrity, demo schema, per-panel rendering, queue modal flow, approve/reject state mutation, intent submission, explain-back narration, director-filter wiring, and accessibility basics. All 31 pass as of v1.0."),
      H2("14.2 Manual browser checklist"),
      P("qa/QA-Checklist.md is a 13-section manual verification list covering cold open, live handshake, every panel, responsive breakpoints, print export, and regression. Run before every release."),
      H2("14.3 Re-running"),
      code("cd qa/ && node headless-smoke.js"),
      rule(),

      /* ---------- 15. INTEGRATION ---------- */
      H1("15. Integration points"),
      H2("15.1 With the ADAM stack"),
      P("In live mode, the dashboard is served by the interface-server container (iac/compose/interface_server.py) at :8300 alongside ADAM's existing built-in UI. It replaces or augments iac/compose/static/index.html at the deployer's preference."),
      H2("15.2 With the Flight Recorder"),
      P("Approve / Reject / Modify actions do not write directly to the Flight Recorder — they call the interface-server endpoints, which in turn append WORM hash-chained events. The dashboard's local Flight Recorder tail is a read-only mirror for situational awareness."),
      H2("15.3 With OPA"),
      P("The dashboard renders evaluated policy chains when they are present in the exception packet. Policy enforcement itself remains in the Open Policy Agent container."),
      rule(),

      /* ---------- 16. ROADMAP ---------- */
      H1("16. Roadmap"),
      bullet("WebSocket live feed from the Flight Recorder, replacing the 2-second poll."),
      bullet("Ed25519 signature indicator alongside every approve / reject."),
      bullet("Twin divergence drill-down — click a twin card to see which dimensions are diverging."),
      bullet("Multi-tenant toggle in the top bar for deployments hosting multiple companies."),
      bullet("Pager-style mobile companion for after-hours OHSHAT alerts."),
      rule(),

      /* ---------- 17. APPENDIX ---------- */
      H1("17. Appendix — File manifest"),
      table(
        ["Path", "Purpose"],
        [
          ["index.html",               "Single-page app entry."],
          ["README.md",                "GitHub-facing reference."],
          ["assets/styles.css",        "All styling; ADAM palette + responsive grid."],
          ["assets/app.js",            "Controller, data-source probe, rendering."],
          ["assets/banner.svg",        "README banner."],
          ["data/demo-data.js",        "Deterministic demo dataset matching real schemas."],
          ["docs/…Reference.docx",     "This document."],
          ["qa/headless-smoke.js",     "Automated smoke test (31 assertions)."],
          ["qa/QA-Checklist.md",       "Manual browser QA checklist."],
          ["qa/report.txt",            "Latest automated run output."]
        ],
        [3480, 5880]
      )
    ]
  }]
});

Packer.toBuffer(doc).then(buf => {
  const out = path.join(__dirname, "ADAM Directors Dashboard - Reference.docx");
  fs.writeFileSync(out, buf);
  console.log("wrote", out, buf.length, "bytes");
});
