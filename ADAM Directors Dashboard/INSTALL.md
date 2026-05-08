# ADAM Directors Dashboard — Install Guide (v0.3)

This guide walks through installing the Directors Dashboard into any ADAM deployment. The result is a byte-identical clone of the dashboard that runs in NetStreamX production at `http://localhost:8500/dashboard/`.

> **Source of truth.** Everything in this directory is mirrored from
> `D:\ADAM\deployment\NetStreamX\netstreamx_app\` (SPA + blueprints) and from
> `D:\ADAM\deployment\NetStreamX\qa\views_smoke.py` (read-only views QA).
> Do not edit files here without round-tripping the change back to that runtime.

---

## 0. Prerequisites

- Python 3.10+ (production runs `python:3.12-slim`).
- Flask + `pynacl` + `requests` available to the Flask app process (these are already installed by the netstreamx-app container's `pip install` step).
- A running ADAM stack with at least:
  - **Flight Recorder** writing to a SQLite chain at a path the Flask process can read.
  - **Exception Router** at `EXC_URL`.
  - **AGT-Full** at `AGT_URL`.
  - The 81-agent registry available to the dashboard backend.
- A docker-managed named volume for the FR hot chain (bind-mounts on Docker Desktop / Windows are unsafe for SQLite WAL+fsync — see `D:\ADAM\upgrade_log\UPGRADE_LOG.md`).

---

## 1. File layout — what goes where

The dashboard installs in three layers. Below, `<APP>` is the Flask app's package directory (in NetStreamX it is `D:\ADAM\deployment\NetStreamX\netstreamx_app\`).

| From this spec dir                          | Install to                                            | Notes |
|---------------------------------------------|-------------------------------------------------------|-------|
| `index.html`                                | `<APP>/static/dashboard/index.html`                   | SPA entry point |
| `assets/app.js`                             | `<APP>/static/dashboard/assets/app.js`                | SPA logic |
| `assets/styles.css`                         | `<APP>/static/dashboard/assets/styles.css`            | Base styles |
| `assets/banner.svg`                         | `<APP>/static/dashboard/assets/banner.svg`            | Header banner |
| `assets/demo/demo_overlays.css`             | `<APP>/static/dashboard/assets/demo/demo_overlays.css`| DEMO mode overlay |
| `assets/demo/demo_overlays.js`              | `<APP>/static/dashboard/assets/demo/demo_overlays.js` | DEMO mode wiring |
| `assets/views/directors_views.css`          | `<APP>/static/dashboard/assets/views/directors_views.css` | Read-only views |
| `assets/views/directors_views.js`           | `<APP>/static/dashboard/assets/views/directors_views.js`  | Read-only views |
| `data/demo-data.js`                         | `<APP>/static/dashboard/data/demo-data.js`            | Deterministic demo payload |
| `server/dashboard_api.py`                   | `<APP>/dashboard_api.py`                              | Flask blueprint (write-side) |
| `server/dashboard_views.py`                 | `<APP>/dashboard_views.py`                            | Flask blueprint (read-only) |
| `server/demo_addons.py`                     | `<APP>/demo_addons.py`                                | DEMO-mode auxiliary endpoints |

After install, the production layout looks like this:

```
<APP>/
├── netstreamx_app.py        ← your Flask entry point (unmodified except for the 4 lines below)
├── dashboard_api.py         ← from spec server/
├── dashboard_views.py       ← from spec server/
├── demo_addons.py           ← from spec server/
└── static/
    └── dashboard/
        ├── index.html
        ├── assets/
        │   ├── app.js
        │   ├── styles.css
        │   ├── banner.svg
        │   ├── demo/{demo_overlays.css,demo_overlays.js}
        │   └── views/{directors_views.css,directors_views.js}
        └── data/demo-data.js
```

A one-shot copy command from this spec dir into a target NetStreamX-style layout:

```bash
SPEC="D:/ADAM/ADAM Book New/ADAM Directors Dashboard"
APP="D:/ADAM/deployment/NetStreamX/netstreamx_app"

