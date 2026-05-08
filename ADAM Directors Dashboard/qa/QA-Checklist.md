# ADAM Directors Dashboard — manual QA checklist (v0.3)

Run this after every non-trivial change. v0.3 expands the v1.0 checklist with the 7-director roster, LIVE/DEMO toggle, agent control, intent decision workflow, idempotency, and the four read-only views.

## 1. Cold open

- [ ] Double-click `index.html` (or visit `http://localhost:8500/dashboard/`) → dashboard loads.
- [ ] Console (F12) is clean (no red errors).
- [ ] Top bar shows Mode chip, Acting director, Viewing director, Doctrine version.

## 2. LIVE / DEMO toggle

- [ ] Mode chip toggles between `LIVE` (green dot) and `DEMO` (blue dot).
- [ ] DEMO returns deterministic payload identical in shape to LIVE.
- [ ] LIVE never silently falls back to DEMO. If the chain is unreachable, the queue is **empty** and `meta.queue_source` exposes the diagnostic.
- [ ] Visiting `?mode=demo` forces DEMO regardless of toggle.

## 3. Director roster (7 directors)

- [ ] 5 mandatory cards: CEO, CFO, Legal, Market, CISO.
- [ ] CPO active by default for streaming/gaming/advertising/live profiles.
- [ ] CTO marked inactive (or active in non-test profiles).
- [ ] Acting / Viewing switchers work; non-CEO/CISO seats show a Read-Only banner when viewing someone else.
- [ ] Per-director scope: CEO/CISO see all 81 agents; CFO/Legal/Market/CPO/CTO scoped to their domain.

## 4. Agent mesh

- [ ] 81 tiles across 7 groups (Human Interface 3, Domain Governors 5, Orchestration 4, Corporate WG 39, AI-Centric 23, Twins 4, Meta-Governance 3).
- [ ] Tile click opens the Agent Card overlay with status, current step, scrollable FR tail, and Start / Restart / Diagnose / Safe-mode buttons.
- [ ] Pressing a control toasts a chain-acknowledgement, then the card auto-refreshes ~1.7 s later and the new state surfaces.
- [ ] Idempotent retry: clicking the same control twice in <2 s shows `Already recorded — idempotent reuse of <action_id>` toast.

## 5. Director Approval Queue

- [ ] Queue rows visible with composite badge, tier pill, owning director.
- [ ] In LIVE, queue is derived from a direct read of `chain.sqlite` (`intent_received` ⨝ decisions ⨝ latest `boss_scored` per intent_id).
- [ ] Row click opens the Intent Object Card overlay.
- [ ] Director Action workflow: Approve / Reject / Modify / Deny / Defer / Comment, with comment textarea, modifications free-text, dimension what-if grid + Recompute composite button.
- [ ] Action writes a Flight Recorder event with deterministic UUIDv5 `action_id`. Retrying the same action returns `idempotent: true`.
- [ ] Companion `director_proxy_acting` event is appended on every action (test profile: `acting_person = michael.lamb`).

## 6. Read-only views (added by `dashboard_views.py`)

- [ ] DNA Graph: `/api/dashboard/dna/sections` returns 13 sections; each section detail loads.
- [ ] FR Lifecycle: graphical, textual, and evidence modes all render for any `intent_id`.
- [ ] BOSS Dimension Detail: per-dimension page shows weight, scoring rubric, tier impact.
- [ ] Intent Object Detail: all 7 dimensions with composite + tier.

## 7. Flight Recorder tail

- [ ] Top-N latest events stream in.
- [ ] Sequence numbers monotonically increase.
- [ ] FR row click opens the matching Intent Object Card.

## 8. Digital Twin usage

- [ ] 4 twin cards render (Enterprise, Operational, Economic, Risk).
- [ ] Consultation bars proportional.
- [ ] Divergence cell changes colour above 1 % and above 2 %.

## 9. Resize, responsive, accessibility

- [ ] Panel resize handles work; density slider is smooth.
- [ ] At 1024 px → 2×2. At ≤1023 px → stacked column. At 2560 px → grid widens cleanly.
- [ ] Tab cycles through every interactive control in visual order.
- [ ] Enter on a queue row opens the overlay; Escape closes it.

## 10. Print / export

- [ ] Ctrl-P → preview shows main panels minus top bar, toolbar, footer, and action buttons.

## 11. Regression — automated

- [ ] `node qa/headless-smoke.js` prints **all PASS** (~56 jsdom assertions).
- [ ] `python3 qa/server-smoke.py` prints **all PASS** (~15 in-process Flask smoke tests).
- [ ] `python3 qa/views_smoke.py` prints **70 PASS / 0 FAIL**.

## 12. Parity (drift catch)

- [ ] `bash scripts/verify_parity.sh <installed_static_dashboard_dir> [<installed_app_dir>]` prints **0 FAIL**.

## 13. Live-mode hardening (May 2026)

These three behaviours must hold (regressions of any are a hard fail):

- [ ] Queue derivation uses a direct SQLite read of `chain.sqlite`, not the FR `/replay` cache.
- [ ] Agent control events match on both `agent_id == target` and `evidence.agent_id == target`, with the `start/restart/diagnose/safe_mode → status` override map applied.
- [ ] `_live_state()` ordering is strict: `interface_pending` → `chain_derived` → empty. **Never** falls back to demo. `meta.queue_source` and `meta.queue_count` are exposed.

## 14. Ports

- [ ] `http://localhost:8500/dashboard/` loads (primary surface).
- [ ] `http://localhost:8500/health` returns `{"ok": true, ...}`.
- [ ] `http://localhost:8300/health` returns `{"ok": true, "pending": <int>, ...}` (Human Interface Agents).
- [ ] The dashboard SPA also resolves through 8300 because the static folder is shared.
