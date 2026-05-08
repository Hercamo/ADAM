/* ============================================================================
 * ADAM Directors Dashboard — Production views (v0.2)
 * ----------------------------------------------------------------------------
 * Loaded by index.html after assets/app.js. Provides four director-facing
 * read-only viewers over live ADAM data:
 *
 *   - DNA Graph viewer        (window.DirectorViews.openDnaGraph)
 *   - Flight Recorder Lifecycle (window.DirectorViews.openLifecycle)
 *   - BOSS Dimension Detail   (window.DirectorViews.openDimension)
 *   - Intent Object Detail    (window.DirectorViews.openIntentObject)
 *
 * The lifecycle viewer reads the live chain.sqlite via
 * /api/dashboard/lifecycle/<intent_id>; the dimension and DNA viewers
 * read the deployed configuration files. None of these views write.
 *
 * Cross-functionality:
 *   - Any per-dimension score (data-boss-dim) is clickable -> Dimension Detail
 *   - Any element with data-lifecycle-intent is clickable -> Lifecycle
 *   - Any element with data-iod-intent is clickable -> Intent Object Detail
 *   - The DNA Graph button on the topbar opens DNA Graph
 *   - The Intent Object Card grows two buttons: "Intent Object" and "Lifecycle"
 * ========================================================================== */