# Front-end
mkdir -p "$APP/static/dashboard/assets/demo"
mkdir -p "$APP/static/dashboard/assets/views"
mkdir -p "$APP/static/dashboard/data"
cp "$SPEC/index.html"                          "$APP/static/dashboard/"
cp "$SPEC/assets/app.js"                       "$APP/static/dashboard/assets/"
cp "$SPEC/assets/styles.css"                   "$APP/static/dashboard/assets/"
cp "$SPEC/assets/banner.svg"                   "$APP/static/dashboard/assets/"
cp "$SPEC/assets/demo/demo_overlays.css"       "$APP/static/dashboard/assets/demo/"
cp "$SPEC/assets/demo/demo_overlays.js"        "$APP/static/dashboard/assets/demo/"
cp "$SPEC/assets/views/directors_views.css"    "$APP/static/dashboard/assets/views/"
cp "$SPEC/assets/views/directors_views.js"     "$APP/static/dashboard/assets/views/"
cp "$SPEC/data/demo-data.js"                   "$APP/static/dashboard/data/"

# Server
cp "$SPEC/server/dashboard_api.py"             "$APP/"
cp "$SPEC/server/dashboard_views.py"           "$APP/"
cp "$SPEC/server/demo_addons.py"               "$APP/"
```

---

## 2. Register the blueprints in your Flask app

In `<APP>/netstreamx_app.py` (or whatever your Flask entry point is named), find `app = Flask(...)` and add four lines immediately after:

```python
app = Flask(__name__, static_folder=None)

# Mount the upgraded Directors Dashboard API blueprint (v0.3). This adds
# /api/dashboard/* endpoints and is the single backend the upgraded SPA uses
# for bootstrap, live state, agent cards, intent cards, and director actions.
try:
    from dashboard_api import register as _register_dashboard_api  # type: ignore
    _register_dashboard_api(app)
    print("[netstreamx-app] Directors Dashboard API v0.3 registered at /api/dashboard/*", flush=True)
except Exception as _e:
    print(f"[netstreamx-app] WARNING: dashboard_api blueprint not loaded: {_e}", flush=True)

# Mount the Director Views blueprint (production). Adds:
#   /api/dashboard/dna/*, /api/dashboard/boss/dimension/<dim>,
#   /api/dashboard/lifecycle/<intent_id>(/event/<seq>),
#   /api/dashboard/views/health
# Strictly read-only against the live Flight Recorder chain.
try:
    from dashboard_views import register as _register_dashboard_views  # type: ignore
    _register_dashboard_views(app)
    print("[netstreamx-app] Director Views registered at /api/dashboard/{dna,boss,lifecycle}/*", flush=True)
except Exception as _e:
    print(f"[netstreamx-app] WARNING: dashboard_views blueprint not loaded: {_e}", flush=True)
```

The blueprints are guarded so a missing optional dependency never blocks the rest of the app — they print a WARNING and the rest of the app continues to boot.

The SPA itself is served by your existing static-file route. In NetStreamX `netstreamx_app.py` does this with a small `/dashboard/<path:p>` route that streams from `<APP>/static/dashboard/`. If your app already mounts `static/` at `/`, you can reach the dashboard at `/dashboard/index.html`.

---

## 3. Environment variables

| Variable           | Purpose                                                                              | Default                                  |
|--------------------|--------------------------------------------------------------------------------------|------------------------------------------|
| `FR_CHAIN_PATH`    | Direct read-only path to the Flight Recorder hot chain SQLite. **Required for live mode** to query `intent_received` + `boss_scored` directly. | `/var/lib/adam/chain/chain.sqlite` |
| `FR_URL`           | HTTP base for the Flight Recorder service (used for `/replay` / `/append`).          | `http://flight-recorder:8200`            |
| `EXC_URL`          | Exception Router base URL.                                                           | `http://exception-router:8220`           |
| `AGT_URL`          | AGT-Full base URL.                                                                   | `http://agt-full:8400`                   |
| `INTERFACE_URL`    | Human Interface Agents (8300) base URL — used for the mesh-overview proxy.           | `http://interface-agents:8300`           |
| `BOSS_URL`         | BOSS scorer base URL.                                                                | `http://boss-scorer:8210`                |
| `DOCTRINE_VERSION` | Doctrine seed version stamped on every emitted FR event.                             | `1.1.0-test`                             |
| `NSX_DB`           | Path to the customer-app SQLite (NetStreamX-specific; ignore in non-NSX deploys).    | `/data/adam/netstreamx_app.sqlite`       |
| `NSX_STATIC`       | Static-folder root if your route serves from a non-default path.                     | `/app/static`                            |
| `PORT`             | TCP port the Flask app binds to.                                                     | `8500`                                   |

