# ADAM Sovereignty Connector

> A local, air-gap-friendly orchestrator + AI passthrough that **deploys** the
> **ADAM** (Autonomy Doctrine & Architecture Model) reference stack on a single
> Windows 11 host — driven by Claude (or any other LLM) over the Model Context
> Protocol.
>
> **Version 1.1** — aligned with ADAM book v1.4 (BOSS v3.2 canonical 7
> dimensions, 5-Director Constitution, 81+ Agent Mesh across seven classes).

The Connector is a single Windows executable you (or Claude) run on a fresh
Windows 11 box. It installs Docker Desktop, kubectl, Helm, and k3d, creates a
local Kubernetes cluster, side-loads every required container image from an
offline media folder, and **deploys** the ADAM skeleton — CORE Engine,
5-Director Constitution, BOSS Score v3.2 (7 canonical dimensions, weight-sum
24.0), Flight Recorder, and the 81+ Agent Mesh. No public cloud. No outbound
internet. Doctrine-aligned by default.

---

## Why this exists

The ADAM book ("ADAM — Autonomy Doctrine & Architecture Model") describes a
sovereign autonomy stack: CORE Engine, BOSS Score v3.2, Exception Economy,
Flight Recorder, Intent Objects, a 5-Director Constitution (CEO, CFO, Legal
Director, Market Director, CISO — optional CPO/CTO), and an 81+ Agent Mesh
across seven canonical classes. Until now, standing up a showcase meant weeks
of manual installation. The Connector collapses that into three phases —
**install**, **bootstrap**, **deploy** — and exposes every step as a vetted
tool the AI can call.

---

## Architecture at a glance

```
┌────────────────────────────────────────────────────────────────────┐
│                Claude / GPT-4 / Llama / Qwen / ...                 │
│                           (any LLM)                                │
└───────────────────────────────┬────────────────────────────────────┘
                                │ MCP  (stdio or TCP)
┌───────────────────────────────▼────────────────────────────────────┐
│                 ADAM Sovereignty Connector  (.exe)                 │
│                                                                    │
│  ┌─────────┐  ┌─────────────┐  ┌──────────┐  ┌─────────────────┐   │
│  │ CLI     │  │ HTTP API +  │  │ MCP      │  │ Audit log       │   │
│  │         │  │ Web UI      │  │ server   │  │ (append-only)   │   │
│  └────┬────┘  └──────┬──────┘  └─────┬────┘  └────────┬────────┘   │
│       │              │               │                │            │
│       └──────────────▼───────────────▼────────────────▼            │
│                     Vetted Command Catalog                         │
│       install_*  │  bootstrap_cluster  │  deploy_*  │  read_*      │
└────────────┬──────────────────────┬────────────────────────────────┘
             │                      │
             ▼                      ▼
   Windows host installers    k3d cluster on Docker Desktop
   (Docker, kubectl, Helm,      - adam-core        (CORE Engine, BOSS Score)
    k3d; all from offline       - adam-constitution (5 Directors)
    media folder)               - adam-agents      (81+ agent mesh, 7 classes)
                                - adam-observability (Flight Recorder)
                                - adam-system      (system services)
```

Claude *does not run shell commands*. It calls named tools (`install_k3d`,
`deploy_core_engine`, `cluster_status`) whose argument schemas and risk tiers
are declared in `deploy/catalog/command_catalog.yaml`. Every call passes
through an append-only audit log and a human-approval gate for privileged
actions.

---

## Requirements

### Target host (where ADAM runs)

Operating system and privileges:

* Windows 11 (22H2 or newer), fully patched. Windows 10 22H2 is tolerated but
  not recommended. Server SKUs (2022/2025) also work.
* Local Administrator account — required for installing Docker Desktop,
  kubectl, Helm, and k3d into `%PROGRAMFILES%\AdamSovereigntyConnector\bin`.
* Hardware virtualization available and enabled in firmware (VT-x / AMD-V,
  SLAT, Second-Level Address Translation). WSL-2 **or** Hyper-V is required
  for Docker Desktop's Linux engine.
* PowerShell 5.1+ (ships with Windows 11).

Hardware — **minimum** vs **recommended** (the 81+ agent doctrine mesh is the
default; the pre-flight will *warn* but never block if you are below these):

| Resource   | Minimum                                  | Recommended             | Comfortable showcase       |
|------------|------------------------------------------|-------------------------|----------------------------|
| CPU cores  | 8 logical                                | 16 logical              | 20 logical (test server)   |
| RAM        | 32 GB                                    | 64 GB                   | 64 GB (test server)        |
| Disk free  | 40 GB                                    | 100 GB                  | 250 GB SSD                 |
| Disk class | SSD                                      | NVMe                    | NVMe                       |
| Network    | Loopback only — no outbound internet     | same                    | same                       |

