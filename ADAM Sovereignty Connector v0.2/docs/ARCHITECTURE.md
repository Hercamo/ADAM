# Architecture

The Connector is a thin, well-boundaried orchestrator with four responsibilities:

1. **Host preparation** — install Docker Desktop, kubectl, Helm, k3d from an
   offline media folder; nothing is fetched over the public internet.
2. **Cluster lifecycle** — create / status / destroy the local k3d cluster;
   side-load container images from the same offline media folder.
3. **ADAM skeleton deploy** — apply a layered set of kubectl manifests (or
   Helm chart) that instantiate CORE Engine, 5-Director Constitution (CEO,
   CFO, Legal Director, Market Director, CISO), BOSS Score v3.2 (canonical
   7 dimensions, weight-sum 24.0), Flight Recorder, and the 81+ Agent Mesh
   (reference count 81 across seven canonical classes).
4. **AI control plane** — expose all of the above as **named tools** over
   MCP and HTTP so Claude (or another LLM) can drive the install.

## Module map

```
adam_sovereignty_connector/
├── cli.py            argparse dispatcher; lazy-imports heavy modules
├── config.py         layered config (env, file, defaults); dataclasses
├── core/
│   ├── orchestrator.py     owns the audit log and command execution
│   ├── command_catalog.py  loads command_catalog.yaml; validates args
│   ├── audit.py            append-only JSONL with SHA-256 hash chain
│   ├── preflight.py        host-capability and media-folder checks (advisory)
│   ├── setup.py            interactive `init` UX
│   ├── corpus.py           reads the ADAM Book (md/docx/pdf/pptx)
│   └── dna.py              loads DNA profiles + emits Helm values overlays
├── ai/
│   ├── base.py             Backend ABC + Message dataclass
│   ├── anthropic_backend.py
│   ├── openai_backend.py
│   ├── ollama_backend.py
│   ├── openai_compat_backend.py
│   └── registry.py         factory: cfg.ai.kind → backend
├── mcp/server.py     stdio + TCP JSON-RPC; tools/list + tools/call + resources
├── http/server.py    stdlib http.server (no fastapi dep inside the .exe)
├── installers/       Docker/kubectl/Helm/k3d; each installer ships a single
│                     `install(args, ctx)` callable that the catalog binds to.
├── deploy/
│   ├── cluster.py    k3d create/destroy/status, kubectl listing/logs
│   └── adam_stack.py deploy_* callables: namespaces → security → directors → core → boss → flight → agents
└── web/static/       Loopback operator UI (plain HTML + fetch)
```

## Data-flow: an AI-driven deploy

```
 Claude ──(MCP tools/call name=deploy_all)──▶  mcp/server.py
                                                      │
                                                      ▼
                                       CommandCatalog.execute()
                                                      │
                                                      ▼
                           risk check ─── approval gate ─── Context(cfg, audit)
                                                      │
                                                      ▼
                             deploy.adam_stack.deploy_all(args, ctx)
                                                      │
                          ┌───────────────┬──────────┴──────────┬───────────────┐
                          ▼               ▼                     ▼               ▼
               deploy_namespaces   deploy_constitution   deploy_core_engine    ...
                          │                                                     
                          ▼                                                     
                 kubectl apply -f 00-namespaces.yaml                            
```

Every arrow is logged to the audit file. Handlers never touch the file system
directly outside the install/ and deploy/ modules; that's the narrow blast
radius the security model depends on.

## Why k3d on Docker Desktop (not Hyper-V VMs)

* **Pure OSS** — k3d + k3s are Rancher / CNCF licensed; no proprietary
  components in the runtime path (Docker Desktop is separate licence concern —
  swap for Rancher Desktop if needed).
* **Fast** — cold-start cluster in ~30 seconds; agent pods start in seconds.
* **Air-gap friendly** — `k3d image import` loads tars without any registry.
* **Doctrine-aligned** — matches ADAM's "lightweight sovereign runtime"
  principle better than full-fat Hyper-V VMs.

If your deployment target requires real VM isolation (e.g. government
"multi-realm" deployments), swap `k3d` out in the command catalog with
`kubeadm`/`HyperV`-based installers — the rest of the stack is unchanged.

## DNA profiles

The Connector doesn't invent company context — it consumes it. The DNA
Deployment Tool produces two artefacts per company:

* `adam-dna-parsed.json` — raw questionnaire answers (~100 Q)
* `config-bundle/adam-master-config.yaml` — the normalised master config
  with BOSS dimension weights, threshold bands, director list, graph
  types, and delegation rules.

`core/dna.py` discovers these (under `corpus_dir` **and**
`%APPDATA%/AdamSovereigntyConnector/dna-profiles/`), normalises them into
a `DNAProfile` dataclass, and emits a Helm values overlay at
`%PROGRAMDATA%/AdamSovereigntyConnector/profile-values.yaml`. The overlay
layers on top of the umbrella chart's defaults (81+ agent doctrine —
reference count 81 across 7 classes; 5 canonical Directors; BOSS v3.2
7-dimension scorer) so two deploys of the same company always look the same.

Three **test-scale presets** (`minimal` / `showcase` / `production-like`)
set synthetic asset/subscriber counts and agent-mesh replica counts. They
are strictly for test-harness realism — they never change ADAM doctrine.

## The 81+ Agent Mesh at workstation scale

The doctrine target is an 81+ agent mesh (reference count 81 across the seven
canonical classes: 5 Domain Governors, 4 Orchestration Agents, 3 Human
Interface Agents, 39 Corporate Work Groups, 23 AI-Centric Division, 4 Digital
Twin Agents, 3 Meta-Governance Agents). On a 32 GB workstation this is
viable; on a laptop it will OOM. The umbrella chart ships with 81 replicas by
default; the Connector's `dna apply --scale minimal` reshapes the test harness
to a 9-agent representative slice with 100 synthetic assets / 100 synthetic
subscribers — Michael's canonical smoke-test shape. Scale manually with:

```cmd
helm upgrade adam deploy\helm\adam-umbrella --set agentMesh.replicas=81
```

## Extending the catalog

Adding a capability is a two-step change:

1. Add a YAML entry in `deploy/catalog/command_catalog.yaml` with a name,
   summary, risk tier, and JSON-Schema arg schema.
2. Add a Python callable `install(args, ctx) -> dict` somewhere under
   `src/adam_sovereignty_connector/installers/` or `deploy/` and wire it in
   `CommandCatalog.bind_defaults()`.

The AI will see the new tool the next time it calls `tools/list`.