The dashboard's `_FR_LIVE` candidate-path search prefers `FR_CHAIN_PATH` → `/var/lib/adam/chain` → `/data/adam/flight_recorder/chain.sqlite` → source-tree default. The first existing non-empty file wins. **In live mode the dashboard never silently falls back to demo data**; if no chain is found, the queue returns empty with `meta.queue_source` set to the diagnostic value `none`.

---

## 4. Storage rules — chain hot path vs. snapshot

> **Critical.** Docker Desktop bind-mounts on Windows silently dropped fsync writes during SQLite WAL checkpoints in May 2026, corrupting the chain four times. Do not put the **hot** chain on a bind-mount.

Required pattern (used in production):

- **Hot chain** lives on a docker-managed named volume (`fr_chain` in NetStreamX) at `/var/lib/adam/chain/chain.sqlite` inside the FR container.
- The hot volume is mounted **read-only** into the netstreamx-app container so the dashboard reads fresh chain data without contention.
- A periodic snapshot back to the bind-mount path runs every 300 s (this is what `D:\ADAM\flight_recorder\chain.sqlite` becomes).
- The dashboard backend reads from the hot path via `FR_CHAIN_PATH` and falls through to the snapshot only if the hot path is unavailable.

A docker-compose excerpt (from `D:\ADAM\deployment\NetStreamX\iac\compose\docker-compose.yml`):

```yaml
services:
  netstreamx-app:
    image: python:3.12-slim
    container_name: adam-netstreamx-app
    working_dir: /app
    command:
      - "bash"
      - "-lc"
      - "pip install --no-cache-dir flask requests pynacl && (python seed_data.py 2>&1 | tail -5 || true) && python -u netstreamx_app.py"
    volumes:
      - "pip_cache:/root/.cache/pip"
      - ../../netstreamx_app:/app:ro
      - ../../digital_twins:/opt/adam/digital_twins:ro
      - ../../flight_recorder:/opt/adam/flight_recorder:ro
      - ../../vault:/opt/adam/vault:ro
      - "D:/ADAM:/data/adam"
      - "fr_chain:/var/lib/adam/chain:ro"   # ← hot chain, read-only
    environment:
      FR_URL:           "http://flight-recorder:8200"
      EXC_URL:          "http://exception-router:8220"
      AGT_URL:          "http://agt-full:8400"
      NSX_DB:           "/data/adam/netstreamx_app.sqlite"
      NSX_STATIC:       "/app/static"
      FR_CHAIN_PATH:    "/var/lib/adam/chain/chain.sqlite"   # ← hot path
      DOCTRINE_VERSION: "1.1.0-test"
      PYTHONPATH:       "/app:/opt/adam/digital_twins:/opt/adam/flight_recorder:/opt/adam/vault"
      PORT:             "8500"
    ports:
      - "8500:8500"
    networks:
      - adam

  interface-agents:
    image: python:3.12-slim
    container_name: adam-netstreamx-interface-agents
    working_dir: /app
    command:
      - "bash"
      - "-lc"
      - "pip install --no-cache-dir flask requests && python server.py"
    volumes:
      - "pip_cache:/root/.cache/pip"
      - ./interface_server.py:/app/server.py:ro
      - ../../netstreamx_app/static:/app/static:ro
      - ../../core/doctrine-seed.json:/etc/adam/doctrine-seed.json:ro
    environment:
      FR_URL:        "http://flight-recorder:8200"
      BOSS_URL:      "http://boss-scorer:8210"
      EXC_URL:       "http://exception-router:8220"
      DOCTRINE_PATH: "/etc/adam/doctrine-seed.json"
      PORT:          "8300"
    ports:
      - "8300:8300"
    networks:
      - adam

volumes:
  fr_chain:
    driver: local
  pip_cache:
    driver: local
```