Notes on sizing:

* The **81+ agent mesh** (reference count 81 across seven classes) is the
  default (`deploy/helm/adam-umbrella/values.yaml`, `agentMesh.replicas: 81`).
  Each agent pod requests `25m` CPU and `48Mi` RAM, so the mesh at rest needs
  ~2 vCPU + ~4 GB. Headroom for the CORE Engine, five Directors, BOSS Score,
  Flight Recorder, k3s server, and Docker Desktop brings the comfortable
  working set to ~12–16 GB when idle and 24–32 GB under load.
* If you are on a laptop or under-spec host, you can still deploy — the
  connector will surface a WARNING and continue. Scale the mesh down with
  `helm upgrade adam deploy/helm/adam-umbrella --set agentMesh.replicas=9`
  for a 3 × 3 laptop showcase.
* Disk: the Docker Desktop installer is ~900 MB; the k3s bundle and five
  ADAM image tars together are ~3–5 GB; cluster state, image cache, and the
  Flight Recorder 5 Gi PVC round the working set to ~15–20 GB. 40 GB is
  survivable, 100 GB is comfortable.
* The target host is assumed to be **fully air-gapped** at run time. All
  binaries and container images arrive via the `ADAM_Offline_Media\` folder
  you prepare once on a connected workstation (see
  [docs/AIR_GAP_SETUP.md](docs/AIR_GAP_SETUP.md)).

### Reference test host (what the v1.1 showcase was validated on)

* Windows 11 Pro 23H2, fully patched
* 20 logical CPU cores (Intel i9 / equivalent)
* 64 GB RAM
* 500 GB NVMe SSD (≥ 250 GB free before install)
* Hyper-V enabled, WSL-2 active, no outbound internet during deploy

On a host at or above this spec the full 81+ agent doctrine mesh comes up
cleanly with `deploy --yes` and stays within ~40 % of total RAM and ~30 % of
CPU under nominal load.

### Build host (produces the `.exe`)

* Python 3.11+ on PATH
* `pip install -r requirements.txt` (PyYAML is required; `anthropic`,
  `openai`, `python-docx`, `pypdf`, `python-pptx` are optional extras)
* `pip install pyinstaller`
* Running `build.bat` on Windows produces `dist\adam_sovereignty_connector.exe`.

The build host can be the same machine as the target — the `.exe` is ~30 MB
and self-contained.

### Offline-media builder host (one-time, connected to internet)

* Docker Desktop (needs the engine running to `docker pull` / `docker save`)
* PowerShell 7+ on Windows, or Bash on Linux/macOS
* ~10 GB working disk while the bundle is being built
* See [docs/AIR_GAP_SETUP.md](docs/AIR_GAP_SETUP.md) for the
  `scripts/build_offline_media.ps1` / `.sh` procedure.

---

## Quick start

On a connected workstation, produce the offline media bundle:

```powershell
scripts\build_offline_media.ps1
```

Copy the resulting `ADAM_Offline_Media\` folder next to the Connector
executable on the air-gapped target host.

Build the `.exe` on any Windows machine (this step is one command):

```cmd
build.bat
```

→ produces `dist\adam_sovereignty_connector.exe`.

Run it on the target:

```cmd
adam_sovereignty_connector.exe init
adam_sovereignty_connector.exe check
adam_sovereignty_connector.exe install --yes
adam_sovereignty_connector.exe bootstrap --yes
adam_sovereignty_connector.exe deploy --yes
adam_sovereignty_connector.exe serve --all
```

The operator UI is at `http://127.0.0.1:8765/`. The MCP endpoint for Claude
Desktop is stdio (pipe the process) or TCP at `127.0.0.1:8766`.

See [docs/QUICKSTART.md](docs/QUICKSTART.md) for a walk-through and
[docs/AIR_GAP_SETUP.md](docs/AIR_GAP_SETUP.md) for the offline-bundle
procedure.

---

## Pointing Claude at the Connector

Add this to Claude Desktop's `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "adam-sovereignty-connector": {
      "command": "C:\\Path\\To\\adam_sovereignty_connector.exe",
      "args": ["serve", "--mcp-stdio"]
    }
  }
}
```

Claude will see every catalog command as a tool (`install_docker_desktop`,
`bootstrap_cluster`, `deploy_all`, `read_book_document`, …). Privileged tools
announce `requiresApproval=true` in their metadata so Claude can surface them
for operator confirmation.

---

## Supported AI backends

Configured under `ai:` in `config.yaml`. Multi-select at `init` time:

| Backend              | kind            | Notes                                        |
|----------------------|-----------------|----------------------------------------------|
| Anthropic Claude     | `anthropic`     | Primary; MCP-first; needs `ANTHROPIC_API_KEY`|
| OpenAI / Azure OAI   | `openai`        | Needs `OPENAI_API_KEY`; Azure via env        |
| Ollama (local)       | `ollama`        | Pure sovereign; default `http://127.0.0.1:11434` |
| OpenAI-compatible    | `openai_compat` | vLLM, LM Studio, together.ai, etc.           |

