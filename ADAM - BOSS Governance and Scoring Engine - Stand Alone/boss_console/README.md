<p align="center">
  <img src="../../ADAM%20-%20Graphics/ADAM%20Flight%20Recorder.png" alt="BOSS Evidence Console" width="100%">
</p>

<h1 align="center">BOSS Evidence Console</h1>

<p align="center">
  <em>The operator UI for the BOSS AI Governance &amp; Risk Engine.</em>
</p>

<p align="center">
  <strong>Scores · Exceptions · Receipts · Flight Recorder · Frameworks · Tiers — in one browser tab.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=white" alt="React 18">
  <img src="https://img.shields.io/badge/TypeScript-Strict-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript Strict">
  <img src="https://img.shields.io/badge/Vite-5-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite 5">
  <img src="https://img.shields.io/badge/Tailwind-CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white" alt="Tailwind">
  <img src="https://img.shields.io/badge/Node-≥_20-339933?style=for-the-badge&logo=node.js&logoColor=white" alt="Node 20+">
  <br>
  <img src="https://img.shields.io/badge/Build-Dual_Mode-6B46C1?style=for-the-badge" alt="Dual Mode">
  <img src="https://img.shields.io/badge/Auth-sessionStorage-B45309?style=for-the-badge" alt="sessionStorage">
  <img src="https://img.shields.io/badge/a11y-WCAG_Aware-047857?style=for-the-badge" alt="a11y">
  <img src="https://img.shields.io/badge/OpenAPI-Source_of_Truth-0D9488?style=for-the-badge" alt="OpenAPI">
</p>

---

## <img src="https://img.shields.io/badge/01-What_It_Is-1E3A8A?style=for-the-badge" alt="01"> The Operator UI for BOSS

The Evidence Console is a React-based operator surface for the [BOSS Engine](../README.md). It talks to `boss_api` over HTTPS and renders **every** artifact the engine produces — dimension scores, exception packets, decision receipts, the hash-chained Flight Recorder, the framework catalog, and the active tier configuration.

It is the **only** presentation layer BOSS ships with — because BOSS is a governance substrate, not an agent UI. If you want to see what your agents are about to do and why BOSS is gating it, this is the tab you open.

---

## <img src="https://img.shields.io/badge/02-Two_Builds-6B46C1?style=for-the-badge" alt="02"> Full Build + Air-Gap Fallback

The console ships as **two buildable surfaces** in one directory. Pick per situation.

| Build | Entry point | Tooling | When to use |
|:---|:---|:---|:---|
| **Full Vite** | `index.html` + `src/` | Vite 5 · TS strict · Tailwind compiled · ESLint · code-split | Regular development, production deploys, CI pipelines. All views, typed end-to-end against `src/types.ts`. |
| **Single-file fallback** | `standalone.html` | React / Tailwind / Recharts from CDN · Babel in-browser | Demos, air-gapped triage, "quick look" without `npm install`. Implements Dashboard · Score · Frameworks · Flight Recorder only. |

> The standalone file exists on purpose: the person staring at an OHSHAT alert at 2 a.m. on a hardened jump host should not need Node.js to read the Flight Recorder.

---

## <img src="https://img.shields.io/badge/03-Prerequisites-0D9488?style=for-the-badge" alt="03"> What You Need

| Requirement | Minimum | Notes |
|:---|:---|:---|
| Node.js | **20** | Vite 5 requires ≥ 20. |
| Package manager | **npm 10** | `pnpm` / `yarn` also work; commands below use npm. |
| BOSS API | running on `http://localhost:8080` | Start with `uvicorn boss_api.app:create_app --factory --reload` or `make run`. |

---

## <img src="https://img.shields.io/badge/04-Run_It-047857?style=for-the-badge" alt="04"> Full Vite Build

```bash
cd boss_console
npm install
npm run dev            # http://localhost:5173 — proxies /v1 to BOSS_API_URL (default :8080)
npm run build          # type-check + bundle to dist/
npm run preview        # serve dist/ locally
npm run lint           # ESLint (typescript-eslint strict)
npm run typecheck      # tsc --noEmit
```

`vite.config.ts` reads `BOSS_API_URL` from the environment at dev-server startup and proxies `/v1/*` calls to it, so the SPA only needs to know about `/v1/...` paths. When `dist/` is hosted behind the BOSS API itself (the Docker image does exactly that), same-origin calls work with no proxy.

### Environment

