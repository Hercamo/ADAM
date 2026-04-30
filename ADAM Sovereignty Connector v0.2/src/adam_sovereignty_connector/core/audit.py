"""Append-only audit log.

Every command invocation (whether from the CLI, HTTP, or MCP) is recorded as
a JSON Lines entry with a monotonic sequence number, a SHA-256 hash chain,
and a UTC timestamp. Tampering or gaps are detectable by replaying the chain.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class AuditRecord:
    seq: int
    id: str
    ts: str
    actor: str               # "cli" | "http" | "mcp:<model>"
    command: str
    arguments: Dict[str, Any]
    result: str              # "pending" | "approved" | "denied" | "ok" | "error"
    details: Dict[str, Any] = field(default_factory=dict)
    prev_hash: str = ""
    hash: str = ""


class AuditLog:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._seq, self._last_hash = self._replay_tail()

    def _replay_tail(self) -> tuple[int, str]:
        if not self.path.exists():
            return (0, "")
        seq, last_hash = 0, ""
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    seq = int(rec.get("seq", seq))
                    last_hash = rec.get("hash", last_hash)
                except Exception:
                    # corrupt line; keep going but stop chain advance
                    continue
        return (seq, last_hash)

    def record(
        self,
        actor: str,
        command: str,
        arguments: Dict[str, Any],
        result: str = "pending",
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditRecord:
        with self._lock:
            self._seq += 1
            rec = AuditRecord(
                seq=self._seq,
                id=str(uuid.uuid4()),
                ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                actor=actor,
                command=command,
                arguments=_safe_args(arguments),
                result=result,
                details=details or {},
                prev_hash=self._last_hash,
            )
            rec.hash = self._compute_hash(rec)
            self._last_hash = rec.hash
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec.__dict__, sort_keys=True) + "\n")
                fh.flush()
                try:
                    os.fsync(fh.fileno())
                except OSError:
                    pass
            return rec

    def update_result(self, record_id: str, result: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Append a follow-up record that closes out a pending one."""
        self.record(
            actor="system",
            command="audit.update",
            arguments={"record_id": record_id},
            result=result,
            details=details or {},
        )

    @staticmethod
    def _compute_hash(rec: AuditRecord) -> str:
        payload = json.dumps(
            {k: v for k, v in rec.__dict__.items() if k != "hash"},
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


def _safe_args(args: Dict[str, Any]) -> Dict[str, Any]:
    """Redact obvious secrets before persisting."""
    redacted = {}
    for k, v in (args or {}).items():
        if any(bad in k.lower() for bad in ("key", "token", "secret", "password", "pwd")):
            redacted[k] = "[REDACTED]"
        else:
            redacted[k] = v
    return redacted
