/* ============================================================================
 * ADAM Directors Dashboard — v0.2 controller
 * ----------------------------------------------------------------------------
 * Vanilla ES2020, zero dependencies.
 * Three full-screen overlays: Agent Card, Intent Object Card, Action workflow.
 * LIVE/DEMO toggle. Per-director scope filtering. Idempotent action_ids.
 * ========================================================================== */
(function () {
  "use strict";

  const CFG = { apiBase: "", pollMs: 2000 };
  const $  = (sel, el = document) => el.querySelector(sel);
  const $$ = (sel, el = document) => [...el.querySelectorAll(sel)];
  const esc = s => String(s ?? "").replace(/[&<>"']/g,
    c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmtNum = n => typeof n === "number" ? n.toLocaleString() : n;
  const tierClass = t => `pill pill-${(t || "").toUpperCase()}`;
  const tierKey = t => (t || "").toLowerCase();
  const tierFromScore = v =>
      v >= 76 ? "ohshat" : v >= 51 ? "high" : v >= 31 ? "elevated" : v >= 11 ? "moderate" : "soap";

  /* uuidv5 — pure JS, dependency-free */
  function uuidv5(name, ns) {
    function strBytes(s){ const b=[]; for(let i=0;i<s.length;i++)b.push(s.charCodeAt(i)&0xff); return b; }
    function nsBytes(u){ const h=u.replace(/-/g,""); const b=[]; for(let i=0;i<h.length;i+=2)b.push(parseInt(h.substr(i,2),16)); return b; }
    function sha1(bytes){
      const W=new Array(80); let H=[0x67452301,0xEFCDAB89,0x98BADCFE,0x10325476,0xC3D2E1F0];
      const ml=bytes.length*8; bytes.push(0x80); while((bytes.length%64)!==56)bytes.push(0);
      for(let i=7;i>=0;i--)bytes.push((ml/Math.pow(2,8*i))&0xff);
      for(let off=0;off<bytes.length;off+=64){
        for(let i=0;i<16;i++)W[i]=(bytes[off+i*4]<<24)|(bytes[off+i*4+1]<<16)|(bytes[off+i*4+2]<<8)|(bytes[off+i*4+3]);
        for(let i=16;i<80;i++){const v=W[i-3]^W[i-8]^W[i-14]^W[i-16]; W[i]=(v<<1)|(v>>>31);}
        let [a,b,c,d,e]=H;
        for(let i=0;i<80;i++){
          let f,k;
          if(i<20){f=(b&c)|((~b)&d); k=0x5A827999;}
          else if(i<40){f=b^c^d; k=0x6ED9EBA1;}
          else if(i<60){f=(b&c)|(b&d)|(c&d); k=0x8F1BBCDC;}
          else{f=b^c^d; k=0xCA62C1D6;}
          const t=(((a<<5)|(a>>>27))+f+e+k+W[i])>>>0;
          e=d; d=c; c=((b<<30)|(b>>>2))>>>0; b=a; a=t;
        }
        H=[(H[0]+a)>>>0,(H[1]+b)>>>0,(H[2]+c)>>>0,(H[3]+d)>>>0,(H[4]+e)>>>0];
      }
      const out=[]; for(let i=0;i<5;i++) out.push((H[i]>>>24)&0xff,(H[i]>>>16)&0xff,(H[i]>>>8)&0xff,H[i]&0xff);
      return out;
    }
    const arr = sha1(nsBytes(ns).concat(strBytes(name))).slice(0,16);
    arr[6] = (arr[6] & 0x0f) | 0x50;
    arr[8] = (arr[8] & 0x3f) | 0x80;
    const h = arr.map(b => (b<16?"0":"")+b.toString(16)).join("");
    return `${h.slice(0,8)}-${h.slice(8,12)}-${h.slice(12,16)}-${h.slice(16,20)}-${h.slice(20,32)}`;
  }
  const ADAM_NS = "d59ec49f-7040-45c7-9324-835626f87525";
  const actionId = (...parts) => uuidv5(parts.map(p => p == null ? "" : String(p)).join("|"), ADAM_NS);

  /* DataSource — talks to /api/dashboard/* on same origin */
  const DataSource = {
    apiAvailable: false,
    async probe(){
      try { const r = await fetch(CFG.apiBase + "/api/dashboard/health", {cache:"no-store"});
            if (r.ok){ const b = await r.json(); this.apiAvailable = !!b.ok; }
      } catch(_){ this.apiAvailable = false; }
    },
    async bootstrap(){
      if (!this.apiAvailable) return null;
      try { const r = await fetch(CFG.apiBase + "/api/dashboard/bootstrap"); return r.ok ? await r.json() : null; }
      catch(_){ return null; }
    },
    async state(mode){
      if (!this.apiAvailable) return null;
      try { const r = await fetch(CFG.apiBase + `/api/dashboard/state?mode=${encodeURIComponent(mode)}`, {cache:"no-store"});
            return r.ok ? await r.json() : null; } catch(_){ return null; }
    },
    async agentCard(id, mode){
      if (!this.apiAvailable) return null;
      try { const r = await fetch(CFG.apiBase + `/api/dashboard/agent/${encodeURIComponent(id)}?mode=${mode}`); return r.ok ? await r.json() : null; }
      catch(_){ return null; }
    },
    async intentCard(id, mode){
      if (!this.apiAvailable) return null;
      try { const r = await fetch(CFG.apiBase + `/api/dashboard/intent/${encodeURIComponent(id)}?mode=${mode}`); return r.ok ? await r.json() : null; }
      catch(_){ return null; }
    },
    async whatIf(id, dimension_overrides, non_idempotent){
      if (!this.apiAvailable) return null;
      try { const r = await fetch(CFG.apiBase + `/api/dashboard/intent/${encodeURIComponent(id)}/what_if`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({dimension_overrides, non_idempotent}) });
        return r.ok ? await r.json() : null; } catch(_){ return null; }
    },
    async submitDecision(id, payload){
      try { const r = await fetch(CFG.apiBase + `/api/dashboard/intent/${encodeURIComponent(id)}/decision`, {
        method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(payload) });
        return await r.json(); } catch(e){ return {ok:false,error:e.message}; }
    },
    async submitAgentControl(id, payload){
      try { const r = await fetch(CFG.apiBase + `/api/dashboard/agent/${encodeURIComponent(id)}/control`, {
        method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(payload) });
        return await r.json(); } catch(e){ return {ok:false,error:e.message}; }
    }
  };

  const UI = { mode:"demo", actingDirector:"ceo", viewingDirector:"ceo",
               selectedDirectorFilter:"all", bootstrap:null, state:null, history:[] };

  const DEFAULT_SCOPES = {
    ceo:             { prefixes:["*"], explicit:[], edit_all:true  },
    ciso:            { prefixes:["*"], explicit:[], edit_all:true  },
    cfo:             { prefixes:["hi-","ga-financial","orch-","wg-fin-","ai-audit-","ai-auto-budget","meta-","twin-"], explicit:["ga-operations"], edit_all:false },
    legal_director:  { prefixes:["hi-","ga-legal","orch-","wg-legal-","ai-ethics-","meta-","twin-"], explicit:["wg-data-pii","wg-data-rights","wg-data-residency","wg-gov-filing","wg-gov-compliance"], edit_all:false },
    market_director: { prefixes:["hi-","ga-market","orch-","wg-market-","meta-","twin-"], explicit:["wg-gov-stakeholder","ai-strategy-competitive","ai-external-stakeholder","ai-external-regulatory"], edit_all:false },
    cpo:             { prefixes:["hi-","ga-operations","orch-","wg-ops-","ai-innov-","ai-strategy-","meta-","twin-"], explicit:["wg-fin-budget","wg-fin-capital"], edit_all:false },
    cto:             { prefixes:["hi-","ga-operations","orch-","wg-data-","wg-sec-vault","ai-model-","ai-data-","ai-core-","meta-","twin-"], explicit:["ga-security"], edit_all:false }
  };

  function scopesForViewer(id){ return UI.bootstrap?.scopes?.[id] || DEFAULT_SCOPES[id] || DEFAULT_SCOPES.ceo; }
  function agentInScope(agentId, directorId){
    const r = scopesForViewer(directorId);
    if (r.edit_all || (r.prefixes||[]).includes("*")) return true;
    if ((r.explicit||[]).includes(agentId)) return true;
    return (r.prefixes||[]).some(p => agentId.startsWith(p));
  }
  function canEdit(actingId, ownerId){
    if (!actingId) return false;
    const r = scopesForViewer(actingId);
    if (r.edit_all) return true;
    return actingId === ownerId;
  }

  async function refresh(){
    let s = null;
    if (DataSource.apiAvailable) s = await DataSource.state(UI.mode);
    if (!s){
      const demo = window.ADAM_DEMO || {};
      s = JSON.parse(JSON.stringify(demo));
      s.meta = s.meta || {}; s.meta.mode = UI.mode;
    }
    UI.state = s;
    renderAll();
  }

  async function bootstrap(){
    const b = await DataSource.bootstrap();
    if (b){
      UI.bootstrap = b;
      populateDirectorSelect("director-select", b.directors);
      populateDirectorSelect("viewing-select", b.directors);
      populateDirectorFilter(b.directors);
    } else {
      const demo = window.ADAM_DEMO || {};
      UI.bootstrap = { directors: demo.directors || [], scopes: DEFAULT_SCOPES };
      populateDirectorSelect("director-select", demo.directors || []);
      populateDirectorSelect("viewing-select", demo.directors || []);
      populateDirectorFilter(demo.directors || []);
    }
    UI.actingDirector = $("#director-select").value || "ceo";
    UI.viewingDirector = $("#viewing-select").value || UI.actingDirector;
  }

  function populateDirectorSelect(elId, directors){
    const el = $("#" + elId); if (!el) return;
    const prev = el.value;
    el.innerHTML = (directors || [])
      .filter(d => d.active !== false)
      .map(d => `<option value="${esc(d.id)}">${esc(d.title || d.id)}</option>`).join("");
    if (prev && [...el.options].some(o => o.value === prev)) el.value = prev;
  }
  function populateDirectorFilter(directors){
    const sel = $("#director-filter"); if (!sel) return;
    const prev = sel.value || "all";
    sel.innerHTML = `<option value="all">All directors</option>` +
      (directors || []).filter(d => d.active !== false)
        .map(d => `<option value="${esc(d.id)}">${esc(d.title || d.id)}</option>`).join("");
    sel.value = prev;
  }

  function renderAll(){
    const s = UI.state || {};
    renderTopChips(s); renderEditBanner();
    renderGroupGrid(s); renderDirectorRoster(s);
    renderRouting(s); renderQueue(s); renderTwins(s); renderFlightTail(s);
  }

  function renderTopChips(s){
    const m = s?.meta || {};
    const chip = $("#mode-chip");
    chip.dataset.mode = UI.mode;
    chip.querySelector(".dot").className = "dot " + (UI.mode === "live" ? "green" : "blue");
    $("#doctrine-chip strong").textContent = m.doctrine_version || "—";
    $("#company-chip strong").textContent  = m.company || "—";
    $("#adam-chip strong").textContent     = "ADAM " + (m.adam_version || "—");
  }

  function renderEditBanner(){
    const banner = $("#edit-banner"); if (!banner) return;
    const acting = UI.actingDirector, viewing = UI.viewingDirector;
    const dActing  = (UI.bootstrap?.directors || []).find(d => d.id === acting);
    const dViewing = (UI.bootstrap?.directors || []).find(d => d.id === viewing);
    const editable = canEdit(acting, viewing);
    banner.hidden = false;
    banner.classList.toggle("editable", editable);
    banner.classList.toggle("readonly", !editable);
    const note = editable
      ? `You are <b>${esc(dActing?.title || acting)}</b> and may edit the <b>${esc(dViewing?.title || viewing)}</b> dashboard.`
      : `You are <b>${esc(dActing?.title || acting)}</b>. The <b>${esc(dViewing?.title || viewing)}</b> dashboard is <b>read-only</b> for you (CEO/CISO can edit any).`;
    banner.innerHTML = `<span class="dot ${editable ? "green" : "amber"}"></span><span>${note}</span>`;
  }

  function esc_status(s){ return s === "down" ? "down" : s === "escalation" ? "escalation" : "autonomous"; }

  function renderGroupGrid(s){
    const root = $("#group-grid"); if (!root) return;
    root.innerHTML = "";
    const classes = s.agent_classes || {};
    const viewer = UI.viewingDirector;
    let totalUp=0, totalEscal=0, totalDown=0, totalShown=0, totalHidden=0;
    for (const [key, cls] of Object.entries(classes)){
      const agents = cls.agents || [];
      let up=0, escal=0, down=0;
      const tiles = agents.map(a => {
        const inScope = agentInScope(a.id, viewer);
        if (inScope) totalShown++; else totalHidden++;
        const st = (s.agent_state || {})[a.id] || {status:"autonomous"};
        if (st.status === "down") down++; else if (st.status === "escalation") escal++; else up++;
        return `<div class="agent-tile ${esc_status(st.status)}${inScope ? "" : " out-of-scope"}"
                     data-agent-id="${esc(a.id)}" role="button" tabindex="0"
                     aria-label="${esc(a.name)} — ${esc(st.status)}"></div>`;
      }).join("");
      totalUp += up; totalEscal += escal; totalDown += down;
      root.insertAdjacentHTML("beforeend", `
        <div class="group-card" data-class="${esc(key)}">
          <h4>
            <span class="dot ${down ? "red" : escal ? "amber" : "green"}"></span>
            ${esc(cls.label || key)}
            <span class="count">${agents.length}</span>
          </h4>
          <div class="panel-sub" style="font-size:11px">${esc(cls.description || "")}</div>
          <div class="agent-tiles">${tiles}</div>
          <div class="legend">
            <span><i class="swatch" style="background:var(--tier-soap)"></i>${up} autonomous</span>
            <span><i class="swatch" style="background:var(--tier-high)"></i>${escal} escalating</span>
            <span><i class="swatch" style="background:var(--tier-ohshat)"></i>${down} down</span>
          </div>
        </div>`);
    }
    $("#mesh-totals").innerHTML =
      `<span><i class="swatch" style="background:var(--tier-soap)"></i><b>${totalUp}</b> autonomous</span>
       <span><i class="swatch" style="background:var(--tier-high)"></i><b>${totalEscal}</b> escalating</span>
       <span><i class="swatch" style="background:var(--tier-ohshat)"></i><b>${totalDown}</b> down</span>`;
    const dViewing = (UI.bootstrap?.directors || []).find(d => d.id === UI.viewingDirector);
    const isFull = scopesForViewer(UI.viewingDirector).edit_all;
    $("#mesh-scope").textContent = isFull
      ? `${totalShown + totalHidden} agents · full mesh (${esc(dViewing?.title || UI.viewingDirector)})`
      : `${totalShown} of ${totalShown + totalHidden} agents in scope (${esc(dViewing?.title || UI.viewingDirector)})`;
  }

  function renderDirectorRoster(s){
    const root = $("#director-roster"); if (!root) return;
    root.innerHTML = "";
    const queueByDirector = (s.queue || []).reduce((acc, q) => {
      acc[q.owning_director] = (acc[q.owning_director] || 0) + 1; return acc;
    }, {});
    const directors = (s.directors || UI.bootstrap?.directors || []);
    for (const d of directors){
      if (d.active === false) continue;
      const n = queueByDirector[d.id] || 0;
      const hasOhshat = (s.queue || []).some(q => q.owning_director === d.id && q.tier === "OHSHAT");
      const pillClass = hasOhshat ? "ohshat" : (n === 0 ? "zero" : "");
      const isViewing = d.id === UI.viewingDirector;
      root.insertAdjacentHTML("beforeend", `
        <div class="director-card ${isViewing ? "active" : ""}" data-director="${esc(d.id)}" tabindex="0" role="button"
             aria-label="View ${esc(d.title)} dashboard">
          <h5>${esc(d.title)}</h5>
          <small>${esc(d.name || "")}</small>
          <div style="margin-top:6px;font-size:11px;color:var(--adam-text-mute)">${esc(d.domain || "")}</div>
          <div class="count-pill ${pillClass}">${n} exception${n===1?"":"s"} in queue</div>
        </div>`);
    }
  }

  function renderQueue(s){
    const list = $("#queue-list"); if (!list) return;
    const filter = UI.selectedDirectorFilter;
    const viewer = UI.viewingDirector, acting = UI.actingDirector;
    const rules = scopesForViewer(viewer);
    let rows = (s.queue || []).slice();
    if (filter !== "all") rows = rows.filter(q => q.owning_director === filter);
    else if (!rules.edit_all && viewer) rows = rows.filter(q => q.owning_director === viewer);
    rows = rows.sort((a, b) => b.score - a.score);
    $("#queue-count").textContent = rows.length + " pending";
    if (!rows.length){
      list.innerHTML = `<div style="padding:20px;text-align:center;color:var(--adam-text-mute)">
        <span class="dot green"></span> No exceptions in queue${filter !== "all" ? " for this director" : ""}.</div>`;
      return;
    }
    const directors = (s.directors || UI.bootstrap?.directors || []);
    list.innerHTML = rows.map(q => {
      const dir = directors.find(d => d.id === q.owning_director);
      const dirTitle = dir ? dir.title : q.owning_director;
      const editable = canEdit(acting, q.owning_director);
      const dis = editable ? "" : "disabled";
      return `
        <div class="queue-item tier-${esc(q.tier)}" data-intent="${esc(q.intent_id)}" tabindex="0" role="button">
          <div class="queue-score">${q.score}</div>
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
            <button class="btn approve" ${dis} data-action="approve" data-intent="${esc(q.intent_id)}">Approve</button>
            <button class="btn modify"  ${dis} data-action="modify"  data-intent="${esc(q.intent_id)}">Modify</button>
            <button class="btn danger"  ${dis} data-action="reject"  data-intent="${esc(q.intent_id)}">Reject</button>
            <button class="btn deny"    ${dis} data-action="deny"    data-intent="${esc(q.intent_id)}">Deny</button>
          </div>
        </div>`;
    }).join("");
  }

  function renderTwins(s){
    const root = $("#twin-grid"); if (!root) return;
    root.innerHTML = "";
    const usage = s.twin_usage || [];
    for (const t of usage){
      const agent = Object.values(s.agent_classes || {}).flatMap(c => c.agents).find(a => a.id === t.id);
      const maxC = Math.max(...usage.map(x => x.consultations_24h));
      const pct = Math.round(t.consultations_24h * 100 / (maxC || 1));
      const div = t.divergence_pct;
      const col = div >= 2 ? "var(--tier-high)" : div >= 1 ? "var(--tier-elevated)" : "var(--tier-soap)";
      root.insertAdjacentHTML("beforeend", `
        <div class="twin-card">
          <h5><span class="dot green"></span>${esc(agent?.name || t.id)}</h5>
          <div class="panel-sub" style="font-size:11px;">${esc(agent?.purpose || "")}</div>
          <div class="twin-stat"><span>Consultations (24h)</span><b>${fmtNum(t.consultations_24h)}</b></div>
          <div class="twin-bar"><span style="width:${pct}%"></span></div>
          <div class="twin-stat"><span>Avg latency</span><b>${t.avg_latency_ms} ms</b></div>
          <div class="twin-stat"><span>Live simulations</span><b>${t.simulations_running}</b></div>
          <div class="twin-stat"><span>Divergence</span><b style="color:${col}">${(t.divergence_pct||0).toFixed(1)}%</b></div>
        </div>`);
    }
  }

  function renderRouting(s){
    const r = s.routing_24h || {};
    const total = (r.soap||0)+(r.moderate||0)+(r.elevated||0)+(r.high||0)+(r.ohshat||0);
    $("#routing-total").textContent = fmtNum(total) + " decisions / 24h";
    $("#routing").innerHTML = `
      <div class="cell soap"    ><b>${fmtNum(r.soap||0)}</b>SOAP</div>
      <div class="cell moderate"><b>${fmtNum(r.moderate||0)}</b>Moderate</div>
      <div class="cell elevated"><b>${fmtNum(r.elevated||0)}</b>Elevated</div>
      <div class="cell high"    ><b>${fmtNum(r.high||0)}</b>High</div>
      <div class="cell ohshat"  ><b>${fmtNum(r.ohshat||0)}</b>OHSHAT</div>`;
  }

  function renderFlightTail(s){
    const tail = s.flight_recorder || []; const el = $("#fr-tail"); if (!el) return;
    el.innerHTML = tail.slice(-30).reverse().map(r => `
      <div class="fr-row" data-intent="${esc(r.intent_id)}" role="button" tabindex="0">
        <span class="seq">#${r.seq}</span>
        <span class="${tierClass(r.tier)}" style="font-size:10px;padding:1px 6px">${esc(r.tier||"—")}</span>
        <span><span class="ev">${esc(r.event_type)}</span> <span style="color:var(--adam-text-mute)">${esc(r.agent_id)}</span></span>
        <span style="color:var(--adam-text-mute)">${esc((r.intent_id||"").slice(0,8))}…</span>
      </div>`).join("");
  }

  /* Conversational panels */
  function addBubble(where, who, html, meta){
    const log = $("#" + where); if (!log) return;
    const b = document.createElement("div");
    b.className = "bubble " + who;
    b.innerHTML = html + (meta ? `<small>${esc(meta)}</small>` : "");
    log.appendChild(b);
    log.scrollTop = log.scrollHeight;
  }

  function recordIntent(entry){
    UI.history = UI.history.filter(x => x.intent_id !== entry.intent_id);
    UI.history.unshift(entry);
    if (UI.history.length > 200) UI.history.length = 200;
  }

  function inferDirector(dims){
    if (!dims || !Object.keys(dims).length) return "ceo";
    const top = Object.entries(dims).sort((a,b)=>b[1]-a[1])[0][0];
    return ({financial_exposure:"cfo", regulatory_impact:"legal_director", rights_certainty:"legal_director",
             security_impact:"ciso", sovereignty_action:"ciso", reputational_risk:"market_director",
             doctrinal_alignment:"ceo"})[top] || "ceo";
  }

  function localInterpret(text, nonIdem){
    const dims = { security_impact:5, sovereignty_action:5, financial_exposure:5,
                   regulatory_impact:5, reputational_risk:5, rights_certainty:5, doctrinal_alignment:10 };
    const triggered = [];
    const m = text.match(/\$\s?([\d,]+(?:\.\d+)?)/);
    if (m){ const amt = parseFloat(m[1].replace(/,/g,""));
      for (const [max, sc] of [[50000,80],[10000,55],[2500,35],[500,15],[100,5]]){
        if (amt >= max){ dims.financial_exposure = sc; triggered.push("financial_exposure"); break; }
      }
    }
    if (/(pii|customer data|egress|breach|leak|ransom)/i.test(text)){ dims.security_impact = Math.max(dims.security_impact, 75); triggered.push("security_impact"); }
    if (/(gdpr|ccpa|dora|nis2|regulator|compliance|license|rights)/i.test(text)){ dims.regulatory_impact = Math.max(dims.regulatory_impact, 55); triggered.push("regulatory_impact"); }
    if (/(campaign|brand|marketing|ad|press)/i.test(text)){ dims.reputational_risk = Math.max(dims.reputational_risk, 40); triggered.push("reputational_risk"); }
    if (/(deploy|rollout|incident|outage|scale|migrat)/i.test(text)){ dims.doctrinal_alignment = Math.max(dims.doctrinal_alignment, 35); triggered.push("doctrinal_alignment"); }
    if (/(sacred|minor|exploit|sanction|weapon)/i.test(text)){ dims.security_impact = 95; dims.doctrinal_alignment = 90; triggered.push("sacred_boundary"); }
    const w = UI.state?.boss?.dimensions || { security_impact:5, sovereignty_action:4, financial_exposure:4,
                                                regulatory_impact:3, reputational_risk:3, rights_certainty:3, doctrinal_alignment:2 };
    const sum = Object.values(w).reduce((a,b)=>a+b,0) || 24;
    let comp = Object.entries(w).reduce((acc,[k,wk]) => acc + (dims[k]||0)*wk, 0) / sum;
    const maxDim = Math.max(...Object.values(dims));
    if (maxDim > 75) comp = Math.max(comp, maxDim - 10);
    if (nonIdem) comp += 15;
    comp = Math.min(100, Math.round(comp));
    const tier = comp >= 76 ? "OHSHAT" : comp >= 51 ? "HIGH" : comp >= 31 ? "ELEVATED" : comp >= 11 ? "MODERATE" : "SOAP";
    return { tier, score: comp, dimensions: dims, triggered_by: triggered, director: inferDirector(dims) };
  }

  function renderIntentBubble(id, text, score, tier, dims, ownerId){
    const dimList = Object.entries(dims).map(([k, v]) => `
      <div class="dim-row"><span>${esc(k)}</span><span>${v}</span>
        <div class="bar"><span class="s-${tierKey(tierFromScore(v))}" style="width:${v}%"></span></div></div>`).join("");
    const directors = (UI.state?.directors || UI.bootstrap?.directors || []);
    const dir = directors.find(d => d.id === ownerId);
    addBubble("intent-log", "adam",
      `Interpreted. Tier <span class="${tierClass(tier)}">${esc(tier)}</span>, composite <b>${score}</b>.<br>
       <small>intent_id: <code>${esc(id || "")}</code></small>
       <div class="dims-grid">${dimList}</div>
       <small>Routed to <b>${esc(dir?.title || ownerId)}</b>.</small>`,
      `hi-intent · ${new Date().toLocaleTimeString()}`);
  }

  async function submitIntent(text, nonIdem){
    addBubble("intent-log", "you", esc(text));
    const out = localInterpret(text, nonIdem);
    const id = "sim-" + Math.random().toString(16).slice(2, 12);
    renderIntentBubble(id, text, out.score, out.tier, out.dimensions, out.director);
    recordIntent({ intent_id:id, text, summary:text.slice(0,160), tier:out.tier, score:out.score,
                   dimensions:out.dimensions, triggered_by:out.triggered_by, owning_director:out.director,
                   non_idempotent:!!nonIdem, recommendation:"review", confidence_pct:60,
                   source:"this session · demo", queued_at:new Date().toISOString() });
    if (["HIGH","OHSHAT","ELEVATED"].includes(out.tier)){
      (UI.state.queue ||= []).unshift({
        intent_id:id, queued_at:new Date().toISOString(), owning_director:out.director,
        tier:out.tier, score:out.score, summary:text.slice(0,120), raw_text:text,
        dimensions:out.dimensions, non_idempotent:!!nonIdem, triggered_by:out.triggered_by,
        alternatives:[], recommendation:"review", confidence_pct:60, time_sensitivity_hours:24
      });
      renderQueue(UI.state); renderDirectorRoster(UI.state);
      const directors = (UI.state.directors || UI.bootstrap?.directors || []);
      addBubble("intent-log", "adam",
        `Escalation packet queued for <b>${esc(directors.find(d=>d.id===out.director)?.title || out.director)}</b>.`,
        "hi-gateway");
    }
  }

  /* Explain-Back */
  function buildIntentIndex(){
    const map = new Map();
    for (const q of (UI.state?.queue || [])){
      map.set(q.intent_id, { intent_id:q.intent_id, text:q.raw_text || q.summary || "",
        summary:q.summary || q.raw_text || "", tier:q.tier, score:q.score,
        dimensions:q.dimensions || {}, triggered_by:q.triggered_by || [],
        owning_director:q.owning_director, non_idempotent:!!q.non_idempotent,
        recommendation:q.recommendation, confidence_pct:q.confidence_pct,
        source:"pending queue", queued_at:q.queued_at });
    }
    for (const h of UI.history) if (!map.has(h.intent_id)) map.set(h.intent_id, h);
    return [...map.values()];
  }

  function fuzzyScore(query, candidate){
    const norm = s => String(s||"").toLowerCase().replace(/[^a-z0-9$.]+/g, " ").trim();
    const STOP = new Set(["the","a","an","to","of","for","on","in","at","and","or","is","be","with","from","into","by","as","that","this","it","approve","approved","approval"]);
    const qTok = norm(query).split(/\s+/).filter(t => t && !STOP.has(t));
    const cTok = new Set(norm(candidate).split(/\s+/).filter(t => t && !STOP.has(t)));
    if (!qTok.length || !cTok.size) return 0;
    let hit = 0;
    for (const t of qTok){
      if (cTok.has(t)){ hit += 2; continue; }
      for (const c of cTok) if (c.includes(t) || t.includes(c)){ hit += 1; break; }
    }
    return hit / Math.max(qTok.length * 2, 1);
  }

  function renderExplainPacket(intent){
    const dimOrdered = Object.entries(intent.dimensions || {}).sort((a,b)=>b[1]-a[1]);
    const dimHtml = dimOrdered.map(([k,v]) => `
      <div class="dim-row"><span>${esc(k)}</span><span>${v}</span>
        <div class="bar"><span class="s-${tierKey(tierFromScore(v))}" style="width:${v}%"></span></div></div>`).join("");
    const directors = (UI.state?.directors || UI.bootstrap?.directors || []);
    const dir = directors.find(d => d.id === intent.owning_director);
    addBubble("explain-log", "adam",
      `<b>Intent ${esc(intent.intent_id.slice(0,8))}… — <span class="${tierClass(intent.tier)}">${esc(intent.tier || "—")}</span> (composite ${intent.score || "—"})</b><br>
       <i>${esc(intent.summary || intent.text || "")}</i>
       <div class="dims-grid" style="margin-top:10px">${dimHtml || "<small>No dimension data.</small>"}</div>
       <p><b>Primary triggers:</b> ${(intent.triggered_by || []).map(t => `<code>${esc(t)}</code>`).join(", ") || "—"}.<br>
       <b>Routed to:</b> ${esc(dir?.title || intent.owning_director || "—")}</p>
       <small style="color:var(--adam-text-mute)">source: ${esc(intent.source || "queue")}</small>
       <div style="margin-top:6px"><button class="btn primary" data-open-intent="${esc(intent.intent_id)}">Open Intent Object Card →</button></div>`,
      `hi-explain · full packet`);
  }

  function renderExplainMatches(query, matches){
    const rows = matches.map(m => `
      <div class="match-option" data-intent="${esc(m.intent_id)}" role="button" tabindex="0"
           style="display:grid;grid-template-columns:auto 1fr auto;gap:8px;align-items:center;
                  padding:8px 10px;border:1px solid var(--adam-line-soft);border-radius:6px;
                  background:rgba(255,255,255,.02);cursor:pointer;margin-top:6px;">
        <span class="${tierClass(m.tier)}">${esc(m.tier||"—")}</span>
        <span style="font-size:12px">${esc((m.summary || m.text || "").slice(0, 120))}</span>
        <span style="font-family:var(--font-mono);font-size:11px;color:var(--adam-text-mute)">${esc((m.intent_id||"").slice(0,8))}…</span>
      </div>`).join("");
    addBubble("explain-log", "adam",
      `I found <b>${matches.length}</b> intents matching "<i>${esc(query)}</i>". Click the one you meant:
       <div style="margin-top:6px">${rows}</div>`, "hi-explain · fuzzy match");
  }

  async function explainIntent(text){
    const q = String(text || "").trim(); if (!q) return;
    addBubble("explain-log", "you", esc(q));
    const looksLikeId = /^[a-f0-9][a-f0-9-]{5,}$/i.test(q);
    const idx = buildIntentIndex();
    if (looksLikeId){
      const byId = idx.find(i => i.intent_id === q || i.intent_id.startsWith(q));
      if (byId){ renderExplainPacket(byId); return; }
    }
    if (!idx.length){
      addBubble("explain-log", "adam",
        `I don't have any intents in the session index yet. Submit one through the Intent Agent.`,
        "hi-explain"); return;
    }
    const scored = idx
      .map(i => ({ i, s: fuzzyScore(q, (i.summary || "") + " " + (i.text || "")) }))
      .filter(r => r.s >= 0.15).sort((a, b) => b.s - a.s);
    if (!scored.length){
      addBubble("explain-log", "adam",
        `No intents match "<i>${esc(q)}</i>". Try a keyword from the original intent.`,
        "hi-explain"); return;
    }
    if (scored.length === 1 || scored[0].s - scored[1].s > 0.25){ renderExplainPacket(scored[0].i); return; }
    renderExplainMatches(q, scored.slice(0, Math.min(6, scored.length)).map(r => r.i));
  }

  function localComposite(dims, non_idem){
    const w = UI.state?.boss?.dimensions || { security_impact:5, sovereignty_action:4, financial_exposure:4,
                                                regulatory_impact:3, reputational_risk:3, rights_certainty:3, doctrinal_alignment:2 };
    const sum = Object.values(w).reduce((a,b)=>a+b, 0) || 24;
    let c = Object.entries(w).reduce((acc,[k,wk]) => acc + (dims[k]||0)*wk, 0) / sum;
    const maxDim = Math.max(...Object.values(dims || {0:0}));
    if (maxDim > 75) c = Math.max(c, maxDim - 10);
    if (non_idem) c += 15;
    c = Math.min(100, Math.round(c));
    const tier = c >= 76 ? "OHSHAT" : c >= 51 ? "HIGH" : c >= 31 ? "ELEVATED" : c >= 11 ? "MODERATE" : "SOAP";
    return { score:c, tier };
  }

  /* Agent Card */
  async function openAgentCard(agentId){
    if (!agentInScope(agentId, UI.viewingDirector)){
      toast(`${agentId} is outside the ${UI.viewingDirector.toUpperCase()} dashboard scope.`, "warn");
      return;
    }
    let card = null;
    if (DataSource.apiAvailable) card = await DataSource.agentCard(agentId, UI.mode);
    if (!card){
      const a = Object.values(UI.state?.agent_classes || {}).flatMap(c => c.agents).find(x => x.id === agentId);
      const st = (UI.state?.agent_state || {})[agentId];
      const tail = (UI.state?.flight_recorder || []).filter(e => e.agent_id === agentId).slice(-30).reverse();
      card = { ok:true, agent_id:agentId, agent: a || {id:agentId, name:agentId},
               state: st || {id:agentId, status:"unknown"}, events: tail,
               controls_supported:["start","restart","diagnose","safe_mode"] };
    }
    const a = card.agent || {}, st = card.state || {}, events = card.events || [];
    $("#agent-card-title").innerHTML = `<span class="dot ${st.status==="down"?"red":st.status==="escalation"?"amber":"green"}"></span> ${esc(a.name || a.id)}`;
    $("#agent-card-sub").textContent = `${esc(a.id)} · ${esc(card.class || a.accountable_to || "")}`;
    const eventsHtml = events.map(ev => {
      const evid = ev.evidence || {};
      const tier = evid.tier || "—";
      return `<div class="fr-row" data-intent="${esc(evid.intent_id || ev.intent_id || "")}" role="button" tabindex="0">
                <span class="seq">#${ev.seq || "—"}</span>
                <span class="${tierClass(tier)}" style="font-size:10px;padding:1px 6px">${esc(tier)}</span>
                <span><span class="ev">${esc(ev.event_type)}</span> <span style="color:var(--adam-text-mute)">${esc((ev.timestamp || ev.ts || "").slice(11,19))}</span></span>
                <span style="color:var(--adam-text-mute)">${esc((evid.intent_id || ev.intent_id || "—").slice(0,8))}…</span>
              </div>`;
    }).join("") || `<div style="color:var(--adam-text-mute)">No events yet.</div>`;
    $("#agent-card-body").innerHTML = `
      <div class="a-grid">
        <div>
          <div class="metric-card">
            <h5>Current state</h5>
            <div class="big">${esc((st.status || "—").toUpperCase())}</div>
            <div class="metric-row"><span>Step</span><b>${esc(st.current_step || "—")}</b></div>
            <div class="metric-row"><span>Last event</span><b>${esc((st.last_event || "—").replace("T"," ").slice(0,19))}</b></div>
          </div>
          <div class="metric-card" style="margin-top:10px">
            <h5>Pressure</h5>
            <div class="metric-row"><span>CPU</span><b>${st.cpu_pct || 0}%</b></div>
            <div class="metric-row"><span>Memory</span><b>${st.mem_pct || 0}%</b></div>
            <div class="metric-row"><span>Queue depth</span><b>${st.queue_depth || 0}</b></div>
            <div class="metric-row"><span>Inflight</span><b>${st.inflight || 0}</b></div>
          </div>
          <div class="metric-card" style="margin-top:10px">
            <h5>Identity</h5>
            <div class="kv-grid">
              <span>id</span><b>${esc(a.id)}</b>
              <span>name</span><b>${esc(a.name)}</b>
              <span>class</span><b>${esc(card.class || "—")}</b>
              ${a.sub_group ? `<span>sub-group</span><b>${esc(a.sub_group)}</b>` : ""}
              ${a.accountable_to ? `<span>accountable to</span><b>${esc(a.accountable_to)}</b>` : ""}
              ${a.boss_dims?.length ? `<span>BOSS dims</span><b>${esc(a.boss_dims.join(", "))}</b>` : ""}
            </div>
          </div>
        </div>
        <div>
          <h5 class="panel-h4" style="margin-top:0">Recent Flight Recorder events for this agent</h5>
          <div class="scroller">${eventsHtml}</div>
          <div style="margin-top:14px;font-size:11px;color:var(--adam-text-mute)">
            Director controls below are gated. Acting <b>${esc(UI.actingDirector.toUpperCase())}</b> ·
            ${canEdit(UI.actingDirector, UI.actingDirector) && agentInScope(agentId, UI.actingDirector) ? "✅ allowed" : "⛔ read-only"}.
          </div>
        </div>
      </div>`;
    const allowed = agentInScope(agentId, UI.actingDirector) && canEdit(UI.actingDirector, UI.actingDirector);
    ["agent-start","agent-restart","agent-diagnose","agent-safemode"].forEach(id => {
      const b = $("#" + id);
      b.classList.toggle("disabled", !allowed);
      b.dataset.agent = agentId;
    });
    $("#agent-card-root").hidden = false;
  }
  function closeAgentCard(){ $("#agent-card-root").hidden = true; }

  async function agentControl(agentId, action){
    if (!agentInScope(agentId, UI.actingDirector)){ toast("This agent is outside your scope.", "err"); return; }
    const aid = actionId(agentId, action, UI.actingDirector);
    const payload = { action, director_id: UI.actingDirector, action_id: aid, comment: "" };
    let resp = null;
    if (DataSource.apiAvailable) resp = await DataSource.submitAgentControl(agentId, payload);
    else                          resp = { ok:true, idempotent:false, action_id:aid, demo:true };
    if (resp?.ok && resp.idempotent) toast(`Already recorded - idempotent reuse of ${aid.slice(0,8)}...`, "warn");
    else if (resp?.ok)               toast(`${action} recorded on the chain for ${agentId}. Refreshing...`, "ok");
    else                            { toast(`Control failed: ${esc(resp?.error || "unknown")}`, "err"); return; }
    // Re-open the same agent card so the user immediately sees the new state.
    // The chain entry has just landed; FR /replay returns it on the next call.
    if (resp?.ok) {
      // Brief delay so the FR cache TTL expires and the new event surfaces.
      setTimeout(() => openAgentCard(agentId), 1700);
      // Also refresh the global state for tile/queue updates.
      setTimeout(refresh, 1700);
    }
  }

  /* Intent Object Card */
  async function openIntentCard(intentId){
    let card = null;
    if (DataSource.apiAvailable) card = await DataSource.intentCard(intentId, UI.mode);
    if (!card?.ok){
      const q = (UI.state?.queue || []).find(x => x.intent_id === intentId);
      if (q){
        card = { ok:true, intent_id:intentId, intent:q,
                 composite: localComposite(q.dimensions, q.non_idempotent),
                 events: (UI.state?.flight_recorder || []).filter(e => e.intent_id === intentId), decisions:[] };
      } else { toast(`Intent ${intentId.slice(0,8)}… not found in current state.`, "warn"); return; }
    }
    const i = card.intent || {}, dims = i.dimensions || {};
    const composite = card.composite || localComposite(dims, i.non_idempotent);
    const directors = (UI.state?.directors || UI.bootstrap?.directors || []);
    const dir = directors.find(d => d.id === i.owning_director);
    const editable = canEdit(UI.actingDirector, i.owning_director);
    const dimHtml = Object.entries(dims).sort((a,b)=>b[1]-a[1])
      .map(([k,v]) => `<div class="dim-row"><span>${esc(k)}</span><span>${v}</span>
        <div class="bar"><span class="s-${tierKey(tierFromScore(v))}" style="width:${v}%"></span></div></div>`).join("");
    const altHtml = (i.alternatives || []).map(a =>
      `<li>${esc(a.label)} → projected composite <b>${a.projected_score}</b></li>`).join("") || "<li>No alternatives available.</li>";
    const trigHtml = (i.triggered_by || []).map(t => `<code>${esc(t)}</code>`).join(", ") || "—";
    const eventsHtml = (card.events || []).map(ev => {
      const evid = ev.evidence || {};
      const tier = evid.tier || ev.tier || "—";
      return `<div class="fr-row">
                <span class="seq">#${ev.seq || "—"}</span>
                <span class="${tierClass(tier)}" style="font-size:10px;padding:1px 6px">${esc(tier)}</span>
                <span><span class="ev">${esc(ev.event_type)}</span> <span style="color:var(--adam-text-mute)">${esc(ev.agent_id)}</span></span>
                <span style="color:var(--adam-text-mute)">${esc((ev.timestamp || ev.ts || "").replace("T"," ").slice(0,19))}</span>
              </div>`;
    }).join("") || `<div style="color:var(--adam-text-mute)">No Flight Recorder events yet for this intent.</div>`;
    const decisionsHtml = (card.decisions || []).map(d => `
      <div class="fr-row">
        <span class="seq">#${d.seq || "—"}</span>
        <span class="pill pill-${d.decision === "approval" || d.decision === "approve" ? "SOAP" : "OHSHAT"}" style="font-size:10px;padding:1px 6px">${esc(d.decision || "")}</span>
        <span>${esc(d.director || "")} · ${esc(d.acting_person || "—")} · ${esc(d.comment || "")}</span>
        <span style="color:var(--adam-text-mute)">${esc((d.ts || "").replace("T"," ").slice(0,19))}</span>
      </div>`).join("");
    $("#intent-card-title").innerHTML = `<span class="${tierClass(composite.tier)}">${esc(composite.tier)}</span> · Intent ${esc(intentId.slice(0,8))}…`;
    $("#intent-card-sub").textContent = `Owner: ${dir?.title || i.owning_director || "—"} · ${i.time_sensitivity_hours || "?"}h SLA · ${i.confidence_pct || "?"}% confidence`;
    $("#intent-card-body").innerHTML = `
      <h4 style="margin:0 0 4px">${esc(i.summary || "")}</h4>
      <div class="composite-badge"><span>Composite</span><b>${composite.score}</b><span>${esc(composite.tier)}</span></div>
      <div style="margin-top:12px;font-size:12px;color:var(--adam-text-dim)">Original intent text</div>
      <div style="padding:10px;background:rgba(0,0,0,.3);border:1px solid var(--adam-line-soft);border-radius:6px;font-size:13px;margin-top:4px">${esc(i.raw_text || i.summary || "—")}</div>
      <h5 class="panel-h4">BOSS v3.2 visual dimension breakdown</h5>
      <div class="dim-bars">${dimHtml || "<small>No dimension data.</small>"}</div>
      <h5 class="panel-h4">Triggers</h5>
      <div>${trigHtml}</div>
      <h5 class="panel-h4">Alternatives</h5>
      <ul style="margin:4px 0 0 18px;padding:0">${altHtml}</ul>
      <h5 class="panel-h4">Flight Recorder entries (scrollable)</h5>
      <div class="scroller">${eventsHtml}</div>
      ${decisionsHtml ? `<h5 class="panel-h4">Director decisions recorded</h5><div class="scroller">${decisionsHtml}</div>` : ""}
      <div style="margin-top:14px;font-size:11px;color:var(--adam-text-mute)">
        Acting <b>${esc(UI.actingDirector.toUpperCase())}</b> · ${editable ? "✅ may decide" : "⛔ read-only"}
      </div>`;
    ["intent-approve","intent-modify","intent-reject","intent-deny","intent-defer","intent-comment"].forEach(id => {
      const b = $("#" + id);
      b.classList.toggle("disabled", !editable);
      b.dataset.intent = intentId;
      b.dataset.owner = i.owning_director || "ceo";
    });
    $("#intent-card-root").hidden = false;
  }
  function closeIntentCard(){ $("#intent-card-root").hidden = true; }

  /* Director Action workflow */
  function openActionWorkflow(intentId, decision){
    const q = (UI.state?.queue || []).find(x => x.intent_id === intentId);
    if (!q){ toast(`Intent ${intentId.slice(0,8)}… not in queue.`, "warn"); return; }
    const editable = canEdit(UI.actingDirector, q.owning_director);
    if (!editable){ toast(`Read-only — only ${q.owning_director.toUpperCase()} / CEO / CISO can decide.`, "err"); return; }
    const directors = (UI.state.directors || UI.bootstrap?.directors || []);
    const dir = directors.find(d => d.id === q.owning_director);
    const aDecision = (decision || "approve").toLowerCase();
    const labelMap = {
      approve:"Approve & Sign", reject:"Reject", modify:"Modify",
      deny:"Deny (with prejudice)", defer:"Defer", comment:"Comment only" };
    $("#action-title").innerHTML = `<span class="${tierClass(q.tier)}">${esc(q.tier)}</span> · ${esc(labelMap[aDecision] || aDecision)}`;
    $("#action-sub").textContent = `Intent ${q.intent_id.slice(0,8)}… · Owner ${dir?.title || q.owning_director} · Acting ${UI.actingDirector.toUpperCase()}`;
    const dimsRows = Object.entries(q.dimensions || {}).map(([k, v]) => `
      <div>${esc(k)}</div>
      <input type="number" min="0" max="100" value="${v}" data-dim="${esc(k)}" class="wf-dim">
      <div data-dim-current="${esc(k)}" style="text-align:right;font-family:var(--font-mono);color:var(--adam-text-mute)">was ${v}</div>`).join("");
    $("#action-body").innerHTML = `
      <div class="field">
        <label>What you are doing</label>
        <select id="wf-decision">
          <option value="approve" ${aDecision==="approve"?"selected":""}>Approve & Sign — write director_approval</option>
          <option value="modify"  ${aDecision==="modify"?"selected":""}>Modify — record desired changes & approve</option>
          <option value="reject"  ${aDecision==="reject"?"selected":""}>Reject — write director_rejection</option>
          <option value="deny"    ${aDecision==="deny"?"selected":""}>Deny (with prejudice) — close & block re-route</option>
          <option value="defer"   ${aDecision==="defer"?"selected":""}>Defer — leave queued, push SLA</option>
          <option value="comment" ${aDecision==="comment"?"selected":""}>Comment only — annotate, no decision</option>
        </select>
      </div>
      <div class="field">
        <label>Director comment (recorded as evidence)</label>
        <textarea id="wf-comment" placeholder="Why this decision? Attach any context, conditions, or expected follow-up."></textarea>
      </div>
      <div class="field">
        <label>Modifications (only used by Modify; free-text accepted)</label>
        <textarea id="wf-modifications" placeholder="e.g., reduce vendor amount to $5,000 with 6-month term."></textarea>
      </div>
      <div class="field">
        <label>What-if scenario — adjust dimension values to see the impact</label>
        <div class="what-if-grid"><b>Dimension</b><b>New</b><b>Was</b>${dimsRows}</div>
        <div style="margin-top:6px">
          <label style="text-transform:none;letter-spacing:0;color:var(--adam-text)">
            <input type="checkbox" id="wf-nonidem" ${q.non_idempotent ? "checked" : ""}> mark non-idempotent (+15)
          </label>
          <button class="btn" type="button" id="wf-recompute">Recompute composite</button>
        </div>
        <div class="what-if-result" id="wf-result">Click <b>Recompute composite</b> to see the projected tier.</div>
      </div>
      <div class="field" style="font-size:11px;color:var(--adam-text-mute)">
        Signed via Flight Recorder HSM (Ed25519 / ML-DSA-65). Idempotent on action_id. Companion director_proxy_acting written.
      </div>`;
    $("#action-submit").dataset.intent = intentId;
    $("#action-submit").dataset.owner = q.owning_director;
    $("#action-root").hidden = false;
    $("#wf-recompute").addEventListener("click", async () => {
      const overrides = {};
      $$(".wf-dim").forEach(inp => overrides[inp.dataset.dim] = Math.max(0, Math.min(100, parseInt(inp.value || "0", 10))));
      const non_idem = $("#wf-nonidem").checked;
      let resp = null;
      if (DataSource.apiAvailable) resp = await DataSource.whatIf(intentId, overrides, non_idem);
      const base = localComposite(q.dimensions, q.non_idempotent);
      const mod  = resp?.modified || localComposite(overrides, non_idem);
      const delta = mod.score - base.score;
      const arrow = delta > 0 ? "▲" : delta < 0 ? "▼" : "▷";
      $("#wf-result").innerHTML = `Base composite <b>${base.score}</b> ${esc(base.tier)} → projected <b>${mod.score}</b> ${esc(mod.tier)} <span style="color:${delta>0?"var(--tier-high)":delta<0?"var(--tier-soap)":"var(--adam-text-mute)"}">(${arrow} ${Math.abs(delta)})</span>`;
    });
  }
  function closeActionWorkflow(){ $("#action-root").hidden = true; }

  async function submitActionWorkflow(){
    const intentId = $("#action-submit").dataset.intent;
    const owner    = $("#action-submit").dataset.owner;
    const decision = $("#wf-decision").value;
    const comment  = $("#wf-comment").value.trim();
    const modifications_text = $("#wf-modifications").value.trim();
    const overrides = {};
    $$(".wf-dim").forEach(inp => overrides[inp.dataset.dim] = Math.max(0, Math.min(100, parseInt(inp.value || "0", 10))));
    const non_idem = $("#wf-nonidem")?.checked;
    const aid = actionId(intentId, decision, UI.actingDirector, comment.slice(0, 64));
    const payload = {
      decision, action_id: aid, director_id: UI.actingDirector, owning_director: owner,
      comment, modifications: { text: modifications_text, dimension_overrides: overrides, non_idempotent: !!non_idem },
      what_if: { dimension_overrides: overrides, non_idempotent: !!non_idem }
    };
    let resp;
    if (DataSource.apiAvailable) resp = await DataSource.submitDecision(intentId, payload);
    else                          resp = { ok:true, idempotent:false, action_id:aid, demo:true };
    if (!resp?.ok)                toast(`Decision failed: ${esc(resp?.error || "unknown")}`, "err");
    else if (resp.idempotent)     toast(`Already recorded — idempotent reuse of ${aid.slice(0,8)}…`, "warn");
    else                           toast(`${decision.toUpperCase()} recorded for ${intentId.slice(0,8)}… (action_id ${aid.slice(0,8)}…).`, "ok");
    if (decision !== "comment" && decision !== "defer"){
      UI.state.queue = (UI.state.queue || []).filter(x => x.intent_id !== intentId);
    }
    (UI.state.flight_recorder ||= []).push({
      seq: ((UI.state.flight_recorder.slice(-1)[0]?.seq) || 10500) + 1,
      ts: new Date().toISOString(),
      event_type: "director_" + (decision === "approve" ? "approval" : decision === "reject" ? "rejection" : decision === "modify" ? "modified" : decision === "deny" ? "denied" : decision === "defer" ? "deferred" : "comment"),
      agent_id: "hi-gateway", tier: "—", intent_id: intentId
    });
    closeActionWorkflow(); closeIntentCard();
    renderQueue(UI.state); renderDirectorRoster(UI.state); renderFlightTail(UI.state);
  }

  /* Toast + tooltip */
  function toast(msg, kind = "ok"){
    const host = $("#toast-host"); if (!host) return;
    const el = document.createElement("div");
    el.className = "toast " + kind; el.innerHTML = msg;
    host.appendChild(el);
    setTimeout(() => { el.style.opacity = "0"; el.style.transition = "opacity .3s"; }, 2500);
    setTimeout(() => el.remove(), 3000);
  }

  function showTooltip(ev){
    const el = ev.target.closest(".agent-tile"); if (!el) return;
    const id = el.dataset.agentId;
    const st = (UI.state?.agent_state || {})[id] || {};
    const agent = Object.values(UI.state?.agent_classes || {}).flatMap(c => c.agents).find(a => a.id === id);
    if (!agent) return;
    const tt = $("#tooltip");
    tt.innerHTML = `
      <b>${esc(agent.name)}</b><br>
      <span style="color:var(--adam-text-mute)">${esc(id)}</span><br>
      <span class="pill pill-${st.status==='down'?'OHSHAT':st.status==='escalation'?'HIGH':'SOAP'}">${esc(st.status)}</span><br>
      <span style="color:var(--adam-text-dim);font-size:11px">${esc(st.current_step||"")}</span><br>
      CPU ${st.cpu_pct||0}% · Mem ${st.mem_pct||0}% · Q ${st.queue_depth||0}<br>
      <span style="color:var(--adam-accent);font-size:11px">click to open Agent Card →</span>`;
    tt.classList.add("show");
    const r = el.getBoundingClientRect();
    tt.style.left = Math.min(window.innerWidth - 300, r.left + 18) + "px";
    tt.style.top  = (r.top - 8 - tt.offsetHeight) + "px";
    if (parseInt(tt.style.top) < 0) tt.style.top = (r.bottom + 8) + "px";
  }
  function hideTooltip(){ $("#tooltip").classList.remove("show"); }

  /* Wiring */
  function wire(){
    $("#mode-select").addEventListener("change", async e => { UI.mode = e.target.value; $("#mode-chip").dataset.mode = UI.mode; await refresh(); });
    $("#director-select").addEventListener("change", e => { UI.actingDirector = e.target.value; renderAll(); });
    $("#viewing-select").addEventListener("change", e => { UI.viewingDirector = e.target.value; renderAll(); });
    $("#director-filter").addEventListener("change", e => { UI.selectedDirectorFilter = e.target.value; renderQueue(UI.state); });

    $("#intent-form").addEventListener("submit", e => {
      e.preventDefault();
      const t = $("#intent-input").value.trim(); if (!t) return;
      const ni = $("#intent-nonidem").checked;
      $("#intent-input").value = ""; $("#intent-nonidem").checked = false;
      submitIntent(t, ni);
    });
    $("#explain-form").addEventListener("submit", e => {
      e.preventDefault();
      const t = $("#explain-input").value.trim(); if (!t) return;
      $("#explain-input").value = "";
      explainIntent(t);
    });
    $("#explain-log").addEventListener("click", e => {
      const opt = e.target.closest(".match-option");
      if (opt){ const id = opt.dataset.intent; const hit = buildIntentIndex().find(i => i.intent_id === id); if (hit) renderExplainPacket(hit); return; }
      const open = e.target.closest("button[data-open-intent]");
      if (open){ openIntentCard(open.dataset.openIntent); return; }
    });
    $("#intent-log").addEventListener("click", e => {
      const open = e.target.closest("button[data-open-intent]");
      if (open) openIntentCard(open.dataset.openIntent);
    });
    $$(".example-chip").forEach(c => c.addEventListener("click", () => {
      document.getElementById(c.dataset.target).value = c.dataset.text;
      document.getElementById(c.dataset.target).focus();
    }));
    $("#queue-list").addEventListener("click", e => {
      const btn = e.target.closest("button[data-action]");
      if (btn){
        if (btn.classList.contains("disabled") || btn.disabled){ toast("Read-only for the acting director.", "err"); return; }
        openActionWorkflow(btn.dataset.intent, btn.dataset.action); return;
      }
      const row = e.target.closest(".queue-item");
      if (row) openIntentCard(row.dataset.intent);
    });
    $("#queue-list").addEventListener("keydown", e => {
      if (e.key === "Enter" || e.key === " "){
        const row = e.target.closest(".queue-item"); if (row){ e.preventDefault(); openIntentCard(row.dataset.intent); }
      }
    });
    $("#director-roster").addEventListener("click", e => {
      const card = e.target.closest(".director-card");
      if (card){ UI.viewingDirector = card.dataset.director; $("#viewing-select").value = UI.viewingDirector; renderAll(); }
    });
    $("#group-grid").addEventListener("click", e => {
      const tile = e.target.closest(".agent-tile"); if (!tile) return;
      openAgentCard(tile.dataset.agentId);
    });
    $("#group-grid").addEventListener("keydown", e => {
      if (e.key === "Enter" || e.key === " "){ const tile = e.target.closest(".agent-tile"); if (tile){ e.preventDefault(); openAgentCard(tile.dataset.agentId); } }
    });
    $("#group-grid").addEventListener("mouseover", showTooltip);
    $("#group-grid").addEventListener("mouseout",  hideTooltip);
    $("#group-grid").addEventListener("focusin",   showTooltip);
    $("#group-grid").addEventListener("focusout",  hideTooltip);
    $("#fr-tail").addEventListener("click", e => {
      const row = e.target.closest(".fr-row"); if (row && row.dataset.intent) openIntentCard(row.dataset.intent);
    });

    $("#modal-close").addEventListener("click", () => { $("#modal-root").hidden = true; });
    $("#modal-cancel").addEventListener("click", () => { $("#modal-root").hidden = true; });
    $("#modal-root").addEventListener("click", e => { if (e.target.id === "modal-root") $("#modal-root").hidden = true; });
    [["modal-approve","approve"],["modal-modify","modify"],["modal-reject","reject"],["modal-deny","deny"],["modal-defer","defer"],["modal-comment","comment"]].forEach(([id, dec]) => {
      $("#" + id).addEventListener("click", e => {
        if (e.currentTarget.classList.contains("disabled")){ toast("Read-only.", "err"); return; }
        $("#modal-root").hidden = true;
        openActionWorkflow(e.currentTarget.dataset.intent, dec);
      });
    });

    $("#agent-card-close").addEventListener("click", closeAgentCard);
    $("#agent-card-root").addEventListener("click", e => { if (e.target.id === "agent-card-root") closeAgentCard(); });
    $("#agent-start").addEventListener("click", e => { if (!e.currentTarget.classList.contains("disabled")) agentControl(e.currentTarget.dataset.agent, "start"); });
    $("#agent-restart").addEventListener("click", e => { if (!e.currentTarget.classList.contains("disabled")) agentControl(e.currentTarget.dataset.agent, "restart"); });
    $("#agent-diagnose").addEventListener("click", e => { if (!e.currentTarget.classList.contains("disabled")) agentControl(e.currentTarget.dataset.agent, "diagnose"); });
    $("#agent-safemode").addEventListener("click", e => { if (!e.currentTarget.classList.contains("disabled")) agentControl(e.currentTarget.dataset.agent, "safe_mode"); });
    $("#agent-card-body").addEventListener("click", e => {
      const row = e.target.closest(".fr-row");
      if (row && row.dataset.intent){ closeAgentCard(); openIntentCard(row.dataset.intent); }
    });

    $("#intent-card-close").addEventListener("click", closeIntentCard);
    $("#intent-card-root").addEventListener("click", e => { if (e.target.id === "intent-card-root") closeIntentCard(); });
    [["intent-approve","approve"],["intent-modify","modify"],["intent-reject","reject"],["intent-deny","deny"],["intent-defer","defer"],["intent-comment","comment"]].forEach(([id, dec]) => {
      $("#" + id).addEventListener("click", e => {
        if (e.currentTarget.classList.contains("disabled")){ toast("Read-only.", "err"); return; }
        openActionWorkflow(e.currentTarget.dataset.intent, dec);
      });
    });

    $("#action-close").addEventListener("click", closeActionWorkflow);
    $("#action-cancel").addEventListener("click", closeActionWorkflow);
    $("#action-root").addEventListener("click", e => { if (e.target.id === "action-root") closeActionWorkflow(); });
    $("#action-submit").addEventListener("click", submitActionWorkflow);

    $("#density").addEventListener("input", e => {
      document.documentElement.style.setProperty("--font-scale", e.target.value);
      document.body.style.fontSize = (parseFloat(e.target.value) * 14) + "px";
    });
    $("#refresh-btn").addEventListener("click", () => refresh());
    $("#export-btn").addEventListener("click", () => window.print());

    document.addEventListener("keydown", e => {
      if (e.key !== "Escape") return;
      if (!$("#action-root").hidden)         closeActionWorkflow();
      else if (!$("#intent-card-root").hidden) closeIntentCard();
      else if (!$("#agent-card-root").hidden)  closeAgentCard();
      else if (!$("#modal-root").hidden)       $("#modal-root").hidden = true;
    });
  }

  function pulse(){
    if (UI.mode === "demo" || !DataSource.apiAvailable){
      const ids = Object.keys(UI.state?.agent_state || {});
      for (let i = 0; i < 3; i++){
        const id = ids[Math.floor(Math.random() * ids.length)];
        const st = (UI.state.agent_state || {})[id]; if (!st) continue;
        st.cpu_pct = Math.max(2, Math.min(98, st.cpu_pct + ((Math.random() * 20 - 10) | 0)));
        st.last_event = new Date().toISOString();
      }
      if (Math.random() > 0.7){
        const id = ids[Math.floor(Math.random() * ids.length)];
        const st = (UI.state.agent_state || {})[id];
        if (st){
          const r = Math.random();
          st.status = r > 0.94 ? "down" : r > 0.82 ? "escalation" : "autonomous";
        }
      }
      const events = ["boss_scored","governor_evaluated","action_executed","twin_simulation_recorded","governors_concurred"];
      (UI.state.flight_recorder ||= []).push({
        seq: ((UI.state.flight_recorder.slice(-1)[0]?.seq) || 10500) + 1,
        ts: new Date().toISOString(),
        event_type: events[Math.floor(Math.random()*events.length)],
        agent_id: ids[Math.floor(Math.random() * ids.length)] || "orch-policy",
        tier: ["SOAP","MODERATE","ELEVATED","HIGH","OHSHAT"][Math.floor(Math.random()*5)],
        intent_id: "stream-" + Math.random().toString(16).slice(2, 10)
      });
      if (UI.state.flight_recorder.length > 200) UI.state.flight_recorder.splice(0, 50);
      UI.state.routing_24h = UI.state.routing_24h || { soap:0, moderate:0, elevated:0, high:0, ohshat:0 };
      UI.state.routing_24h.soap     += Math.floor(Math.random() * 3);
      UI.state.routing_24h.moderate += (Math.random() > 0.7 ? 1 : 0);
      renderGroupGrid(UI.state); renderFlightTail(UI.state); renderRouting(UI.state);
    } else {
      refresh();
    }
  }

  async function boot(){
    wire();
    await DataSource.probe();
    await bootstrap();
    UI.mode = $("#mode-select").value || "demo";
    await refresh();
    setInterval(pulse, CFG.pollMs);
  }
  document.addEventListener("DOMContentLoaded", boot);

  /* test hook */
  window.__ADAM_DASHBOARD__ = {
    UI, DataSource, refresh, openAgentCard, openIntentCard, openActionWorkflow,
    submitIntent, explainIntent, agentInScope, canEdit, actionId, localComposite
  };
})();