| Variable | Default | Purpose |
|:---|:---|:---|
| `BOSS_API_URL` | `http://localhost:8080` | Dev-server proxy target (upstream BOSS API). |
| `VITE_API_PREFIX` | `/v1` | API prefix baked into the client bundle. |

---

## <img src="https://img.shields.io/badge/05-Standalone_Mode-B45309?style=for-the-badge" alt="05"> Zero-Install Air-Gap Fallback

```bash
# Nothing to install. Just open the file.
open boss_console/standalone.html

# Or serve it from any static http server:
python3 -m http.server --directory boss_console 8000
# → http://localhost:8000/standalone.html
```

The standalone file honours the same `boss.api.base` / `boss.api.token` sessionStorage keys as the Vite build, so switching between the two preserves your config.

### Known limits of the standalone build

| Caveat | Detail |
|:---|:---|
| **In-browser JSX** | Compiles JSX via `@babel/standalone`. Don't ship to production. |
| **CDN Tailwind** | Uses `cdn.tailwindcss.com` (JIT play build). Not safe for airlocked deploys. |
| **Missing views** | Exception queue, receipt signing, and tier editor are **not** implemented. Use the Vite build for those. |

---

## <img src="https://img.shields.io/badge/06-Routes-B91C1C?style=for-the-badge" alt="06"> What's Wired Up (Vite Build)

| Route | Purpose |
|:---|:---|
| `/dashboard` | Engine overview — framework count · tier config snapshot · top-priority dimension. |
| `/score` | Paste an ADAM Intent Object v1.0, see dimension radar + tier + modifiers + rationale. |
| `/exceptions` | Open an Exception Packet; keeps an in-session queue. |
| `/receipts` | Sign a Decision Receipt (`APPROVE` · `APPROVE_WITH_CONSTRAINTS` · `REJECT` · `DEFER` · `ESCALATE`). |
| `/flight-recorder` | Tail the immutable Flight Recorder and verify hash-chain integrity. |
| `/frameworks` | Full framework catalog with provenance URLs and dimension attribution. |
| `/tiers` | Director-only tier configuration editor, with the "exactly one **Top**" constraint enforced. |

---

## <img src="https://img.shields.io/badge/07-Auth_+_Session-1E3A8A?style=for-the-badge" alt="07"> Bearer Tokens in `sessionStorage`

The console stores its bearer token in `sessionStorage` under the key `boss.api.token` — **intentionally**. `localStorage` would survive a browser restart; `sessionStorage` forces a re-authentication on each new tab, which matches how auditors expect evidence consoles to behave.

Paste a token through the header-bar pop-in. It is never sent anywhere except the configured API base.

> This is a small design decision with a load-bearing consequence: the evidence console is *not* a dashboard you leave open. It is an investigation tool you open when you need to see something and close when you're done.

---

## <img src="https://img.shields.io/badge/08-Type_Safety-0D9488?style=for-the-badge" alt="08"> OpenAPI Is the Source of Truth

`src/types.ts` is the client-side mirror of the Pydantic v2 models in `boss_core` and `boss_api`. The authoritative source is the OpenAPI schema served at `/v1/openapi.json`. CI regenerates these types on every API change — see the `generate-client` job in `.github/workflows/ci.yml`.

**Concrete guarantee:** if the API's `IntentObject` or `BOSSResult` shape changes, the console either regenerates or fails to type-check. There is no manual drift.

---

## <img src="https://img.shields.io/badge/09-Accessibility-047857?style=for-the-badge" alt="09"> Built for Auditors

| Choice | Why |
|:---|:---|
| Every input has an associated `<label>` | Keyboard + screen-reader users can tab the form. |
| Tier color is never the sole signal | Each tier pill also carries a textual label (`SOAP`, `OHSHAT`, …). |
| Default Tailwind focus rings | Visible in every interactive state. |
| Recharts Tooltips carry aria-friendly titles | Radar chart hover states are announced. |

---

## <img src="https://img.shields.io/badge/10-License-B45309?style=for-the-badge" alt="10"> License

Apache License 2.0 — see the root [`LICENSE`](../LICENSE) and [`NOTICE`](../NOTICE). The console follows the same license as the rest of the BOSS Engine.

---

<p align="center">
  <a href="../README.md"><img src="https://img.shields.io/badge/⬅_Back_to_BOSS_Engine-1E3A8A?style=for-the-badge" alt="Back to BOSS Engine"></a>
  <a href="../../README.md"><img src="https://img.shields.io/badge/⬅_Back_to_ADAM_SpecPack-047857?style=for-the-badge" alt="Back to ADAM SpecPack"></a>
</p>
