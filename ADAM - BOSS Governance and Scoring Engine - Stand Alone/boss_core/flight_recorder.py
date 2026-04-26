"""Append-only, hash-chained Flight Recorder.

The Flight Recorder is ADAM's evidentiary substrate. Each event embeds
the SHA-256 hash of the prior event plus a canonical JSON encoding of
its own payload. The chain makes tampering detectable and gives every
BOSS score, exception packet, and decision receipt a verifiable lineage.

The default implementation stores events in a JSON Lines file so that
the engine has no hard dependency on a specific database. The API layer
replaces this with a Postgres-backed implementation in production.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from boss_core.exceptions import IntegrityError
from boss_core.schemas import FlightRecorderEvent, utcnow

GENESIS_HASH = "0" * 64


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    """Serialize a payload to canonical, deterministic JSON bytes."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def hash_event(prior_hash: str, payload: dict[str, Any]) -> str:
    """Return hex SHA-256 over (prior_hash || canonical(payload))."""
    hasher = hashlib.sha256()
    hasher.update(prior_hash.encode("utf-8"))
    hasher.update(_canonical_bytes(payload))
    return hasher.hexdigest()


class RecorderSink(Protocol):
    """Storage sink contract for the flight recorder."""

    def head(self) -> str: ...
    def append(self, event: FlightRecorderEvent) -> None: ...
    def events(self) -> Iterator[FlightRecorderEvent]: ...


class JsonlSink:
    """Thread-safe JSON Lines sink. Useful for local dev and tests."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        if not self._path.exists():
            self._path.touch()

    def head(self) -> str:
        last: str | None = None
        with self._path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    last = line
        if last is None:
            return GENESIS_HASH
        payload = json.loads(last)
        return str(payload["event_hash"])

    def append(self, event: FlightRecorderEvent) -> None:
        with self._lock, self._path.open("a", encoding="utf-8") as fh:
            fh.write(event.model_dump_json() + "\n")

    def events(self) -> Iterator[FlightRecorderEvent]:
        with self._path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                yield FlightRecorderEvent.model_validate_json(line)


class FlightRecorder:
    """High-level recorder that wraps a sink and enforces the chain."""

    def __init__(self, sink: RecorderSink, signer: str = "boss-engine") -> None:
        self._sink = sink
        self._signer = signer
        self._lock = threading.Lock()

    def append(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        signer: str | None = None,
    ) -> FlightRecorderEvent:
        with self._lock:
            prior = self._sink.head()
            # Build the typed event first. Hash using the exact same
            # JSON serialization that ``verify`` will use, so every
            # round-trip through Pydantic produces identical bytes.
            provisional = FlightRecorderEvent.model_validate(
                {
                    "event_id": str(uuid4()),
                    "event_type": event_type,
                    "timestamp": utcnow(),
                    "signer": signer or self._signer,
                    "prior_hash": prior,
                    "payload": payload,
                    "event_hash": "0" * 64,  # placeholder; re-computed below
                }
            )
            hashable = provisional.model_dump(mode="json", exclude={"event_hash"})
            event_hash = hash_event(prior, hashable)
            event = provisional.model_copy(update={"event_hash": event_hash})
            self._sink.append(event)
            return event

    def verify(self) -> bool:
        """Walk every event and confirm the chain is intact."""
        prior = GENESIS_HASH
        for event in self._sink.events():
            if event.prior_hash != prior:
                raise IntegrityError(f"prior_hash mismatch at event {event.event_id}")
            # Use ``mode='json'`` so datetime fields are rendered as ISO
            # strings (with the ``T`` separator) — identical to the
            # ``utcnow().isoformat()`` form used when the event was
            # originally hashed in ``append``. Without this, Pydantic
            # returns a native ``datetime`` which ``json.dumps(default=str)``
            # renders with a space separator, breaking the chain.
            payload = event.model_dump(mode="json", exclude={"event_hash"})
            expected = hash_event(event.prior_hash, payload)
            if expected != event.event_hash:
                raise IntegrityError(f"event_hash mismatch at event {event.event_id}")
            prior = event.event_hash
        return True

    def events(self) -> Iterator[FlightRecorderEvent]:
        return self._sink.events()