---

## Repository layout

```
.
├── build.bat                    # Windows build entry → produces the .exe
├── build/
│   ├── adam_sovereignty_connector.spec
│   └── version_info.txt
├── src/adam_sovereignty_connector/
│   ├── cli.py                   # argparse entry
│   ├── config.py                # layered config
│   ├── core/                    # orchestrator, catalog, audit, preflight
│   ├── ai/                      # 4 AI backend adapters + registry
│   ├── mcp/                     # Minimal MCP server (stdio + TCP)
│   ├── http/                    # Control-plane HTTP API + tiny web UI
│   ├── installers/              # Docker/kubectl/Helm/k3d installers
│   ├── deploy/                  # k3d lifecycle + kubectl apply helpers
│   └── web/static/              # Loopback operator UI
├── deploy/
│   ├── catalog/command_catalog.yaml   # Vetted command surface
│   ├── manifests/                     # Plain kubectl-applyable YAML
│   └── helm/adam-umbrella/            # Umbrella Helm chart
├── media/
│   └── MANIFEST.md                    # What ADAM_Offline_Media must contain
├── scripts/
│   ├── build_offline_media.ps1        # Windows builder
│   └── build_offline_media.sh         # Linux/macOS builder
├── docs/
│   ├── ARCHITECTURE.md
│   ├── QUICKSTART.md
│   ├── AIR_GAP_SETUP.md
│   └── SECURITY.md
├── tests/                             # pytest smoke tests
├── pyproject.toml
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Security model (summary)

* Loopback-only by default — HTTP + MCP TCP bind to `127.0.0.1`.
* Narrow catalog — the AI cannot execute arbitrary shell; every capability
  is declared in `command_catalog.yaml` with a risk tier.
* Human-approval gate — privileged actions (`install_docker_desktop`,
  `destroy_cluster`, `apply_raw_kubectl`) require explicit operator confirmation.
* Append-only audit log with a SHA-256 hash chain at
  `%PROGRAMDATA%\AdamSovereigntyConnector\audit.log`.
* API keys live in environment variables (or Windows Credential Manager via
  `keyring` if installed); the audit log redacts any arg whose name suggests a
  secret.

Details in [docs/SECURITY.md](docs/SECURITY.md).

---

## DNA profiles (company configuration)

Each ADAM deploy is parameterised by a **DNA profile** — the output of the
ADAM DNA Deployment Tool. The Connector auto-discovers profiles under
two roots:

* `cfg.corpus_dir` — typically the ADAM Book folder you pointed `init` at.
  The reference profile **NetStreamX** lives at
  `ADAM Book/ADAM - DNA Deployment Tool/example-output-netstreamx/`.
* `%APPDATA%\AdamSovereigntyConnector\dna-profiles\` — drop your own
  `adam-dna-parsed.json` and/or `config-bundle/adam-master-config.yaml` here.

Every DNA profile has two artefacts the Connector understands:

| File                                             | Role                                       |
|--------------------------------------------------|--------------------------------------------|
| `adam-dna-parsed.json`                           | Raw questionnaire answers (~100 Q)         |
| `config-bundle/adam-master-config.yaml`          | Normalised BOSS dims, directors, etc.      |

When `deploy_all` runs, it writes a **Helm values overlay** to
`%PROGRAMDATA%\AdamSovereigntyConnector\profile-values.yaml` — company
name, mission/vision, the five canonical Directors (CEO, CFO, Legal Director,
Market Director, CISO), BOSS v3.2 dimensions + thresholds, and any
test-scale overrides you supply.

### CLI

```cmd
adam_sovereignty_connector.exe dna list
adam_sovereignty_connector.exe dna show --name netstreamx
adam_sovereignty_connector.exe dna apply --scale minimal --assets 100 --subscribers 100
adam_sovereignty_connector.exe dna apply --scale showcase            REM doctrine defaults (81+ agents, reference 81)
adam_sovereignty_connector.exe dna apply --agents 81 --assets 1000000 --subscribers 1000000
```

### Built-in scale presets

The presets are knobs for **test realism** — they don't change ADAM's behaviour,
they change how much synthetic load the placeholder services advertise so a
test harness can confirm the stack responds correctly at that shape.

| Preset            | Assets     | Subscribers | Agents | When to use                           |
|-------------------|-----------:|------------:|-------:|---------------------------------------|
| `minimal`         |        100 |         100 |      9 | Laptop smoke tests / CI rehearsal     |
| `showcase`        |     10 000 |      10 000 |     81 | Doctrine default on 64 GB / 16-core   |
| `production-like` |  1 000 000 |   1 000 000 |     81 | Multi-node cluster rehearsal          |

### NetStreamX showcase — the default test path

NetStreamX is the fictional streaming-entertainment company used throughout
the ADAM book as the running worked example. Its full DNA ships in the book
corpus, so with nothing extra to configure you can:

```cmd
adam_sovereignty_connector.exe init                        REM point corpus_dir at the ADAM Book folder
adam_sovereignty_connector.exe check
adam_sovereignty_connector.exe install --yes
adam_sovereignty_connector.exe bootstrap --yes
adam_sovereignty_connector.exe dna apply --scale minimal --assets 100 --subscribers 100
adam_sovereignty_connector.exe deploy --yes
adam_sovereignty_connector.exe status
```

That gives you an air-gapped, doctrine-aligned ADAM instance configured as
a scaled-down NetStreamX — 100 synthetic assets, 100 synthetic subscribers,
9-pod agent mesh — which is exactly the smoke-test shape the book's QA
chapter describes.

---

## How this fits into the ADAM Book and SpecPack

The Connector is not a standalone tool — it is the **bootloader** for the
reference implementation described across the ADAM book and the SpecPack.
Each layer the Connector deploys has a source-of-truth chapter you can
point Claude at with `read_book_document`.

| Connector layer / catalog command           | Backed by                                              | ADAM Book section                                         |
|---------------------------------------------|--------------------------------------------------------|-----------------------------------------------------------|
| `deploy_namespaces`                         | `deploy/manifests/00-namespaces.yaml`                  | Reference Architecture — Blueprint Layers                 |
| `deploy_security_policies`                  | `deploy/manifests/10-security-policies.yaml`           | Legal & Governance — EU AI Act / DORA / NIS2 alignment    |
| `deploy_constitution` (5 Directors)         | `deploy/manifests/20-constitution-directors.yaml`      | 5-Director Constitution (ch. 4)                           |
| `deploy_core_engine`                        | `deploy/manifests/30-core-engine.yaml`                 | CORE Engine + Intent Objects (ch. 3)                      |
| `deploy_boss_score` (v3.2, 7 canonical dims) | `deploy/manifests/40-boss-score.yaml`                 | BOSS Score v3.2 formulas (ch. 5) + questionnaire          |
| `deploy_flight_recorder`                    | `deploy/manifests/50-flight-recorder.yaml`             | Flight Recorder + Exception Economy (ch. 6)               |
| `deploy_agent_mesh` (81+ agents)            | `deploy/manifests/60-agent-mesh.yaml`                  | 81+ Agent Mesh across 7 canonical classes (ch. 7)         |
| `load_dna_profile` / `apply_dna_profile`    | `core/dna.py`                                          | DNA Questionnaire + DNA Deployment Tool docs         |
| `list_book_documents` / `read_book_document`| `core/corpus.py`                                       | Every book chapter, AGT plugin docs, diagrams             |

**Reference inputs shipped with the book (and readable via MCP as resources):**

* 12 core manuscript documents (v0.09 as of April 2026).
* 2 AGT plugin specs.
* **DNA Deployment Tool** — the upstream generator of the profiles this
  Connector consumes.
* **DNA TOOL web app** — the conversational successor to the DNA
  questionnaire; its JSON output drops straight into
  `%APPDATA%\AdamSovereigntyConnector\dna-profiles\`.
* 9 architecture diagrams (`.drawio`) — the multi-cloud topology, blueprint
  layers, agent runtime, communication protocols.
* **NetStreamX example output** — the canonical worked example used here
  for the default showcase install.

**SpecPack cross-references (deployment targets):**

* `aws/`, `azure/`, `azure-local/`, `gcp/`, `kubernetes/{config,helm,kustomize}`
  — target-specific ADAM deployments generated by the DNA Deployment Tool.
  The Connector is the **Windows k3d** target in that family; the same
  `adam-master-config.yaml` feeds all of them so the doctrine stays
  identical across clouds.

### The four-phase deploy in book terms

1. **Install** prepares the host (Docker Desktop, kubectl, Helm, k3d) from
   the offline media folder — corresponds to the "Sovereign Runtime" layer
   of the Reference Architecture.
2. **Bootstrap** stands up the k3d cluster and side-loads every image —
   corresponds to the "Platform Substrate" layer.
3. **Deploy** applies the seven ADAM manifests in doctrinal order
   (namespaces → security → constitution → CORE → BOSS → Flight Recorder →
   agents). Each maps 1-to-1 to a blueprint layer above "Platform Substrate".
4. **Serve** hands control to Claude / another LLM over MCP. From here the
   AI can read the book (for context), inspect the running cluster, and
   re-apply DNA overlays for what-if experiments — all without ever
   touching a raw shell.

---

## License

Apache-2.0. See [LICENSE](LICENSE).
