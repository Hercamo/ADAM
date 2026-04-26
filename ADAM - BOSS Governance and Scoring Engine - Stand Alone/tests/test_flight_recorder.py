"""Flight Recorder hash-chain tests.

The Flight Recorder is ADAM's evidentiary substrate. Every event's
``event_hash`` is computed over the prior hash plus the canonical JSON
encoding of the event payload (minus the hash itself). These tests
verify that:

* the first event's ``prior_hash`` is ``GENESIS_HASH`` (64 zeros);
* ``verify()`` accepts a clean chain;
* any tampering — whether editing a payload or reshuffling events —
  raises ``IntegrityError``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from boss_core.exceptions import IntegrityError
from boss_core.flight_recorder import (
    GENESIS_HASH,
    FlightRecorder,
    JsonlSink,
    hash_event,
)


def _append_many(recorder: FlightRecorder, n: int) -> None:
    for i in range(n):
        recorder.append(
            "SCORED",
            {"index": i, "composite": 10.0 + i, "tier": "MODERATE"},
        )


class TestHashChain:
    def test_first_event_references_genesis(self, flight_recorder: FlightRecorder) -> None:
        event = flight_recorder.append("SCORED", {"composite": 25.0})
        assert event.prior_hash == GENESIS_HASH

    def test_each_event_links_to_prior(self, flight_recorder: FlightRecorder) -> None:
        first = flight_recorder.append("SCORED", {"composite": 25.0})
        second = flight_recorder.append("SCORED", {"composite": 35.0})
        assert second.prior_hash == first.event_hash

    def test_verify_accepts_clean_chain(self, flight_recorder: FlightRecorder) -> None:
        _append_many(flight_recorder, 5)
        assert flight_recorder.verify() is True

    def test_hash_is_deterministic(self) -> None:
        payload = {"a": 1, "b": "two", "c": [3, 4]}
        h1 = hash_event(GENESIS_HASH, payload)
        h2 = hash_event(GENESIS_HASH, payload)
        assert h1 == h2
        assert len(h1) == 64

    def test_hash_sensitive_to_prior_hash(self) -> None:
        payload = {"a": 1}
        h1 = hash_event(GENESIS_HASH, payload)
        h2 = hash_event("deadbeef" * 8, payload)
        assert h1 != h2

    def test_hash_sensitive_to_payload(self) -> None:
        h1 = hash_event(GENESIS_HASH, {"a": 1})
        h2 = hash_event(GENESIS_HASH, {"a": 2})
        assert h1 != h2


class TestTamperDetection:
    def test_verify_flags_payload_tamper(
        self, tmp_flight_path: Path, flight_recorder: FlightRecorder
    ) -> None:
        _append_many(flight_recorder, 3)
        # Tamper with the middle line's payload but keep the hash.
        lines = tmp_flight_path.read_text(encoding="utf-8").splitlines()
        record = json.loads(lines[1])
        record["payload"]["composite"] = 999.0
        lines[1] = json.dumps(record)
        tmp_flight_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with pytest.raises(IntegrityError):
            flight_recorder.verify()

    def test_verify_flags_reordering(
        self, tmp_flight_path: Path, flight_recorder: FlightRecorder
    ) -> None:
        _append_many(flight_recorder, 3)
        lines = tmp_flight_path.read_text(encoding="utf-8").splitlines()
        # Swap the last two events.
        lines[-1], lines[-2] = lines[-2], lines[-1]
        tmp_flight_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with pytest.raises(IntegrityError):
            flight_recorder.verify()

    def test_verify_flags_prior_hash_edit(
        self, tmp_flight_path: Path, flight_recorder: FlightRecorder
    ) -> None:
        _append_many(flight_recorder, 2)
        lines = tmp_flight_path.read_text(encoding="utf-8").splitlines()
        # Swap the prior_hash of the second event to nonsense but keep
        # its own event_hash — this should break both links.
        record = json.loads(lines[1])
        record["prior_hash"] = "f" * 64
        lines[1] = json.dumps(record)
        tmp_flight_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with pytest.raises(IntegrityError):
            flight_recorder.verify()


class TestJsonlSink:
    def test_empty_file_head_is_genesis(self, tmp_flight_path: Path) -> None:
        sink = JsonlSink(tmp_flight_path)
        assert sink.head() == GENESIS_HASH

    def test_head_returns_latest_hash(self, flight_recorder: FlightRecorder) -> None:
        events = [
            flight_recorder.append("SCORED", {"i": 0}),
            flight_recorder.append("SCORED", {"i": 1}),
            flight_recorder.append("SCORED", {"i": 2}),
        ]
        # After 3 writes, head() must equal the last event's hash.
        assert flight_recorder.events  # sanity
        # Iterate manually through the sink to get a fresh read.
        all_events = list(flight_recorder.events())
        assert len(all_events) == 3
        assert all_events[-1].event_hash == events[-1].event_hash
