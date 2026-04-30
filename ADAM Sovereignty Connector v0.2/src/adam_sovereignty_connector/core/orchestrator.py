"""High-level Orchestrator.

Coordinates pre-flight, installers, cluster bootstrap, and ADAM stack
deployment. Wires the command catalog to the audit log, approval gate, HTTP
API, and MCP server.
"""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from adam_sovereignty_connector.config import Config, program_data_dir
from adam_sovereignty_connector.core.audit import AuditLog
from adam_sovereignty_connector.core.command_catalog import Context, load_catalog

log = logging.getLogger("adam.orchestrator")

DEPLOY_PLAN = [
    ("check_host", {}, "Pre-flight: host capability, tools, media presence"),
    ("install_docker_desktop", {}, "Install Docker Desktop (offline installer from media folder)"),
    ("install_kubectl", {}, "Install kubectl"),
    ("install_helm", {}, "Install Helm"),
    ("install_k3d", {}, "Install k3d"),
    ("import_offline_images", {}, "Side-load container images into k3d registry"),
    ("bootstrap_cluster", {}, "Create the k3d cluster"),
    ("deploy_namespaces", {}, "Create ADAM namespaces"),
    ("deploy_security_policies", {}, "Apply NetworkPolicies and RBAC"),
    ("deploy_constitution", {}, "Deploy the 5-Director constitution services"),
    ("deploy_core_engine", {}, "Deploy CORE Engine"),
    ("deploy_boss_score", {}, "Deploy BOSS Score (7-dimension scorer)"),
    ("deploy_flight_recorder", {}, "Deploy Flight Recorder (audit/telemetry)"),
    ("deploy_agent_mesh", {}, "Deploy 81-agent mesh StatefulSet"),
    ("cluster_status", {}, "Summarise cluster + ADAM service health"),
]

class Orchestrator:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.catalog = load_catalog()
        audit_path = (
            Path(cfg.security.audit_log_path)
            if cfg.security.audit_log_path
            else program_data_dir() / "audit.log"
        )
        self.audit = AuditLog(audit_path)
        self._ctx = Context(config=cfg, audit=self.audit, orchestrator=self)

    # ---- plan / catalog --------------------------------------------------
    def print_plan(self) -> None:
        print("ADAM deployment plan")
        print("-" * 60)
        for idx, (cmd, args, note) in enumerate(DEPLOY_PLAN, start=1):
            spec = self.catalog.spec(cmd) if cmd in self.catalog else None
            risk = f"[{spec.risk}]" if spec else "[?]"
            approval = "  (requires human approval)" if spec and spec.requires_approval else ""
            print(f"  {idx:2}. {risk:<12} {cmd:<28} — {note}{approval}")
        print("\n  (Run sub-steps with `exec <command>`; run the full plan with `install` + `bootstrap` + `deploy`.)")

    # ---- public command surface ------------------------------------------
    def execute_command(
        self,
        name: str,
        args: Optional[Dict[str, Any]] = None,
        actor: str = "cli",
        assume_yes: bool = False,
    ) -> int:
        args = args or {}
        spec = self.catalog.spec(name) if name in self.catalog else None
        if spec is None:
            log.error("Unknown command: %s", name)
            return 2

        needs_approval = spec.requires_approval or name in self.cfg.security.require_human_approval
        if needs_approval and not assume_yes and actor == "cli":
            if not _confirm(f"{name} is a privileged action. Continue? [y/N]: "):
                self.audit.record(actor, name, args, result="denied", details={"reason": "user declined"})
                return 1

        rec = self.audit.record(actor, name, args, result="pending")
        try:
            result = self.catalog.execute(name, args, self._ctx)
            self.audit.record("system", name, args, result="ok", details=_truncate(result))
            if result:
                print(json.dumps(result, indent=2, default=str))
            return 0
        except Exception as e:
            log.exception("Command %s failed", name)
            self.audit.record("system", name, args, result="error", details={"error": str(e)})
            return 1

    # ---- full-plan conveniences ------------------------------------------
    def install_prereqs(self, only: Optional[List[str]] = None, assume_yes: bool = False) -> int:
        steps = [
            "install_docker_desktop",
            "install_kubectl",
            "install_helm",
            "install_k3d",
        ]
        if only:
            steps = [s for s in steps if s in only]
        return self._run_sequence(steps, assume_yes)

    def bootstrap_cluster(self, assume_yes: bool = False) -> int:
        return self._run_sequence(
            ["check_host", "import_offline_images", "bootstrap_cluster"],
            assume_yes,
        )

    def deploy_adam(self, layers: Optional[List[str]] = None, assume_yes: bool = False) -> int:
        all_layers = [
            "deploy_namespaces",
            "deploy_security_policies",
            "deploy_constitution",
            "deploy_core_engine",
            "deploy_boss_score",
            "deploy_flight_recorder",
            "deploy_agent_mesh",
        ]
        steps = [l for l in all_layers if (not layers or l in layers)]
        return self._run_sequence(steps, assume_yes)

    def status(self) -> int:
        return self.execute_command("cluster_status", {}, actor="cli", assume_yes=True)

    def destroy(self) -> int:
        return self.execute_command("destroy_cluster", {}, actor="cli")

    # ---- servers ---------------------------------------------------------
    def serve(
        self,
        enable_http: bool = True,
        enable_mcp_stdio: bool = False,
        enable_mcp_tcp: bool = False,
    ) -> int:
        from adam_sovereignty_connector.http.server import start_http_server
        from adam_sovereignty_connector.mcp.server import serve_stdio, serve_tcp

        threads = []
        if enable_http:
            t = threading.Thread(
                target=start_http_server, args=(self,), name="http", daemon=True
            )
            t.start()
            threads.append(t)
            print(
                f"HTTP API listening on http://{self.cfg.server.http_host}:{self.cfg.server.http_port}"
            )

        if enable_mcp_tcp:
            t = threading.Thread(
                target=serve_tcp, args=(self,), name="mcp-tcp", daemon=True
            )
            t.start()
            threads.append(t)
            print(
                f"MCP (TCP) listening on {self.cfg.server.mcp_tcp_host}:{self.cfg.server.mcp_tcp_port}"
            )

        if enable_mcp_stdio:
            # stdio server is blocking; run in main thread
            print("MCP (stdio) attached to STDIN/STDOUT.")
            serve_stdio(self)
            return 0

        if not threads:
            log.error("No server surface enabled. Pass --http, --mcp-stdio, --mcp-tcp, or --all.")
            return 2

        try:
            while any(t.is_alive() for t in threads):
                for t in threads:
                    t.join(timeout=1.0)
        except KeyboardInterrupt:
            print("\nShutting down.")
        return 0

    # ---- helpers ---------------------------------------------------------
    def _run_sequence(self, steps: List[str], assume_yes: bool) -> int:
        for step in steps:
            rc = self.execute_command(step, {}, actor="cli", assume_yes=assume_yes)
            if rc != 0:
                log.error("Step %s failed with exit code %s. Aborting sequence.", step, rc)
                return rc
        return 0

def _confirm(prompt: str) -> bool:
    try:
        resp = input(prompt).strip().lower()
    except EOFError:
        return False
    return resp in {"y", "yes"}

def _truncate(obj: Any, limit: int = 1500) -> Any:
    try:
        s = json.dumps(obj, default=str)
    except Exception:
        return {"_repr": str(obj)[:limit]}
    if len(s) <= limit:
        return obj
    return {"_truncated": True, "_preview": s[:limit]}
