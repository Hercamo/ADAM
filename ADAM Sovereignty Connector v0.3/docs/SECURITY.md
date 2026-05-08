# Security model

## Threat model

The Connector is designed for a **trusted local operator** driving a possibly
**untrusted LLM** against a local Windows host. The operator runs the `.exe`.
The LLM issues tool calls over MCP. The Connector enforces the boundary.

Core assumption: the operator is legitimate. A malicious operator can already
do anything on their own box; we don't defend against that. The interesting
boundary is the model ↔ connector boundary.

## Boundaries

### 1. No arbitrary shell

The AI cannot invoke `subprocess.run(...)` or `kubectl apply -f` with a
free-form blob. Every action is a named tool declared in
`deploy/catalog/command_catalog.yaml` with a JSON-Schema argument shape.
Adding a new tool is a catalog edit — a deliberate, reviewable change.

### 2. Risk tiers + approval gate

Each tool declares a risk tier:

| Tier        | Effect                                | Approval                     |
|-------------|---------------------------------------|------------------------------|
| read        | Inspect only                          | None                         |
| low         | Cluster writes (kubectl apply, etc.)  | None                         |
| high        | Host-level install                    | `--yes` on CLI               |
| privileged  | Destructive or needs elevation        | HTTP `_approved=true` or CLI confirmation |

`require_human_approval` in `config.yaml` can extend the privileged list.

### 3. Append-only audit log

Every call (including denied ones) is written as a JSON Lines entry to
`%PROGRAMDATA%\AdamSovereigntyConnector\audit.log`. Each record has a
monotonic sequence number, UTC timestamp, actor, command, arguments
(redacted), result, and a SHA-256 hash of the record plus the previous
record's hash. Replay the chain to detect tampering or gaps.

### 4. Secret hygiene

* API keys live in environment variables (the config stores only the
  env-var *name*, never the value).
* Arguments whose keys contain `key`, `token`, `secret`, `password`, or
  `pwd` are `[REDACTED]` in the audit log.
* The HTTP + MCP TCP servers bind to `127.0.0.1` by default.

### 5. Loopback-only defaults

`server.http_host` and `server.mcp_tcp_host` default to `127.0.0.1`. Exposing
them on a non-loopback interface is a deliberate, operator-made change; you
should pair it with a reverse proxy that does mTLS or SSO.

## What we don't protect against (yet)

* **Malicious manifests** supplied via a future `apply_raw_kubectl` tool.
  This is why it's gated behind `privileged + requires_approval=true` and
  disabled in the catalog.
* **Untrusted offline-media bundles.** The `check` command hashes what it
  finds but does not verify signatures. Adding `cosign verify` is a small
  addition to `core/preflight.py` and on the roadmap.
* **Compromised operator workstations.** Out of scope — see threat model.

## Reporting

Found a security issue? Please file privately; do not open a public issue.
