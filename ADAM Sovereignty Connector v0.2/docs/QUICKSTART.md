# Quickstart

This walk-through assumes a fresh Windows 11 box, administrator account,
and a prepared `ADAM_Offline_Media\` folder (see [AIR_GAP_SETUP.md](AIR_GAP_SETUP.md)).

## 1. Place the Connector

Copy `adam_sovereignty_connector.exe` and `ADAM_Offline_Media\` into a
working directory, e.g. `C:\ADAM\`. The folder layout must look like:

```
C:\ADAM\
 ├── adam_sovereignty_connector.exe
 └── ADAM_Offline_Media\
      ├── MANIFEST.json
      ├── binaries\...
      └── images\...
```

## 2. First-run configuration

Open an **elevated** PowerShell or cmd in `C:\ADAM\`:

```cmd
adam_sovereignty_connector.exe init
```

Pick:
* **AI backend** — `anthropic` for the primary path, or `ollama` for pure
  sovereignty (no outbound calls). You can add others later by editing
  `%APPDATA%\AdamSovereigntyConnector\config.yaml`.
* **HTTP port** — default `8765` is fine.
* **ADAM Book corpus dir** — point at the folder containing the .docx/.md
  source material if you want the AI to read the book as MCP resources.

Drop the Anthropic key into the environment (one-shot):

```cmd
setx ANTHROPIC_API_KEY "sk-ant-..."
```

## 3. Pre-flight

```cmd
adam_sovereignty_connector.exe check
```

Confirms: Windows 11, admin, ≥ 60 GB free, media files present,
virtualization available.

## 4. Install host tools

```cmd
adam_sovereignty_connector.exe install --yes
```

Copies `kubectl.exe`, `helm.exe`, `k3d.exe` into
`%PROGRAMFILES%\AdamSovereigntyConnector\bin` and runs the Docker Desktop
installer. A reboot is usually required before Docker Desktop's engine is
fully operational — restart, then continue.

## 5. Bootstrap the cluster

```cmd
adam_sovereignty_connector.exe bootstrap --yes
```

* Side-loads every `.tar` under `ADAM_Offline_Media\images\` into the local
  k3d registry.
* Creates the k3d cluster named `adam-sovereignty` (1 server + 2 agents by
  default).

## 6. (Optional) Apply a DNA profile

The Connector auto-loads the **NetStreamX** reference profile from the ADAM
book corpus if you pointed `init` at it. To pre-generate the Helm values
overlay with a scaled-down test footprint:

```cmd
REM 100 synthetic assets + 100 synthetic subscribers + 9-agent laptop mesh
adam_sovereignty_connector.exe dna apply --scale minimal --assets 100 --subscribers 100

REM Doctrine default — 81-agent mesh, comfortable on 64 GB / 16-core
adam_sovereignty_connector.exe dna apply --scale showcase

REM Custom: full 81 agents but a 1 M / 1 M load shape
adam_sovereignty_connector.exe dna apply --agents 81 --assets 1000000 --subscribers 1000000
```

The overlay is written to
`%PROGRAMDATA%\AdamSovereigntyConnector\profile-values.yaml`. `deploy --yes`
auto-applies it if present.

## 7. Deploy ADAM

```cmd
adam_sovereignty_connector.exe deploy --yes
```

Applies namespaces, security policies, the five Directors, CORE Engine,
BOSS Score, Flight Recorder, and the Agent Mesh StatefulSet (81 pods by
default — the doctrine target).

Verify:

```cmd
adam_sovereignty_connector.exe status
```

You should see pods in `adam-core`, `adam-constitution`, `adam-agents`,
`adam-observability` reaching Ready.

## 8. Hand control to Claude

```cmd
adam_sovereignty_connector.exe serve --all
```

This enables:
* HTTP operator UI at `http://127.0.0.1:8765/`
* MCP over stdio (Claude Desktop connects here)
* MCP over TCP at `127.0.0.1:8766`

Add the MCP entry to `claude_desktop_config.json` (see the main README).
Now tell Claude:

> "Read the ADAM book from the connector and bring the cluster to BOSS Score 7/7."

Claude will call `list_book_documents`, `read_book_document`, `cluster_status`,
`describe_workload`, and any install/deploy tools it needs. Privileged actions
will prompt you for explicit approval through the HTTP `_approved: true` flow.