(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);

  // ------------------------------------------------------------- helpers ---
  function fetchJson(url, opts) {
    return fetch(url, opts).then(r => r.ok ? r.json() : r.json().then(j => Promise.reject(j)));
  }
  function escapeHtml(s) {
    return String(s == null ? "" : s).replace(/[&<>'"]/g, c => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
    }[c]));
  }
  function buildOverlay(id, title, sub) {
    let el = document.getElementById(id);
    if (el) return el;
    el = document.createElement("div");
    el.id = id; el.className = "vw-overlay";
    el.innerHTML = `
      <div class="vw-overlay-card">
        <div class="vw-overlay-hd">
          <h3>${escapeHtml(title)}</h3>
          <span class="vw-sub" data-sub>${escapeHtml(sub || "")}</span>
          <span class="spacer"></span>
          <button class="vw-close" type="button">Close</button>
        </div>
        <div class="vw-overlay-bd" data-body></div>
        <div class="vw-overlay-ft" data-ft></div>
      </div>`;
    document.body.appendChild(el);
    el.querySelector(".vw-close").addEventListener("click", () => el.classList.remove("open"));
    el.addEventListener("click", (e) => { if (e.target === el) el.classList.remove("open"); });
    return el;
  }

  // ------------------------------------------------------------- DNA -------
  function openDnaGraph() {
    const ov = buildOverlay("vw-dna", "DNA Graph — Company doctrine", "13 sections of the company DNA, sourced from the deployed configuration");
    const body = ov.querySelector("[data-body]");
    body.innerHTML = `<div style="color:var(--vw-mute)">Loading DNA Graph…</div>`;
    ov.classList.add("open");
    fetchJson(`/api/dashboard/dna/sections`).then(payload => {
      const sections = payload.sections || [];
      const tocHtml = sections.map(s =>
        `<button data-id="${s.id}"><span class="dna-num">§${s.id}</span> ${escapeHtml(s.title)}</button>`
      ).join("");
      body.innerHTML = `
        <div class="dna-grid">
          <div class="dna-toc" id="dna-toc">${tocHtml}</div>
          <div class="dna-section" id="dna-section"></div>
        </div>`;
      const renderSection = (sec) => {
        const subHtml = sec.subsections.map(ss => `
          <div class="dna-subsection">
            <h5>§${escapeHtml(ss.id)} ${escapeHtml(ss.title)}</h5>
            ${ss.questions.map(q => `
              <div class="dna-qa">
                <div class="dna-q"><span class="dna-id">${escapeHtml(q.id)}</span>${escapeHtml(q.q)}</div>
                <div class="dna-a">${escapeHtml(q.a)}</div>
              </div>`).join("")}
          </div>`).join("");
        $("dna-section").innerHTML = `
          <h4>§${sec.id}. ${escapeHtml(sec.title)}</h4>
          <div class="dna-summary">${escapeHtml(sec.summary)}</div>
          <div class="dna-cen-note">CORE Engine note — ${escapeHtml(sec.core_engine_note)}</div>
          ${subHtml}`;
      };
      const toc = $("dna-toc");
      toc.querySelectorAll("button").forEach(btn => btn.addEventListener("click", () => {
        toc.querySelectorAll("button").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const sec = sections.find(s => String(s.id) === btn.dataset.id);
        if (sec) renderSection(sec);
      }));
      const first = toc.querySelector("button");
      if (first) first.click();
    }).catch(err => {
      body.innerHTML = `<div style="color:var(--vw-bad)">DNA load failed: ${escapeHtml(JSON.stringify(err))}</div>`;
    });
  }

  // ------------------------------------------------------------- Lifecycle -
  function openLifecycle(intentId) {
    if (!intentId) { alert("No intent_id supplied"); return; }
    const ov = buildOverlay("vw-lc", "Flight Recorder Lifecycle",
                            `Intent ${intentId.slice(0,8)}…  ·  read from chain.sqlite`);
    const body = ov.querySelector("[data-body]");
    const ft = ov.querySelector("[data-ft]");
    body.innerHTML = `<div style="color:var(--vw-mute)">Loading lifecycle…</div>`;
    ft.innerHTML = `
      <div class="lc-modes">
        <button data-view="graphical" class="active">Graphical lifecycle</button>
        <button data-view="textual">Textual log</button>
        <button data-view="evidence">Evidence review</button>
      </div>`;
    ov.classList.add("open");
    let payload = null;
    fetchJson(`/api/dashboard/lifecycle/${encodeURIComponent(intentId)}`).then(p => {
      payload = p;
      renderView("graphical");
    }).catch(err => {
      body.innerHTML = `<div style="color:var(--vw-bad)">Lifecycle load failed: ${escapeHtml(JSON.stringify(err))}</div>`;
    });
    ft.querySelectorAll(".lc-modes button").forEach(b => b.addEventListener("click", () => {
      ft.querySelectorAll(".lc-modes button").forEach(x => x.classList.remove("active"));
      b.classList.add("active");
      renderView(b.dataset.view);
    }));

    function renderView(view) {
      if (!payload) return;
      const events = payload.events || [];
      if (events.length === 0) {
        body.innerHTML = `<div class="lc-empty">No Flight Recorder events found for this intent in chain.sqlite.</div>`;
        return;
      }
      if (view === "graphical") {
        body.innerHTML = `
          <div style="color:var(--vw-mute); margin-bottom:8px">
            ${events.length} events · earliest on the left, latest on the right · click any step for the full Flight Recorder entry.
          </div>
          <div class="lc-track">
            ${events.map(e => `
              <div class="lc-step" data-seq="${e.seq}">
                <div class="lc-num">${e.step}</div>
                <div class="lc-label">${escapeHtml(e.label)}</div>
                <div class="lc-event">${escapeHtml(e.event_type)}</div>
                <div class="lc-summary">${escapeHtml(e.summary)}</div>
                <div class="lc-agent">${escapeHtml(e.agent_id)}</div>
                <div class="lc-ts">${escapeHtml(e.ts || "")}</div>
              </div>`).join("")}
          </div>`;
        body.querySelectorAll(".lc-step").forEach(el => el.addEventListener("click", () =>
          openLifecycleEvent(intentId, parseInt(el.dataset.seq, 10))));
      } else if (view === "textual") {
        body.innerHTML = `
          <div class="lc-textual">
            <table>
              <thead><tr><th>#</th><th>Seq</th><th>TS (UTC)</th><th>Event</th><th>Agent</th><th>Summary</th></tr></thead>
              <tbody>
                ${events.map(e => `
                  <tr data-seq="${e.seq}">
                    <td>${e.step}</td><td>${e.seq}</td><td>${escapeHtml(e.ts || "")}</td>
                    <td>${escapeHtml(e.event_type)}</td><td>${escapeHtml(e.agent_id)}</td>
                    <td>${escapeHtml(e.summary)}</td>
                  </tr>`).join("")}
              </tbody>
            </table>
          </div>`;
        body.querySelectorAll("tr[data-seq]").forEach(el => el.addEventListener("click", () =>
          openLifecycleEvent(intentId, parseInt(el.dataset.seq, 10))));
      } else { // evidence
        body.innerHTML = `
          <div style="color:var(--vw-mute); margin-bottom:8px">
            Auditor / regulator view — full evidence per event.
          </div>
          <div class="lc-evidence-stack">
            ${events.map(e => `
              <div class="lc-evidence-block">
                <div class="lc-evidence-hdr">
                  <span class="pill">#${e.step}</span>
                  <b>${escapeHtml(e.event_type)}</b>
                  <span class="ts">seq ${e.seq} · ${escapeHtml(e.ts || "")}</span>
                  <button class="lc-open-card-btn" data-seq="${e.seq}">Open card</button>
                </div>
                <div style="color:var(--vw-ink); margin-bottom:6px">${escapeHtml(e.summary)}</div>
                <pre style="background:#060a14; padding:10px; border-radius:4px; max-height:160px; overflow:auto; font-size:11px;">${escapeHtml(JSON.stringify(e.evidence, null, 2))}</pre>
              </div>`).join("")}
          </div>`;
        body.querySelectorAll(".lc-open-card-btn").forEach(el => el.addEventListener("click", () =>
          openLifecycleEvent(intentId, parseInt(el.dataset.seq, 10))));
      }
    }
  }

  function openLifecycleEvent(intentId, seq) {
    const ov = buildOverlay("vw-lc-evt", "Flight Recorder entry", `Seq ${seq} · intent ${intentId.slice(0,8)}…`);
    const body = ov.querySelector("[data-body]");
    body.innerHTML = `<div style="color:var(--vw-mute)">Loading event…</div>`;
    ov.classList.add("open");
    fetchJson(`/api/dashboard/lifecycle/${encodeURIComponent(intentId)}/event/${seq}`).then(d => {
      const e = d.event;
      const proof = d.proof || {};
      body.innerHTML = `
        <div class="lc-evidence">
          <div>
            <h4 style="color:var(--vw-amber); margin:0 0 4px 0">${escapeHtml(e.event_type)}</h4>
            <div style="color:var(--vw-mute); font-size:12px; margin-bottom:8px">
              ${escapeHtml(e.label)} · ${escapeHtml(e.agent_id)} · ${escapeHtml(e.ts || "")}
            </div>
            <div style="color:var(--vw-ink); margin-bottom:10px">${escapeHtml(e.summary)}</div>
            <pre>${escapeHtml(JSON.stringify(e.evidence, null, 2))}</pre>
          </div>
          <div class="proof">
            <h4>Cryptographic proof</h4>
            <div><span class="k">Chain</span> ${escapeHtml(proof.chain)}</div>
            <div><span class="k">Key id</span> ${escapeHtml(proof.key_id)}</div>
            <div><span class="k">Algorithm</span> ${escapeHtml(proof.algorithm)}</div>
            <div><span class="k">Signature</span> ${proof.signature_present ? "present" : "absent"}</div>
            <div><span class="k">Anchor</span> ${escapeHtml(proof.anchor_id || "(rolled into next daily anchor)")}</div>
            <div><span class="k">Tamper-evident</span> ${proof.tamper_evident ? "yes" : "no"}</div>
            <div><span class="k">WORM</span> ${proof.worm_enforced ? "enforced" : "no"}</div>
            <div style="margin-top:10px; color:var(--vw-mute); font-size:11px;">
              Doctrine version ${escapeHtml(d.doctrine_version)}
            </div>
          </div>
        </div>`;
    }).catch(err => {
      body.innerHTML = `<div style="color:var(--vw-bad)">Event load failed: ${escapeHtml(JSON.stringify(err))}</div>`;
    });
  }

  // -------------------------------------------------------- Dimension Detail
  function openDimension(dim) {
    if (!dim) return;
    const ov = buildOverlay("vw-dim", "BOSS dimension detail", dim);
    const body = ov.querySelector("[data-body]");
    body.innerHTML = `<div style="color:var(--vw-mute)">Loading…</div>`;
    ov.classList.add("open");
    fetchJson(`/api/dashboard/boss/dimension/${encodeURIComponent(dim)}`).then(d => {
      const tier = (d.tier_interpretation || []).map(t =>
        `<tr><td><b>${escapeHtml(t.range)}</b></td><td>${escapeHtml(t.label)}</td><td>${escapeHtml(t.meaning)}</td></tr>`
      ).join("");
      const rules = (d.matched_rules || []);
      const rulesHtml = rules.length ? rules.map(r => `
        <div class="dim-rule">
          <b>${escapeHtml(r.id || "rule")}:</b> ${escapeHtml(r.text || "")}<br>
          <span style="color:var(--vw-mute); font-size:11px">Source: ${escapeHtml(r.source || "—")} · Scope: ${escapeHtml(r.scope || "—")}</span>
        </div>`).join("") : `<div class="dim-rule" style="border-left-color:var(--vw-mute)"><i style="color:var(--vw-mute)">No rules in rules-seed.json reference this dimension directly.</i></div>`;

      const bands = d.scoring_bands || {};
      let bandsHtml = "";
      if (bands.bands_usd && bands.bands_usd.length) {
        bandsHtml = bands.bands_usd.map(b =>
          `<div class="dim-band"><b>≤ $${b.max == null ? "∞" : b.max.toLocaleString()}</b> → score ${b.score}</div>`
        ).join("");
      } else if (bands.guide) {
        bandsHtml = `<div class="dim-band">${escapeHtml(bands.guide)}</div>`;
      } else {
        bandsHtml = `<div class="dim-band"><i style="color:var(--vw-mute)">No explicit input bands configured for this dimension.</i></div>`;
      }

      body.innerHTML = `
        <div class="dim-vw">
          <div>
            <h4 style="color:var(--vw-amber); margin:0 0 4px 0">${escapeHtml(d.label)}</h4>
            <div style="color:var(--vw-mute); margin-bottom:10px">Weight ${d.weight} (${escapeHtml(d.weight_label)}) · Owner role: ${escapeHtml(d.owner_role)}</div>
            <h5 style="color:var(--vw-ink); margin:10px 0 4px 0">Scoring bands</h5>
            ${bandsHtml}
            <h5 style="color:var(--vw-ink); margin:14px 0 4px 0">Tier interpretation</h5>
            <table class="dim-tier-table">${tier}</table>
            <h5 style="color:var(--vw-ink); margin:14px 0 4px 0">Doctrine rules referencing this dimension</h5>
            ${rulesHtml}
          </div>
          <div class="dim-meta">
            <div><span class="k">Framework</span> ${escapeHtml(d.framework)}</div>
            <div><span class="k">Doctrine</span> ${escapeHtml(d.doctrine_version)}</div>
            <div style="margin-top:14px; color:var(--vw-mute); font-size:11px;">
              The composite formula and weights live in <code>boss-config.json</code>; matched rules are read from <code>core/rules-seed.json</code>.
            </div>
          </div>
        </div>`;
    }).catch(err => {
      body.innerHTML = `<div style="color:var(--vw-bad)">Dimension load failed: ${escapeHtml(JSON.stringify(err))}</div>`;
    });
  }

  // ------------------------------------------------------- Intent Object Detail
  // Field-by-field structured view of the Intent Object backing the
  // currently selected card. Read-only; reflects whatever the existing
  // /api/dashboard/intent/<id> endpoint returns.
  const IO_FIELD_DESCRIPTIONS = {
    "intent_id":               "Globally unique UUIDv4 — every intent has exactly one.",
    "doctrine_version":        "Doctrine snapshot under which this intent was scored.",
    "timestamp":               "Wall-clock UTC time the intent was first received.",
    "source.role":             "What kind of actor produced the intent (director / executive / operator / system / customer).",
    "source.director_id":      "Owning director seat — set when the action is director-initiated or escalated.",
    "source.originating_agent_id": "Agent that emitted the intent, where applicable.",
    "desired_outcomes":        "Structured outcomes the agent is asked to produce, with success criteria.",
    "constraints":             "Preconditions agents must respect.",
    "urgency":                 "routine / elevated / critical / emergency — drives SLA timer.",
    "is_non_idempotent":       "True means software cannot reverse this action; adds +15 to BOSS composite.",
    "approval_conditions":     "Conditions under which the action may auto-execute without director sign-off.",
    "core_graph_context":      "Pointers to relevant CORE Graph context (rules, mandates, prior decisions).",
    "replay_marker":           "Set on re-runs — captures the original intent_id and doctrine_version_at_original.",
  };

  function openIntentObject(intentId) {
    if (!intentId) { alert("No intent_id supplied"); return; }
    const ov = buildOverlay("vw-iod", "Intent Object",
                            `Intent ${intentId.slice(0,8)}… · structured view of the schema-validated payload`);
    const body = ov.querySelector("[data-body]");
    body.innerHTML = `<div style="color:var(--vw-mute)">Loading intent…</div>`;
    ov.classList.add("open");
    fetchJson(`/api/dashboard/intent/${encodeURIComponent(intentId)}`).then(d => {
      const i = d.intent || {};
      const composite = d.composite || {};
      // Build a normalised set of fields from whatever the endpoint returns.
      const renderRow = (k, v, desc) => `
        <div class="iod-field">
          <div class="k">${escapeHtml(k)}</div>
          <div class="v">${escapeHtml(typeof v === "object" ? JSON.stringify(v) : String(v))}</div>
          ${desc ? `<div class="desc">${escapeHtml(desc)}</div>` : ""}
        </div>`;
      const fields = [
        ["intent_id",                 intentId],
        ["doctrine_version",          d.doctrine_version || ""],
        ["timestamp",                 i.queued_at || i.timestamp || ""],
        ["source.role",               (i.source && i.source.role) || i.role || ""],
        ["source.director_id",        i.owning_director || ""],
        ["source.originating_agent_id", (i.source && i.source.originating_agent_id) || ""],
        ["desired_outcomes",          i.desired_outcomes || (i.summary ? [{ "description": i.summary }] : [])],
        ["constraints",               i.constraints || (i.non_idempotent ? ["non_idempotent"] : [])],
        ["urgency",                   (i.tier === "OHSHAT" ? "emergency" :
                                       i.tier === "HIGH"   ? "elevated"   :
                                       i.urgency || "routine")],
        ["is_non_idempotent",         !!i.non_idempotent],
        ["replay_marker",             i.replay_marker || {}],
      ];
      const rendered = fields.map(([k, v]) => renderRow(k, v, IO_FIELD_DESCRIPTIONS[k] || "")).join("");
      body.innerHTML = `
        <div style="color:var(--vw-mute); margin-bottom:8px">
          Schema: <code>intent-object-schema.json v1.1</code> · doctrine ${escapeHtml(d.doctrine_version || "")}
        </div>
        <div class="iod-grid">
          <div class="iod-fields">${rendered}</div>
          <div>
            <h5 style="color:var(--vw-ink); margin:0 0 6px 0">Raw Intent Object payload</h5>
            <pre class="iod-raw">${escapeHtml(JSON.stringify(i, null, 2))}</pre>
            ${composite.score != null ? `
              <h5 style="color:var(--vw-ink); margin:14px 0 6px 0">Computed composite</h5>
              <pre class="iod-raw">${escapeHtml(JSON.stringify(composite, null, 2))}</pre>` : ""}
          </div>
        </div>`;
    }).catch(err => {
      body.innerHTML = `<div style="color:var(--vw-bad)">Intent load failed: ${escapeHtml(JSON.stringify(err))}</div>`;
    });
  }

  // -------------------------------------------------------- Auto-wire in DOM
  function attachClickDelegation() {
    document.body.addEventListener("click", (e) => {
      const dim = e.target.closest("[data-boss-dim]");
      if (dim) { openDimension(dim.dataset.bossDim); return; }
      const lc = e.target.closest("[data-lifecycle-intent]");
      if (lc) { openLifecycle(lc.dataset.lifecycleIntent || lc.dataset.intent || lc.dataset.intentId); return; }
      const iod = e.target.closest("[data-iod-intent]");
      if (iod) { openIntentObject(iod.dataset.iodIntent || iod.dataset.intent || iod.dataset.intentId); return; }
    });
  }

  function buildTopbarButtons() {
    const meta = document.querySelector(".topbar-meta");
    if (!meta || meta.querySelector(".vw-topbtn[data-vw='dna']")) return;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "vw-topbtn";
    btn.dataset.vw = "dna";
    btn.textContent = "DNA Graph";
    btn.title = "View the company DNA — 13 sections of doctrine, culture, objectives, rules, subgraphs and more.";
    btn.addEventListener("click", openDnaGraph);
    meta.appendChild(btn);
  }

  // Capture intent id when the existing dashboard opens an intent card.
  // The existing app.js writes data-intent (not data-intent-id) on queue
  // rows, FR-tail rows and approve/modify/reject buttons. We accept both
  // conventions so this code stays correct if the markup is ever renamed.
  function patchOpenIntent() {
    document.addEventListener("click", (e) => {
      const row = e.target.closest("[data-intent], [data-intent-id]");
      if (row) {
        window.__currentIntentId =
          row.dataset.intent || row.dataset.intentId || window.__currentIntentId;
      }
    });
  }

  // Inject "Intent Object" + "Lifecycle" buttons into the Intent Card footer.
  function injectIntentCardButtons() {
    const ft = document.getElementById("intent-card-ft");
    if (!ft) return;
    if (!ft.querySelector(".iod-open-btn")) {
      const btn = document.createElement("button");
      btn.className = "iod-open-btn";
      btn.type = "button";
      btn.textContent = "Intent Object";
      btn.title = "Open the structured Intent Object view";
      btn.addEventListener("click", () => {
        const id = (window.__currentIntentId || "").trim();
        if (id) openIntentObject(id);
      });
      ft.insertBefore(btn, ft.firstChild);
    }
    if (!ft.querySelector(".lc-open-btn")) {
      const btn = document.createElement("button");
      btn.className = "lc-open-btn";
      btn.type = "button";
      btn.textContent = "Lifecycle";
      btn.title = "Open the Flight Recorder Lifecycle for this intent";
      btn.addEventListener("click", () => {
        const id = (window.__currentIntentId || "").trim();
        if (id) openLifecycle(id);
      });
      ft.insertBefore(btn, ft.firstChild);
    }
  }

  // Mark dimension scores rendered by the existing dashboard as clickable.
  // The existing app.js renders dimension chips inside the Intent Card body
  // with class "dim-chip" + data-dim="<key>"; we add data-boss-dim and the
  // pointer-cursor affordance in CSS (see vw-clickable-score).
  function annotateDimensionChips() {
    document.querySelectorAll("[data-dim]").forEach(el => {
      if (!el.dataset.bossDim) {
        el.dataset.bossDim = el.dataset.dim;
        el.classList.add("vw-clickable-score");
      }
    });
  }

  // ------------------------------------------------------------- public API
  window.DirectorViews = {
    openDnaGraph, openLifecycle, openLifecycleEvent: openLifecycleEvent,
    openDimension, openIntentObject,
  };

  // ------------------------------------------------------------- bootstrap
  document.addEventListener("DOMContentLoaded", () => {
    attachClickDelegation();
    patchOpenIntent();
    buildTopbarButtons();
    setInterval(() => {
      injectIntentCardButtons();
      annotateDimensionChips();
    }, 800);
  });
})();