---

## 5. Ports

| Port  | Container                            | What it serves                                                                |
|-------|--------------------------------------|-------------------------------------------------------------------------------|
| 8500  | `adam-netstreamx-app`                | Customer site **and** Directors Dashboard at `/dashboard/`. This is the primary surface. |
| 8300  | `adam-netstreamx-interface-agents`   | Human Interface Agents (`/intent`, `/approve/<id>`, `/reject/<id>`, `/explain/<id>`, `/pending`). Also serves the static dashboard SPA as an additional surface because it shares the same `static/` mount. |

> **Naming.** Do not rename `dashboard_api.py`, `dashboard_views.py`, the `/api/dashboard/*` URL prefix, the `/dashboard/` static prefix, or the SPA's `index.html`. The SPA hard-codes these paths and the addon-bundle install scripts grep for them.

---

## 6. Smoke tests

After install, from the spec directory (these are the same harnesses used in the runtime):

```bash
node    qa/headless-smoke.js          # SPA jsdom smoke (~56 assertions)
python3 qa/server-smoke.py            # write-side blueprint smoke (~15 tests)
python3 qa/views_smoke.py             # read-only views smoke (70 PASS / 0 FAIL)
```

`qa/views_smoke.py` is the production-grade one used in the netstreamx-app container; it boots a Flask test client in-process, posts intents through the chain, and asserts the four read-only views return the expected payloads.

To verify the installed copy hasn't drifted from this spec:

```bash
bash scripts/verify_parity.sh /path/to/installed/static/dashboard /path/to/installed/app/folder
```

The script md5-compares every file in the SPA + blueprints against the spec and prints OK / FAIL per file.

---

## 7. Live-mode hardening (May 2026)

These three fixes are baked into v0.3 (see `D:\ADAM\upgrade_log\UPGRADE_LOG.md` entries 5, 6, 7):

1. **Direct chain read for queue derivation.** `dashboard_api.py` opens `chain.sqlite` read-only and joins `intent_received` + decisions + latest `boss_scored` per `intent_id`. The previous implementation relied on the FR `/replay` cache (last 500 events), which dropped `intent_received` events under self-audit heartbeat traffic.
2. **Indirect agent_id matching.** Agent control events are matched on `agent_id == target` **or** `evidence.agent_id == target`, with a `start/restart/diagnose/safe_mode → status` override map applied. The previous implementation missed control events emitted by `hi-gateway` against an indirect target.
3. **Strict live ordering.** `_live_state()` returns `interface_pending` → `chain_derived` → empty (in that order); it **never** falls back to demo. `meta.queue_source` and `meta.queue_count` are exposed for diagnostics.

A symptom of regressing any of these is "approval queue identical between LIVE and DEMO" or "control button click toasts success but agent state never updates."

---

## 8. Optional: bounce script

In NetStreamX, the canonical operator command after editing any blueprint or SPA file is:

```powershell
cd D:\ADAM\deployment\NetStreamX\scripts\windows
.\bounce_app.ps1
```

It recreates the netstreamx-app container, prints the last 50 log lines, and probes `/health` for ~30 s. Equivalent on Linux: `scripts/linux/bounce_app.sh`.

---

## 9. Memory / context for future sessions

The pointer in `MEMORY.md` (auto-memory) is `[ADAM Directors Dashboard v0.2](adam_directors_dashboard_v02.md)`. After install, all three copies (production runtime / spec / addon bundle) should remain md5-identical at the SPA layer; if they don't, run `scripts/verify_parity.sh` and update the spec from the runtime — never the other way around.
