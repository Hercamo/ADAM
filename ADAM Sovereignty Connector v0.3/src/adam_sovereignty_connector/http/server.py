"""Local HTTP control-plane for ADAM Sovereignty Connector.

Deliberately uses stdlib ``http.server`` so the frozen .exe stays tiny and has
no optional dependency on FastAPI / uvicorn. This endpoint is bound to
loopback by default and is for operator convenience + tiny web UI.

Endpoints:
    GET  /                      -> web UI (static HTML)
    GET  /api/health            -> {"ok": true}
    GET  /api/catalog           -> command catalog
    GET  /api/plan              -> deployment plan
    GET  /api/status            -> cluster + ADAM service health
    GET  /api/audit?limit=50    -> tail of audit log
    POST /api/exec              -> {"command": "...", "arguments": {...}}
    POST /api/ai/chat           -> {"messages": [...]}  (uses configured backend)
"""
from __future__ import annotations

import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse

from adam_sovereignty_connector.config import resource_root
from adam_sovereignty_connector.core.orchestrator import DEPLOY_PLAN

log = logging.getLogger("adam.http")

def start_http_server(orchestrator) -> None:
    cfg = orchestrator.cfg.server
    server = ThreadingHTTPServer(
        (cfg.http_host, cfg.http_port), _make_handler(orchestrator)
    )
    log.info("HTTP server listening on http://%s:%s", cfg.http_host, cfg.http_port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

def _make_handler(orch):
    class Handler(BaseHTTPRequestHandler):
        server_version = "AdamSovereigntyConnector/1.1"

        def log_message(self, fmt, *args):
            log.info("%s - %s", self.address_string(), fmt % args)

        # ---- routing -----------------------------------------------------
        def do_GET(self):  # noqa: N802
            url = urlparse(self.path)
            path = url.path
            if path == "/" or path == "/index.html":
                return self._serve_static("index.html", default_mime="text/html")
            if path.startswith("/static/"):
                return self._serve_static(path[len("/static/"):])
            if path == "/api/health":
                return self._json(200, {"ok": True, "name": "adam-sovereignty-connector"})
            if path == "/api/catalog":
                return self._json(200, {"commands": [s.describe() for s in orch.catalog.specs()]})
            if path == "/api/plan":
                plan = [
                    {
                        "step": i + 1,
                        "command": cmd,
                        "arguments": args,
                        "note": note,
                        "risk": orch.catalog.spec(cmd).risk if cmd in orch.catalog else "unknown",
                    }
                    for i, (cmd, args, note) in enumerate(DEPLOY_PLAN)
                ]
                return self._json(200, {"plan": plan})
            if path == "/api/status":
                try:
                    status = orch.catalog.execute("cluster_status", {}, orch._ctx)
                    return self._json(200, status)
                except Exception as e:
                    return self._json(500, {"error": str(e)})
            if path == "/api/audit":
                qs = parse_qs(url.query)
                limit = int((qs.get("limit") or ["50"])[0])
                return self._json(200, {"entries": _tail_audit(orch.audit.path, limit)})
            return self._json(404, {"error": "Not found", "path": path})

        def do_POST(self):  # noqa: N802
            url = urlparse(self.path)
            path = url.path
            body = self._read_json()
            if path == "/api/exec":
                return self._exec(body)
            if path == "/api/ai/chat":
                return self._ai_chat(body)
            return self._json(404, {"error": "Not found", "path": path})

        # ---- actions -----------------------------------------------------
        def _exec(self, body: Dict[str, Any]):
            name = body.get("command")
            args = body.get("arguments") or {}
            actor = body.get("_actor", "http")
            if not name:
                return self._json(400, {"error": "command required"})
            try:
                spec = orch.catalog.spec(name) if name in orch.catalog else None
                if spec is None:
                    return self._json(404, {"error": f"unknown command {name}"})
                if spec.requires_approval and not body.get("_approved"):
                    return self._json(
                        403,
                        {"error": "human approval required", "hint": "re-submit with _approved=true from an operator"},
                    )
                orch.audit.record(actor, name, args, result="pending")
                result = orch.catalog.execute(name, args, orch._ctx)
                orch.audit.record("system", name, args, result="ok",
                                  details={"http_client": self.client_address[0]})
                return self._json(200, {"ok": True, "result": result})
            except Exception as e:
                log.exception("exec %s failed", name)
                orch.audit.record("system", name, args, result="error", details={"error": str(e)})
                return self._json(500, {"ok": False, "error": str(e)})

        def _ai_chat(self, body: Dict[str, Any]):
            from adam_sovereignty_connector.ai import get_backend
            from adam_sovereignty_connector.ai.base import Message
            try:
                backend = get_backend(orch.cfg.ai)
                msgs = [Message(role=m["role"], content=m["content"]) for m in body.get("messages", [])]
                reply = backend.chat(
                    msgs,
                    max_tokens=int(body.get("max_tokens", orch.cfg.ai.max_tokens)),
                    temperature=float(body.get("temperature", orch.cfg.ai.temperature)),
                )
                return self._json(200, {"backend": orch.cfg.ai.kind, "model": orch.cfg.ai.model, "reply": reply})
            except Exception as e:
                log.exception("ai/chat failed")
                return self._json(500, {"error": str(e)})

        # ---- low-level helpers ------------------------------------------
        def _read_json(self) -> Dict[str, Any]:
            length = int(self.headers.get("Content-Length") or 0)
            if not length:
                return {}
            raw = self.rfile.read(length)
            try:
                return json.loads(raw.decode("utf-8") or "{}")
            except Exception:
                return {}

        def _json(self, status: int, payload):
            data = json.dumps(payload, default=str).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)

        def _serve_static(self, rel: str, default_mime: str = "application/octet-stream"):
            root = resource_root() / "src" / "adam_sovereignty_connector" / "web" / "static"
            target = (root / rel).resolve()
            try:
                target.relative_to(root.resolve())
            except ValueError:
                return self._json(403, {"error": "forbidden"})
            if not target.exists():
                return self._json(404, {"error": "missing", "path": str(target)})
            mime = _mime_for(target.suffix) or default_mime
            data = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return Handler

def _mime_for(suffix: str) -> str:
    return {
        ".html": "text/html; charset=utf-8",
        ".css": "text/css",
        ".js": "application/javascript",
        ".json": "application/json",
        ".svg": "image/svg+xml",
        ".png": "image/png",
    }.get(suffix.lower(), "")

def _tail_audit(path: Path, limit: int):
    if not Path(path).exists():
        return []
    # simple backwards read; audit logs are modest in size for this use case
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out
