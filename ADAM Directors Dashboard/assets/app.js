/* ============================================================================
 * ADAM Directors Dashboard — controller
 * ----------------------------------------------------------------------------
 * Self-contained vanilla JS (zero dependencies). Runs from file:// or when
 * served by any HTTP host. No build step.
 *
 * Three-tier data strategy (auto-fallback):
 *   1. Live API   — http://localhost:8300 (the ADAM interface-server bundle).
 *                   Also probes 8200/8210/8220 for direct service access.
 *   2. Local JSON — relative paths, intended for cases where this folder is
 *                   served alongside the ADAM deployment directory.
 *   3. Demo       — window.ADAM_DEMO from /data/demo-data.js.
 *
 * Everything converges on a single normalised model the UI renders from.
 * ========================================================================== */

(function () {
  "use strict";

  /* --------------------------------------------------------------------- */
  /* Config                                                                */
  /* --------------------------------------------------------------------- */
  const CFG = {
    liveBases: [
      "http://localhost:8300",      // interface-server (UI + intent/pending/approve/reject/explain)
      ""                             // same-origin (when dashboard is served from ADAM itself)
    ],
    pollMs: 2000,
    localJson: {
      directors:       "../../deployment/NetStreamX/docs/directors.json",
      agents:          "../../deployment/NetStreamX/agents/agent-registry.json",
      boss:            "../../deployment/NetStreamX/boss/boss-config.json"
    }
  };

  const $  = (sel, el = document) => el.querySelector(sel);
  const $$ = (sel, el = document) => [...el.querySelectorAll(sel)];

  const esc = s => String(s ?? "").replace(/[&<>"']/g,
    c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const fmtNum = n => typeof n === "number" ? n.toLocaleString() : n;
  const tierClass = t => `pill pill-${(t || "").toUpperCase()}`;
  const tierKey   = t => (t || "").toLowerCase();

  /* --------------------------------------------------------------------- */
  /* Data source                                                           */
  /* --------------------------------------------------------------------- */
  const DataSource = {
    mode: "demo",            // "live" | "file" | "demo"
    base: "",
    lastError: null,

    async probe() {
      // 1. Live
      for (const base of CFG.liveBases) {
        try {
          const r = await fetch((base || "") + "/health", { method: "GET", cache: "no-store" });
          if (r.ok) {
            this.mode = "live";
            this.base = base;
            return;
          }
        } catch (_e) { /* try next */ }
      }
      // 2. Local files (fetch from relative path; only works when served by HTTP)
      try {
        const r = await fetch(CFG.localJson.agents, { cache: "no-store" });
        if (r.ok) {
          this.mode = "file";
          return;
        }
      } catch (_e) {}

      // 3. Demo
      this.mode = "demo";
    },

    async live_pending() {
      try {
        const r = await fetch(this.base + "/pending", { cache: "no-store" });
        if (!r.ok) return null;
        return await r.json();
      } catch (e) { this.lastError = e.message; return null; }
    },

    async live_submitIntent(text, nonIdem) {
      const r = await fetch(this.base + "/intent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, is_non_idempotent: !!nonIdem })
      });
      return await r.json();
    },

    async live_explain(intentId) {
      const r = await fetch(this.base + "/explain/" + encodeURIComponent(intentId));
      return await r.json();
    },

    async live_decide(intentId, decision) {
      const path = decision === "approve" ? "/approve/" : "/reject/";
      const r = await fetch(this.base + path + encodeURIComponent(intentId), { method: "POST" });
      return await r.json();
    },

    async file_json(path) {
      const r = await fetch(path, { cache: "no-store" });
      return await r.json();
    }
  };

  /* --------------------------------------------------------------------- */
  /* Model — normalised state the UI consumes                              */
  /* --------------------------------------------------------------------- */
  const Model = {
    meta: {}, directors: [], agent_classes: {}, agent_state: {},
    twin_usage: [], queue: [], flight_recorder: [], routing_24h: {}, boss: {},
    selectedDirector: "all",
    // Persistent index of every intent the director has seen or submitted —
    // used by the Explain-Back agent's fuzzy text search so directors can
    // find historical intents without knowing the intent_id.
    intent_history: []
  };

  async function refresh() {
    const demo = window.ADAM_DEMO;

    // Always start from demo (a complete baseline), then overlay live where available.
    const base = JSON.parse(JSON.stringify(demo));

    if (DataSource.mode === "live") {
      // Pull real pending queue
      const pending = await DataSource.live_pending();
      if (pending && pending.queue) {
        const q = [];
        for (const [id, entry] of Object.entries(pending.queue)) {
          const p = entry.packet || {};
          const dims = p.score_breakdown || p.dimensions || {};
          q.push({
            intent_id: id,
            queued_at: entry.queued_at,
            owning_director: p.owning_director || inferDirector(dims),
            tier: (p.tier || "HIGH").toUpperCase(),
            score: p.score ?? p.composite ?? 0,
            summary: (p.intent && (p.intent.desired_outcomes?.[0]?.description || p.intent.raw_text)) || "—",
            raw_text: p.intent?.desired_outcomes?.[0]?.description || "",
            dimensions: dims,
            non_idempotent: !!p.non_idempotent,
            triggered_by: p.triggered_by || [],
            alternatives: p.alternatives || [],
            recommendation: p.recommendation || "review",
            confidence_pct: p.confidence_pct || 0,
            time_sensitivity_hours: p.time_sensitivity_hours || 24
          });
        }
        base.queue = q.length ? q : base.queue;
      }
    } else if (DataSource.mode === "file") {
      try {
        const [dirs, agents, boss] = await Promise.all([
          DataSource.file_json(CFG.localJson.directors),
          DataSource.file_json(CFG.localJson.agents),
          DataSource.file_json(CFG.localJson.boss)
        ]);
        if (dirs?.directors) {
          base.directors = Object.entries(dirs.directors).map(([id, d]) => ({
            id,
            title: d.title,
            name: d.real_seat_holder_test,
            domain: d.domain,
            boss_dims: d.boss_dim_owned || [],
            cap_usd: d.delegation_cap_per_txn_test_usd,
            emergency_override: !!d.emergency_override_authority
          }));
        }
        if (agents?.agent_classes) {
          base.agent_classes = {};
          for (const [k, v] of Object.entries(agents.agent_classes)) {
            base.agent_classes[k] = {
              label: humanizeClass(k),
              description: v.description,
              agents: v.agents || []
            };
          }
          // Re-draw synthetic agent state from demo seed, but only for known ids
          const known = Object.values(base.agent_classes).flatMap(c => c.agents.map(a => a.id));
          base.agent_state = {};
          known.forEach(id => {
            const prev = demo.agent_state[id];
            base.agent_state[id] = prev || {
              id, status: "autonomous", inflight: 0, queue_depth: 0,
              cpu_pct: 5, mem_pct: 20, last_event: new Date().toISOString(),
              current_step: "idle"
            };
          });
        }
        if (boss?.dimensions) base.boss = { ...base.boss, ...boss };
      } catch (e) { console.warn("file mode partial failure:", e); }
    }

    Object.assign(Model, base);

    // Surface mode in the UI
    renderMode();
    renderAll();
  }

  function humanizeClass(k) {
    return k.split("_").map(w => w[0].toUpperCase() + w.slice(1)).join(" ");
  }

  function inferDirector(dims) {
    // map the heaviest BOSS dimension to the director who owns it
    if (!dims || !Object.keys(dims).length) return "ceo";
    const topDim = Object.entries(dims).sort((a,b)=>b[1]-a[1])[0][0];
    const map = {
      financial_exposure:   "cfo",
      regulatory_impact:    "legal_director",
      rights_certainty:     "legal_director",
      security_impact:      "ciso",
      sovereignty_action:   "ciso",
      reputational_risk:    "market_director",
      doctrinal_alignment:  "ceo"
    };
    return map[topDim] || "ceo";
  }

  /* --------------------------------------------------------------------- */
  /* Rendering                                                             */
  /* --------------------------------------------------------------------- */
  function renderMode() {
    const chip = $("#mode-chip");
    chip.dataset.mode = DataSource.mode;
    chip.querySelector(".dot").className = "dot " + (
      DataSource.mode === "live" ? "green" :
      DataSource.mode === "file" ? "amber" : "blue"
    );
    chip.querySelector("strong").textContent =
      DataSource.mode === "live" ? "Live · localhost:8300" :
      DataSource.mode === "file" ? "File mode" :
      "Demo mode";
    $("#doctrine-chip strong").textContent = Model.meta?.doctrine_version || "—";
    $("#company-chip strong").textContent = Model.meta?.company || "—";
    $("#adam-chip strong").textContent = "ADAM " + (Model.meta?.adam_version || "—");
  }

  function renderAll() {
    renderGroupGrid();
    renderDirectorRoster();
    renderQueue();
    renderTwins();
    renderRouting();
    renderFlightTail();
  }

  /* ---- Agent group grid ---- */
  function renderGroupGrid() {
    const root = $("#group-grid");
    root.innerHTML = "";
    const classes = Model.agent_classes || {};
    let totalUp = 0, totalEscal = 0, totalDown = 0;

    for (const [key, cls] of Object.entries(classes)) {
      const agents = cls.agents || [];
      let up = 0, escal = 0, down = 0;
      const tiles = agents.map(a => {
        const st = Model.agent_state[a.id] || { status: "autonomous" };
        if (st.status === "down") down++; else if (st.status === "escalation") escal++; else up++;
        return `<div class="agent-tile ${esc_status(st.status)}"
                     data-agent-id="${esc(a.id)}"
                     role="button" tabindex="0"
                     aria-label="${esc(a.name)} — ${esc(st.status)}"
                ></div>`;
      }).join("");

      totalUp += up; totalEscal += escal; totalDown += down;

      // Group-level sub-breakdown for corporate work groups & AI-centric
      const subBreakdown = groupSubBreakdown(agents);

      root.insertAdjacentHTML("beforeend", `
        <div class="group-card" data-class="${esc(key)}">
          <h4>
            <span class="dot ${down ? "red" : escal ? "amber" : "green"}"></span>
            ${esc(cls.label || key)}
            <span class="count">${agents.length}</span>
          </h4>
          <div class="panel-sub" style="font-size:11px">${esc(cls.description || "")}</div>
          <div class="agent-tiles">${tiles}</div>
          ${subBreakdown}
          <div class="legend">
            <span><i class="swatch" style="background:var(--tier-soap)"></i>${up} autonomous</span>
            <span><i class="swatch" style="background:var(--tier-high)"></i>${escal} escalating</span>
            <span><i class="swatch" style="background:var(--tier-ohshat)"></i>${down} down</span>
          </div>
        </div>
      `);
    }
    $("#mesh-totals").innerHTML =
      `<span><i class="swatch" style="background:var(--tier-soap)"></i><b>${totalUp}</b> autonomous</span>
       <span><i class="swatch" style="background:var(--tier-high)"></i><b>${totalEscal}</b> escalating</span>
       <span><i class="swatch" style="background:var(--tier-ohshat)"></i><b>${totalDown}</b> down</span>`;
  }

  function esc_status(s) {
    if (s === "down") return "down";
    if (s === "escalation") return "escalation";
    return "autonomous";
  }

  function groupSubBreakdown(agents) {
    const subs = {};
    for (const a of agents) {
      if (!a.sub_group) continue;
      const st = Model.agent_state[a.id]?.status || "autonomous";
      if (!subs[a.sub_group]) subs[a.sub_group] = { a: 0, e: 0, d: 0, t: 0 };
      subs[a.sub_group].t++;
      if (st === "down") subs[a.sub_group].d++;
      else if (st === "escalation") subs[a.sub_group].e++;
      else subs[a.sub_group].a++;
    }
    if (!Object.keys(subs).length) return "";
    return `<div style="font-size:11px;color:var(--adam-text-dim);display:grid;gap:3px;margin-top:2px;">
      ${Object.entries(subs).map(([g, c]) => `
        <div style="display:flex;align-items:center;gap:6px;">
          <span class="dot ${c.d?'red':c.e?'amber':'green'}" style="width:6px;height:6px;"></span>
          <span style="flex:1">${esc(g)}</span>
          <span style="color:var(--adam-text-mute)">${c.a}/${c.t}</span>
        </div>`).join("")}
    </div>`;
  }

  /* ---- Director roster ---- */
  function renderDirectorRoster() {
    const root = $("#director-roster");
    root.innerHTML = "";
    const queueByDirector = Model.queue.reduce((acc, q) => {
      acc[q.owning_director] = (acc[q.owning_director] || 0) + 1;
      return acc;
    }, {});

    for (const d of Model.directors) {
      const n = queueByDirector[d.id] || 0;
      const hasOhshat = Model.queue.some(q => q.owning_director === d.id && q.tier === "OHSHAT");
      const pillClass = hasOhshat ? "ohshat" : (n === 0 ? "zero" : "");

      root.insertAdjacentHTML("beforeend", `
        <div class="director-card" data-director="${esc(d.id)}" tabindex="0" role="button"
             aria-label="Filter queue to ${esc(d.title)}">
          <h5>${esc(d.title)}</h5>
          <small>${esc(d.name || "")}</small>
          <div style="margin-top:6px;font-size:11px;color:var(--adam-text-mute)">${esc(d.domain || "")}</div>
          <div class="count-pill ${pillClass}">${n} exception${n===1?"":"s"} in queue</div>
        </div>
      `);
    }
    // Populate director filter dropdown
    const sel = $("#director-filter");
    const current = sel.value || "all";
    sel.innerHTML = `<option value="all">All directors</option>` +
      Model.directors.map(d => `<option value="${esc(d.id)}">${esc(d.title)}</option>`).join("");
    sel.value = current;
  }

  /* ---- Director queue ---- */
  function renderQueue() {
    const list = $("#queue-list");
    const filter = Model.selectedDirector;
    const rows = Model.queue
      .filter(q => filter === "all" || q.owning_director === filter)
      .sort((a,b) => b.score - a.score);

    $("#queue-count").textContent = rows.length + " pending";

    if (!rows.length) {
      list.innerHTML = `<div style="padding:20px;text-align:center;color:var(--adam-text-mute)">
        <span class="dot green"></span> No exceptions in queue${filter !== "all" ? " for this director" : ""}.</div>`;
      return;
    }

    list.innerHTML = rows.map(q => {
      const dir = Model.directors.find(d => d.id === q.owning_director);
      const dirTitle = dir ? dir.title : q.owning_director;
      return `
        <div class="queue-item tier-${esc(q.tier)}" data-intent="${esc(q.intent_id)}" tabindex="0" role="button">
          <div class="queue-score" title="Composite BOSS score">${q.score}</div>
          <div>
            <span class="${tierClass(q.tier)}">${esc(q.tier)}</span>
            <span style="margin-left:8px;color:var(--adam-text-mute);font-size:11px">→ ${esc(dirTitle)}</span>
            <div class="queue-summary">${esc(q.summary || "")}</div>
            <div class="queue-meta">
              <span>⏱ ${q.time_sensitivity_hours}h SLA</span>
              <span>🎯 ${q.confidence_pct}% confidence</span>
              <span>↪ rec: ${esc(q.recommendation)}</span>
              ${q.non_idempotent ? `<span style="color:var(--tier-high)">⚠ non-idempotent (+15)</span>` : ""}
              ${(q.triggered_by||[]).slice(0,2).map(t=>`<span>• ${esc(t)}</span>`).join("")}
            </div>
          </div>
          <div class="queue-actions">
            <button class="btn approve" data-action="approve" data-intent="${esc(q.intent_id)}">Approve</button>
            <button class="btn modify"  data-action="modify"  data-intent="${esc(q.intent_id)}">Modify</button>
            <button class="btn danger"  data-action="reject"  data-intent="${esc(q.intent_id)}">Reject</button>
          </div>
        </div>`;
    }).join("");
  }

  /* ---- Twins ---- */
  function renderTwins() {
    const root = $("#twin-grid");
    root.innerHTML = "";
    for (const t of Model.twin_usage) {
      const agent = Object.values(Model.agent_classes)
        .flatMap(c => c.agents).find(a => a.id === t.id);
      const maxConsults = Math.max(...Model.twin_usage.map(x=>x.consultations_24h));
      const pct = Math.round(t.consultations_24h * 100 / maxConsults);
      const div = t.divergence_pct;
      const divColor = div >= 2 ? "var(--tier-high)" : div >= 1 ? "var(--tier-elevated)" : "var(--tier-soap)";
      root.insertAdjacentHTML("beforeend", `
        <div class="twin-card">
          <h5><span class="dot green"></span>${esc(agent?.name || t.id)}</h5>
          <div class="panel-sub" style="font-size:11px;">${esc(agent?.purpose || "")}</div>
          <div class="twin-stat"><span>Consultations (24h)</span><b>${fmtNum(t.consultations_24h)}</b></div>
          <div class="twin-bar"><span style="width:${pct}%"></span></div>
          <div class="twin-stat"><span>Avg latency</span><b>${t.avg_latency_ms} ms</b></div>
          <div class="twin-stat"><span>Live simulations</span><b>${t.simulations_running}</b></div>
          <div class="twin-stat"><span>Divergence</span><b style="color:${divColor}">${t.divergence_pct.toFixed(1)}%</b></div>
        </div>`);
    }
  }

  /* ---- Routing distribution ---- */
  function renderRouting() {
    const r = Model.routing_24h;
    const total = (r.soap||0)+(r.moderate||0)+(r.elevated||0)+(r.high||0)+(r.ohshat||0);
    $("#routing-total").textContent = fmtNum(total) + " decisions / 24h";
    const root = $("#routing");
    root.innerHTML = `
      <div class="cell soap"    ><b>${fmtNum(r.soap||0)}</b>SOAP</div>
      <div class="cell moderate"><b>${fmtNum(r.moderate||0)}</b>Moderate</div>
      <div class="cell elevated"><b>${fmtNum(r.elevated||0)}</b>Elevated</div>
      <div class="cell high"    ><b>${fmtNum(r.high||0)}</b>High</div>
      <div class="cell ohshat"  ><b>${fmtNum(r.ohshat||0)}</b>OHSHAT</div>`;
  }

  /* ---- Flight recorder tail ---- */
  function renderFlightTail() {
    const tail = Model.flight_recorder || [];
    const el = $("#fr-tail");
    el.innerHTML = tail.slice(-10).reverse().map(r => `
      <div class="fr-row">
        <span class="seq">#${r.seq}</span>
        <span class="${tierClass(r.tier)}" style="font-size:10px;padding:1px 6px">${esc(r.tier||"—")}</span>
        <span><span class="ev">${esc(r.event_type)}</span> <span style="color:var(--adam-text-mute)">${esc(r.agent_id)}</span></span>
        <span style="color:var(--adam-text-mute)">${esc((r.intent_id||"").slice(0,8))}…</span>
      </div>`).join("");
  }

  /* --------------------------------------------------------------------- */
  /* Conversational panels                                                 */
  /* --------------------------------------------------------------------- */
  function addBubble(where, who, html, meta) {
    const log = $("#" + where);
    const b = document.createElement("div");
    b.className = "bubble " + who;
    b.innerHTML = html + (meta ? `<small>${esc(meta)}</small>` : "");
    log.appendChild(b);
    log.scrollTop = log.scrollHeight;
  }

  /* Record a submitted intent in the session index so Explain-Back can find
   * it later by text search. */
  function recordIntent(entry) {
    // De-dupe on intent_id
    Model.intent_history = (Model.intent_history || []).filter(x => x.intent_id !== entry.intent_id);
    Model.intent_history.unshift(entry);
    // Cap the session index to keep the fuzzy search snappy.
    if (Model.intent_history.length > 200) Model.intent_history.length = 200;
  }

  async function submitIntent(text, nonIdem) {
    addBubble("intent-log", "you", esc(text));
    if (DataSource.mode === "live") {
      try {
        const r = await DataSource.live_submitIntent(text, nonIdem);
        const dims = r.interpreted?.dimensions || {};
        const dimList = Object.entries(dims).map(([k,v])=>`
          <div class="dim-row"><span>${esc(k)}</span><span>${v}</span>
            <div class="bar"><span class="s-${tierKey((v>=76?'ohshat':v>=51?'high':v>=31?'elevated':v>=11?'moderate':'soap'))}" style="width:${v}%"></span></div>
          </div>`).join("");
        const idShort = (r.intent_id || "").slice(0,8);
        addBubble("intent-log", "adam",
          `Interpreted. Routed to <span class="${tierClass(r.tier)}">${esc(r.tier||"?")}</span>
           with composite <b>${r.score??"?"}</b>.<br>
           <small>intent_id: <code>${esc(r.intent_id||"")}</code></small>
           <div class="dims-grid">${dimList}</div>
           <small>Ask Explain-Back about this later — just retype similar words or paste <code>${esc(idShort)}</code>.</small>`,
          `hi-intent · ${new Date().toLocaleTimeString()}`
        );
        // Track in session index so Explain-Back fuzzy search can find it.
        recordIntent({
          intent_id:       r.intent_id,
          text:            text,
          summary:         text,
          tier:            (r.tier || "").toUpperCase(),
          score:           r.score,
          dimensions:      dims,
          triggered_by:    r.triggered_by || [],
          owning_director: r.owning_director || inferDirector(dims),
          non_idempotent:  !!nonIdem,
          recommendation:  r.recommendation,
          confidence_pct:  r.confidence_pct,
          source:          "this session · live",
          queued_at:       new Date().toISOString()
        });
        if (r.tier && ["HIGH","OHSHAT","ELEVATED"].includes(r.tier.toUpperCase())) {
          addBubble("intent-log", "adam",
            `Escalation packet has been queued for the <b>${esc(r.tier)}</b> director. Check the queue panel.`,
            "hi-gateway");
          refresh();
        }
      } catch (e) {
        addBubble("intent-log", "adam", `Live submit failed: ${esc(e.message)}`, "error");
      }
    } else {
      // Local interpreter mirrors the server-side heuristic (interface_server.py)
      const out = localInterpret(text, nonIdem);
      const id = "sim-" + Math.random().toString(16).slice(2, 12);
      const idShort = id.slice(0,8);
      const dimList = Object.entries(out.dimensions).map(([k,v]) => `
        <div class="dim-row"><span>${esc(k)}</span><span>${v}</span>
          <div class="bar"><span class="s-${tierKey(v>=76?'ohshat':v>=51?'high':v>=31?'elevated':v>=11?'moderate':'soap')}" style="width:${v}%"></span></div>
        </div>`).join("");
      addBubble("intent-log", "adam",
        `Interpreted. Tier <span class="${tierClass(out.tier)}">${esc(out.tier)}</span>,
         composite <b>${out.score}</b>.<br>
         <small>intent_id: <code>${esc(id)}</code></small>
         <div class="dims-grid">${dimList}</div>
         <small>Demo interpretation — routed to <b>${esc(Model.directors.find(d=>d.id===out.director)?.title || out.director)}</b>.
         Ask Explain-Back with similar words or paste <code>${esc(idShort)}</code>.</small>`,
        `hi-intent · ${new Date().toLocaleTimeString()}`);

      // Always record — even SOAP/MODERATE intents are useful to look up.
      recordIntent({
        intent_id:       id,
        text:            text,
        summary:         text.slice(0, 160),
        tier:            out.tier,
        score:           out.score,
        dimensions:      out.dimensions,
        triggered_by:    out.triggered_by,
        owning_director: out.director,
        non_idempotent:  !!nonIdem,
        recommendation:  "review",
        confidence_pct:  60,
        source:          "this session · demo",
        queued_at:       new Date().toISOString()
      });

      if (["HIGH","OHSHAT","ELEVATED"].includes(out.tier)) {
        // Synthesise an entry into the queue so the director can practice the flow
        Model.queue.unshift({
          intent_id: id,
          queued_at: new Date().toISOString(),
          owning_director: out.director,
          tier: out.tier,
          score: out.score,
          summary: text.slice(0, 120),
          raw_text: text,
          dimensions: out.dimensions,
          non_idempotent: !!nonIdem,
          triggered_by: out.triggered_by,
          alternatives: [],
          recommendation: "review",
          confidence_pct: 60,
          time_sensitivity_hours: 24
        });
        renderQueue();
        renderDirectorRoster();
        addBubble("intent-log", "adam",
          `Escalation packet queued for <b>${esc(Model.directors.find(d=>d.id===out.director)?.title || out.director)}</b>. See the approval queue.`,
          "hi-gateway");
      }
    }
  }

  /* Lightweight heuristic mirroring interface_server.py — only used in demo/file */
  function localInterpret(text, nonIdem) {
    const dims = {
      security_impact: 5, sovereignty_action: 5, financial_exposure: 5,
      regulatory_impact: 5, reputational_risk: 5, rights_certainty: 5,
      doctrinal_alignment: 10
    };
    const triggered = [];

    const mFin = text.match(/\$\s?([\d,]+(?:\.\d+)?)/);
    if (mFin) {
      const amt = parseFloat(mFin[1].replace(/,/g, ""));
      for (const [max, score] of [[50000,80],[10000,55],[2500,35],[500,15],[100,5]]) {
        if (amt >= max) { dims.financial_exposure = score; triggered.push("financial_exposure"); break; }
      }
    }
    if (/(pii|customer data|egress|breach|leak|ransom)/i.test(text))  { dims.security_impact = Math.max(dims.security_impact, 75); triggered.push("security_impact"); }
    if (/(gdpr|ccpa|dora|nis2|regulator|compliance|license|rights)/i.test(text)) { dims.regulatory_impact = Math.max(dims.regulatory_impact, 55); triggered.push("regulatory_impact"); }
    if (/(campaign|brand|marketing|ad|press)/i.test(text)) { dims.reputational_risk = Math.max(dims.reputational_risk, 40); triggered.push("reputational_risk"); }
    if (/(deploy|rollout|incident|outage|scale|migrat)/i.test(text))  { dims.doctrinal_alignment = Math.max(dims.doctrinal_alignment, 35); triggered.push("doctrinal_alignment"); }
    if (/(sacred|minor|exploit|sanction|weapon)/i.test(text)) { dims.security_impact = 95; dims.doctrinal_alignment = 90; triggered.push("sacred_boundary"); }

    // Weighted composite per BOSS v3.2
    const w = Model.boss?.dimensions || { security_impact:5, sovereignty_action:4, financial_exposure:4, regulatory_impact:3, reputational_risk:3, rights_certainty:3, doctrinal_alignment:2 };
    const sum = Object.values(w).reduce((a,b)=>a+b, 0) || 24;
    let composite = Object.entries(w).reduce((acc,[k,wk]) => acc + (dims[k] || 0) * wk, 0) / sum;
    // Critical override
    const maxDim = Math.max(...Object.values(dims));
    if (maxDim > 75) composite = Math.max(composite, maxDim - 10);
    if (nonIdem) composite += 15;
    composite = Math.min(100, Math.round(composite));

    const tier =
      composite >= 76 ? "OHSHAT" :
      composite >= 51 ? "HIGH" :
      composite >= 31 ? "ELEVATED" :
      composite >= 11 ? "MODERATE" : "SOAP";

    return { tier, score: composite, dimensions: dims, triggered_by: triggered, director: inferDirector(dims) };
  }

  /* ---------------------------------------------------------------------
   * Explain-Back Agent — directors don't know intent_ids, so the primary
   * path is fuzzy TEXT search across every intent we know about (the live
   * queue + the session's own submitted intents + anything the user has
   * explored recently). An intent_id is accepted as a shortcut.
   * -------------------------------------------------------------------*/

  /* Build one searchable index over every intent ADAM has visibility on. */
  function buildIntentIndex() {
    const map = new Map();
    // Live/demo queue — fresh pending packets
    for (const q of (Model.queue || [])) {
      map.set(q.intent_id, {
        intent_id:       q.intent_id,
        text:            q.raw_text || q.summary || "",
        summary:         q.summary || q.raw_text || "",
        tier:            q.tier,
        score:           q.score,
        dimensions:      q.dimensions || {},
        triggered_by:    q.triggered_by || [],
        owning_director: q.owning_director,
        non_idempotent:  !!q.non_idempotent,
        recommendation:  q.recommendation,
        confidence_pct:  q.confidence_pct,
        source:          "pending queue",
        queued_at:       q.queued_at
      });
    }
    // Session history — intents submitted via hi-intent in this session.
    for (const h of (Model.intent_history || [])) {
      if (!map.has(h.intent_id)) map.set(h.intent_id, h);
    }
    return [...map.values()];
  }

  /* Token-overlap fuzzy score. Cheap, dependency-free, good enough for
   * narrative intents where directors reach for the same words twice. */
  function fuzzyScore(query, candidate) {
    const norm = s => String(s||"").toLowerCase().replace(/[^a-z0-9$.]+/g, " ").trim();
    const STOP = new Set(["the","a","an","to","of","for","on","in","at","and","or","is","be","with","from","into","by","as","that","this","it","approve","approved","approval"]);
    const qTok = norm(query).split(/\s+/).filter(t => t && !STOP.has(t));
    const cTok = new Set(norm(candidate).split(/\s+/).filter(t => t && !STOP.has(t)));
    if (!qTok.length || !cTok.size) return 0;
    let hit = 0;
    for (const t of qTok) {
      if (cTok.has(t)) { hit += 2; continue; }
      // partial match (e.g., "payment" ~ "payments", "$7500" ~ "$7,500")
      for (const c of cTok) if (c.includes(t) || t.includes(c)) { hit += 1; break; }
    }
    return hit / Math.max(qTok.length * 2, 1);   // 0..1
  }

  /* Render the full Explain-Back packet for a single intent. */
  function renderExplainPacket(intent) {
    const dimOrdered = Object.entries(intent.dimensions || {}).sort((a,b)=>b[1]-a[1]);
    const dimHtml = dimOrdered.map(([k,v]) => {
      const cls = v>=76?"ohshat":v>=51?"high":v>=31?"elevated":v>=11?"moderate":"soap";
      return `<div class="dim-row"><span>${esc(k)}</span><span>${v}</span>
        <div class="bar"><span class="s-${cls}" style="width:${v}%"></span></div>
      </div>`;
    }).join("");
    const director = Model.directors.find(d => d.id === intent.owning_director);
    addBubble("explain-log", "adam",
      `<b>Intent ${esc(intent.intent_id.slice(0,8))}… — <span class="${tierClass(intent.tier)}">${esc(intent.tier||"—")}</span> (composite ${intent.score||"—"})</b><br>
       <i>${esc(intent.summary || intent.text || "")}</i>
       <div class="dims-grid" style="margin-top:10px">${dimHtml || "<small>No dimension data.</small>"}</div>
       <p><b>Primary triggers:</b> ${(intent.triggered_by||[]).map(t=>`<code>${esc(t)}</code>`).join(", ") || "—"}.<br>
       <b>Routed to:</b> ${esc(director?.title || intent.owning_director || "—")}<br>
       ${intent.confidence_pct != null ? `<b>Recommendation:</b> ${esc(intent.recommendation || "—")} (${intent.confidence_pct}% confidence)<br>` : ""}
       ${intent.non_idempotent ? `<b>Non-idempotent:</b> BOSS added the +15 irreversibility penalty.` : ""}</p>
       <small style="color:var(--adam-text-mute)">source: ${esc(intent.source || "queue")}</small>`,
      `hi-explain · full packet`
    );
  }

  /* Render a clickable picker when multiple intents match the text. */
  function renderExplainMatches(query, matches) {
    const rows = matches.map(m => `
      <div class="match-option" data-intent="${esc(m.intent_id)}" role="button" tabindex="0"
           style="display:grid;grid-template-columns:auto 1fr auto;gap:8px;align-items:center;
                  padding:8px 10px;border:1px solid var(--adam-line-soft);border-radius:6px;
                  background:rgba(255,255,255,.02);cursor:pointer;margin-top:6px;">
        <span class="${tierClass(m.tier)}">${esc(m.tier||"—")}</span>
        <span style="font-size:12px">${esc((m.summary || m.text || "").slice(0, 120))}</span>
        <span style="font-family:var(--font-mono);font-size:11px;color:var(--adam-text-mute)">
          ${esc((m.intent_id||"").slice(0,8))}…
        </span>
      </div>`).join("");

    addBubble("explain-log", "adam",
      `I found <b>${matches.length}</b> intents matching "<i>${esc(query)}</i>". Click the one you meant:
       <div style="margin-top:6px">${rows}</div>`,
      "hi-explain · fuzzy match");
  }

  async function explainIntent(text) {
    const q = String(text || "").trim();
    if (!q) return;
    addBubble("explain-log", "you", esc(q));

    // 1) If it LOOKS like an intent_id (hex/uuid-ish, no spaces), go direct.
    const looksLikeId = /^[a-f0-9][a-f0-9-]{5,}$/i.test(q);

    if (looksLikeId) {
      // Try live first
      if (DataSource.mode === "live") {
        try {
          const r = await DataSource.live_explain(q);
          if (r && r.narrative && r.narrative.length) {
            const paras = r.narrative.map(p => `<p>${esc(p)}</p>`).join("");
            addBubble("explain-log", "adam", paras, "hi-explain · Flight Recorder replay");
            return;
          }
        } catch (_e) { /* fall through */ }
      }
      // Then match against the known index by id prefix
      const idx = buildIntentIndex();
      const byId = idx.find(i => i.intent_id === q || i.intent_id.startsWith(q));
      if (byId) { renderExplainPacket(byId); return; }
      // Fall through to text search as a secondary attempt
    }

    // 2) Fuzzy TEXT search across every intent we know
    const idx = buildIntentIndex();
    if (!idx.length) {
      addBubble("explain-log", "adam",
        `I don't have any intents in the session index yet. Submit one through the Intent Agent, or wait for the pending queue to populate.`,
        "hi-explain");
      return;
    }

    const scored = idx
      .map(i => ({ i, s: fuzzyScore(q, (i.summary || "") + " " + (i.text || "")) }))
      .filter(r => r.s >= 0.15)
      .sort((a,b) => b.s - a.s);

    if (!scored.length) {
      addBubble("explain-log", "adam",
        `No intents match "<i>${esc(q)}</i>". Try a keyword from the original intent — for example an amount, "DORA", "vendor", "campaign", or "doctrine".`,
        "hi-explain");
      return;
    }

    // 3) Single strong match → render directly
    if (scored.length === 1 || scored[0].s - scored[1].s > 0.25) {
      renderExplainPacket(scored[0].i);
      return;
    }

    // 4) Multiple candidates → render picker
    const top = scored.slice(0, Math.min(6, scored.length)).map(r => r.i);
    renderExplainMatches(q, top);
  }

  /* --------------------------------------------------------------------- */
  /* Exception queue actions + modal                                       */
  /* --------------------------------------------------------------------- */
  function openExceptionModal(intentId) {
    const q = Model.queue.find(x => x.intent_id === intentId);
    if (!q) return;
    const dir = Model.directors.find(d => d.id === q.owning_director);
    const dimHtml = Object.entries(q.dimensions || {})
      .sort((a,b) => b[1]-a[1])
      .map(([k,v]) => {
        const cls = v>=76?"ohshat":v>=51?"high":v>=31?"elevated":v>=11?"moderate":"soap";
        return `<div class="dim-row"><span>${esc(k)}</span><span>${v}</span>
          <div class="bar"><span class="s-${cls}" style="width:${v}%"></span></div></div>`;
      }).join("");
    const altHtml = (q.alternatives || []).map(a => `
      <li>${esc(a.label)} → projected composite <b>${a.projected_score}</b></li>`).join("") ||
      "<li>No alternatives available.</li>";

    $("#modal-title").innerHTML = `<span class="${tierClass(q.tier)}">${esc(q.tier)}</span> · Intent ${esc(q.intent_id.slice(0,8))}…`;
    $("#modal-body").innerHTML = `
      <h4 style="margin:0 0 4px">${esc(q.summary)}</h4>
      <div class="panel-sub">Routed to <b>${esc(dir?.title || q.owning_director)}</b> · ${q.time_sensitivity_hours}h SLA · ${q.confidence_pct}% confidence</div>
      <div style="margin-top:12px;font-size:12px;color:var(--adam-text-dim)">Original intent text</div>
      <div style="padding:10px;background:rgba(0,0,0,.3);border:1px solid var(--adam-line-soft);border-radius:6px;font-size:13px;margin-top:4px">${esc(q.raw_text || q.summary)}</div>
      <h5 style="margin:16px 0 4px">BOSS v3.2 dimension breakdown</h5>
      <div class="dims-grid">${dimHtml}</div>
      <h5 style="margin:14px 0 4px">Alternatives with lower composite</h5>
      <ul style="margin:4px 0 0 18px;padding:0">${altHtml}</ul>
      <h5 style="margin:14px 0 4px">Triggers</h5>
      <div class="queue-meta">${(q.triggered_by||[]).map(t=>`<span>• ${esc(t)}</span>`).join("") || "<span>—</span>"}</div>
      <h5 style="margin:14px 0 4px">Explain-Back narrative</h5>
      <div id="modal-explain" style="font-size:12px;color:var(--adam-text-dim)">
        Intent received and validated. BOSS v3.2 scored ${q.score} composite via weighted dimensions.
        ${q.non_idempotent ? "Non-idempotent flag added +15 penalty. " : ""}
        Critical override ${Math.max(...Object.values(q.dimensions||{0:0}))>75 ? "engaged" : "not engaged"}.
        Exception packet emitted to owning director.
      </div>`;
    $("#modal-approve").dataset.intent = q.intent_id;
    $("#modal-modify").dataset.intent = q.intent_id;
    $("#modal-reject").dataset.intent = q.intent_id;
    $("#modal-root").hidden = false;
    $("#modal-approve").focus();
  }

  function closeModal() { $("#modal-root").hidden = true; }

  async function decide(intentId, action) {
    const q = Model.queue.find(x => x.intent_id === intentId);
    if (!q) return;
    if (DataSource.mode === "live" && (action === "approve" || action === "reject")) {
      try { await DataSource.live_decide(intentId, action); } catch (_e) {}
    }
    // Local state update (works regardless of mode)
    Model.queue = Model.queue.filter(x => x.intent_id !== intentId);
    Model.flight_recorder.push({
      seq: (Model.flight_recorder.slice(-1)[0]?.seq || 10500) + 1,
      ts: new Date().toISOString(),
      event_type: action === "approve" ? "director_approval" : action === "modify" ? "director_modified" : "director_rejection",
      agent_id: "hi-gateway",
      tier: q.tier,
      intent_id: intentId
    });
    renderQueue(); renderDirectorRoster(); renderFlightTail();
    closeModal();
    toast(`Intent ${intentId.slice(0,8)}… ${action}ed.`, action === "reject" ? "err" : "ok");
  }

  /* Toast */
  function toast(msg, kind) {
    const el = document.createElement("div");
    el.textContent = msg;
    el.style.cssText = `
      position:fixed;bottom:20px;left:50%;transform:translateX(-50%);
      background:${kind === "err" ? "var(--tier-ohshat)" : "var(--tier-soap)"};
      color:#0a1220;font-weight:600;padding:10px 16px;border-radius:8px;
      box-shadow:var(--shadow-lg);z-index:300;font-size:13px;`;
    document.body.appendChild(el);
    setTimeout(() => { el.style.opacity = "0"; el.style.transition = "opacity .35s"; }, 1400);
    setTimeout(() => el.remove(), 2000);
  }

  /* --------------------------------------------------------------------- */
  /* Tooltip                                                                */
  /* --------------------------------------------------------------------- */
  function showTooltip(ev) {
    const el = ev.target.closest(".agent-tile");
    if (!el) return;
    const id = el.dataset.agentId;
    const st = Model.agent_state[id] || {};
    const agent = Object.values(Model.agent_classes).flatMap(c => c.agents).find(a => a.id === id);
    if (!agent) return;
    const tt = $("#tooltip");
    tt.innerHTML = `
      <b>${esc(agent.name)}</b><br>
      <span style="color:var(--adam-text-mute)">${esc(id)}</span><br>
      <span class="pill pill-${st.status==='down'?'OHSHAT':st.status==='escalation'?'HIGH':'SOAP'}">${esc(st.status)}</span><br>
      <span style="color:var(--adam-text-dim);font-size:11px">${esc(st.current_step||"")}</span><br>
      CPU ${st.cpu_pct||0}% · Mem ${st.mem_pct||0}% · Q ${st.queue_depth||0}`;
    tt.classList.add("show");
    const r = el.getBoundingClientRect();
    tt.style.left = Math.min(window.innerWidth - 300, r.left + 18) + "px";
    tt.style.top  = (r.top - 8 - tt.offsetHeight) + "px";
    if (parseInt(tt.style.top) < 0) tt.style.top = (r.bottom + 8) + "px";
  }
  function hideTooltip() { $("#tooltip").classList.remove("show"); }

  /* --------------------------------------------------------------------- */
  /* Wiring                                                                 */
  /* --------------------------------------------------------------------- */
  function wire() {
    // Intent form
    $("#intent-form").addEventListener("submit", e => {
      e.preventDefault();
      const t = $("#intent-input").value.trim();
      if (!t) return;
      const ni = $("#intent-nonidem").checked;
      $("#intent-input").value = "";
      $("#intent-nonidem").checked = false;
      submitIntent(t, ni);
    });
    // Explain form
    $("#explain-form").addEventListener("submit", e => {
      e.preventDefault();
      const t = $("#explain-input").value.trim();
      if (!t) return;
      $("#explain-input").value = "";
      explainIntent(t);
    });
    // Explain-Back picker — click a match row to render its packet
    $("#explain-log").addEventListener("click", e => {
      const opt = e.target.closest(".match-option");
      if (!opt) return;
      const id = opt.dataset.intent;
      const hit = buildIntentIndex().find(i => i.intent_id === id);
      if (hit) renderExplainPacket(hit);
    });
    $("#explain-log").addEventListener("keydown", e => {
      if ((e.key === "Enter" || e.key === " ") && e.target.classList?.contains("match-option")) {
        e.preventDefault();
        e.target.click();
      }
    });
    // Intent/Explain example chips
    $$(".example-chip").forEach(c => c.addEventListener("click", () => {
      const target = c.dataset.target;
      document.getElementById(target).value = c.dataset.text;
      document.getElementById(target).focus();
    }));
    // Queue clicks + action buttons
    $("#queue-list").addEventListener("click", e => {
      const btn = e.target.closest("button[data-action]");
      if (btn) {
        decide(btn.dataset.intent, btn.dataset.action);
        return;
      }
      const row = e.target.closest(".queue-item");
      if (row) openExceptionModal(row.dataset.intent);
    });
    $("#queue-list").addEventListener("keydown", e => {
      if (e.key === "Enter" || e.key === " ") {
        const row = e.target.closest(".queue-item");
        if (row) { e.preventDefault(); openExceptionModal(row.dataset.intent); }
      }
    });
    // Director roster filter
    $("#director-roster").addEventListener("click", e => {
      const card = e.target.closest(".director-card");
      if (card) {
        Model.selectedDirector = card.dataset.director;
        $("#director-filter").value = Model.selectedDirector;
        renderQueue();
      }
    });
    $("#director-filter").addEventListener("change", e => {
      Model.selectedDirector = e.target.value;
      renderQueue();
    });
    // Modal buttons
    $("#modal-close").addEventListener("click", closeModal);
    $("#modal-root").addEventListener("click", e => { if (e.target.id === "modal-root") closeModal(); });
    $("#modal-approve").addEventListener("click", e => decide(e.target.dataset.intent, "approve"));
    $("#modal-modify") .addEventListener("click", e => decide(e.target.dataset.intent, "modify"));
    $("#modal-reject") .addEventListener("click", e => decide(e.target.dataset.intent, "reject"));
    $("#modal-cancel") .addEventListener("click", closeModal);
    document.addEventListener("keydown", e => { if (e.key === "Escape") closeModal(); });
    // Density slider
    $("#density").addEventListener("input", e => {
      document.documentElement.style.setProperty("--font-scale", e.target.value);
      document.body.style.fontSize = (parseFloat(e.target.value) * 14) + "px";
    });
    // Refresh button
    $("#refresh-btn").addEventListener("click", () => refresh());
    // Tooltip delegation
    $("#group-grid").addEventListener("mouseover", showTooltip);
    $("#group-grid").addEventListener("mouseout",  hideTooltip);
    $("#group-grid").addEventListener("focusin",   showTooltip);
    $("#group-grid").addEventListener("focusout",  hideTooltip);
    // Export briefing (print)
    $("#export-btn").addEventListener("click", () => window.print());
  }

  /* --------------------------------------------------------------------- */
  /* Live polling — mutate some agent states so it feels alive              */
  /* --------------------------------------------------------------------- */
  function pulse() {
    if (DataSource.mode !== "live") {
      const ids = Object.keys(Model.agent_state);
      for (let i = 0; i < 4; i++) {
        const id = ids[Math.floor(Math.random() * ids.length)];
        const st = Model.agent_state[id];
        if (!st) continue;
        st.cpu_pct = Math.max(2, Math.min(98, st.cpu_pct + (Math.random() * 20 - 10) | 0));
        st.inflight = Math.max(0, st.inflight + (Math.random() > 0.5 ? 1 : -1));
        st.last_event = new Date().toISOString();
      }
      if (Math.random() > 0.7) {
        const id = ids[Math.floor(Math.random() * ids.length)];
        const st = Model.agent_state[id];
        if (st) {
          const r = Math.random();
          st.status = r > 0.92 ? "down" : r > 0.8 ? "escalation" : "autonomous";
          st.current_step = st.status === "autonomous"
            ? ["planning","validating","executing","verifying","recording evidence"][Math.floor(Math.random()*5)]
            : st.status === "escalation" ? "awaiting director approval" : "offline — investigating";
        }
      }
      const events = ["boss_scored","governor_evaluated","action_executed","twin_simulation_recorded","governors_concurred"];
      Model.flight_recorder.push({
        seq: (Model.flight_recorder.slice(-1)[0]?.seq || 10500) + 1,
        ts: new Date().toISOString(),
        event_type: events[Math.floor(Math.random()*events.length)],
        agent_id: ids[Math.floor(Math.random() * ids.length)],
        tier: ["SOAP","MODERATE","ELEVATED","HIGH","OHSHAT"][Math.floor(Math.random()*5)],
        intent_id: "stream-" + Math.random().toString(16).slice(2, 10)
      });
      if (Model.flight_recorder.length > 200) Model.flight_recorder.splice(0, 50);
      Model.routing_24h.soap = (Model.routing_24h.soap||0) + Math.floor(Math.random()*3);
      Model.routing_24h.moderate = (Model.routing_24h.moderate||0) + (Math.random() > 0.7 ? 1 : 0);
      renderGroupGrid(); renderFlightTail(); renderRouting();
    } else {
      refresh();
    }
  }

  /* --------------------------------------------------------------------- */
  /* Boot                                                                   */
  /* --------------------------------------------------------------------- */
  async function boot() {
    wire();
    await DataSource.probe();
    await refresh();
    setInterval(pulse, CFG.pollMs);
  }
  document.addEventListener("DOMContentLoaded", boot);
})();
