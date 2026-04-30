"""Minimal MCP server.

We implement the JSON-RPC 2.0 subset of the Model Context Protocol that
Claude Desktop / Claude Code expect: ``initialize``, ``tools/list``,
``tools/call``. Two transports are supported:

  * **stdio**  — the canonical MCP transport Claude Desktop uses when it
    spawns the connector as a subprocess.
  * **tcp**    — a newline-delimited JSON-RPC transport for other clients
    and manual testing with ``nc`` / ``telnet``.

This intentionally avoids a dependency on the official ``mcp`` SDK so the
frozen .exe stays tiny and air-gap deployable; if you prefer the SDK, swap
this module out — the catalog layer is unchanged.
"""
from __future__ import annotations

import json
import logging
import socketserver
import sys
from typing import Any, Dict

from adam_sovereignty_connector.core.command_catalog import CommandSpec

log = logging.getLogger("adam.mcp")

SERVER_NAME = "adam-sovereignty-connector"
SERVER_VERSION = "1.1.0"
PROTOCOL_VERSION = "2025-06-18"

# ---------------------------------------------------------------------------
# JSON-RPC handler
# ---------------------------------------------------------------------------

class MCPHandler:
    def __init__(self, orchestrator) -> None:
        self.orch = orchestrator

    # --- MCP tool list / call mapping --------------------------------------
    def _tool_definitions(self) -> list[dict[str, Any]]:
        tools: list[dict[str, Any]] = []
        for spec in self.orch.catalog.specs():
            tools.append({
                "name": spec.name,
                "description": _describe_for_ai(spec),
                "inputSchema": _to_input_schema(spec),
                "annotations": {
                    "risk": spec.risk,
                    "requiresApproval": spec.requires_approval,
                    "tags": spec.tags,
                },
            })
        return tools

    def handle(self, payload: Dict[str, Any]) -> Dict[str, Any] | None:
        method = payload.get("method")
        req_id = payload.get("id")
        params = payload.get("params") or {}

        try:
            if method == "initialize":
                return _ok(req_id, {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "logging": {},
                    },
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                })

            if method in ("notifications/initialized", "initialized"):
                return None  # notifications have no response

            if method == "ping":
                return _ok(req_id, {})

            if method == "tools/list":
                return _ok(req_id, {"tools": self._tool_definitions()})

            if method == "tools/call":
                name = params.get("name")
                args = params.get("arguments") or {}
                if not name:
                    return _err(req_id, -32602, "Missing 'name' in tools/call")
                actor = f"mcp:{params.get('_callerModel', 'unknown')}"
                # Execute via the orchestrator so audit + approval apply.
                result = self.orch.catalog.execute(name, args, self.orch._ctx)
                self.orch.audit.record(actor, name, args, result="ok", details=_trim(result))
                return _ok(req_id, {
                    "content": [{"type": "text", "text": json.dumps(result, default=str, indent=2)}],
                    "isError": False,
                })

            if method == "resources/list":
                # advertise the ADAM corpus as MCP resources so the model can read it directly
                from adam_sovereignty_connector.core.corpus import list_documents
                docs = list_documents(self.orch.cfg.corpus_dir)
                resources = [
                    {
                        "uri": f"adam-book://{d['path']}",
                        "name": d["path"],
                        "mimeType": _guess_mime(d["ext"]),
                    }
                    for d in docs
                ]
                return _ok(req_id, {"resources": resources})

            if method == "resources/read":
                from adam_sovereignty_connector.core.corpus import read_document
                uri = params.get("uri", "")
                rel = uri.replace("adam-book://", "", 1) if uri.startswith("adam-book://") else uri
                doc = read_document(rel, self.orch.cfg.corpus_dir)
                if "error" in doc:
                    return _err(req_id, -32000, doc["error"])
                return _ok(req_id, {
                    "contents": [{
                        "uri": uri,
                        "mimeType": _guess_mime(doc.get("ext", "")),
                        "text": doc.get("content", ""),
                    }]
                })

            return _err(req_id, -32601, f"Method not found: {method}")

        except Exception as e:
            log.exception("MCP handler error on %s", method)
            return _err(req_id, -32000, str(e))

# ---------------------------------------------------------------------------
# Transports
# ---------------------------------------------------------------------------

def serve_stdio(orchestrator) -> None:
    """Blocking stdio JSON-RPC loop."""
    handler = MCPHandler(orchestrator)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            sys.stdout.write(json.dumps(_err(None, -32700, "Parse error")) + "\n")
            sys.stdout.flush()
            continue
        resp = handler.handle(req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

def serve_tcp(orchestrator) -> None:
    cfg = orchestrator.cfg.server
    host = cfg.mcp_tcp_host or "127.0.0.1"
    port = cfg.mcp_tcp_port or 8766
    handler = MCPHandler(orchestrator)

    class _Handler(socketserver.StreamRequestHandler):
        def handle(self):
            log.info("MCP TCP client connected: %s", self.client_address)
            for raw in self.rfile:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    req = json.loads(raw.decode("utf-8"))
                except Exception:
                    self.wfile.write((json.dumps(_err(None, -32700, "Parse error")) + "\n").encode())
                    self.wfile.flush()
                    continue
                resp = handler.handle(req)
                if resp is not None:
                    self.wfile.write((json.dumps(resp) + "\n").encode())
                    self.wfile.flush()

    class _Server(socketserver.ThreadingTCPServer):
        allow_reuse_address = True

    srv = _Server((host, port), _Handler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _ok(req_id, result) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}

def _err(req_id, code, message) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}

def _trim(obj, limit=1200) -> Any:
    try:
        s = json.dumps(obj, default=str)
    except Exception:
        return {"_repr": str(obj)[:limit]}
    if len(s) <= limit:
        return obj
    return {"_truncated": True, "_preview": s[:limit]}

def _describe_for_ai(spec: CommandSpec) -> str:
    base = spec.summary or spec.name
    risk = f"[risk={spec.risk}]"
    approval = " [human approval required]" if spec.requires_approval else ""
    return f"{base} {risk}{approval}"

def _to_input_schema(spec: CommandSpec) -> dict:
    # default if the YAML schema was empty: accept anything, no required args
    if not spec.args_schema:
        return {"type": "object", "properties": {}, "additionalProperties": True}
    return spec.args_schema

def _guess_mime(ext: str) -> str:
    ext = (ext or "").lower().lstrip(".")
    return {
        "md": "text/markdown",
        "txt": "text/plain",
        "yaml": "application/yaml",
        "yml": "application/yaml",
        "json": "application/json",
        "html": "text/html",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pdf": "application/pdf",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }.get(ext, "application/octet-stream")
