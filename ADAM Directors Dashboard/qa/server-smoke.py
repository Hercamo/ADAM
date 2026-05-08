#!/usr/bin/env python3
"""ADAM Directors Dashboard v0.2 — server-side smoke test.

Boots the dashboard_api Flask blueprint in-process (no HTTP server required),
stubs the Flight Recorder and interface-server collaborators, and exercises
every endpoint including the idempotency contract.

    python qa/server-smoke.py

Exit code 0 on pass; non-zero on any failure.
"""
from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "server"))

# Shared in-memory chain used by the mocked Flight Recorder.
_FAKE_FR = {"events": []}


class _FakeResponse:
    def __init__(self, body=None, status=200, ok=True):
        self._body = body if body is not None else {"ok": True}
        self.status_code = status
        self.ok = ok
        self.text = ""
    def json(self):
        return self._body
    def raise_for_status(self):
        if not self.ok:
            raise RuntimeError(f"HTTP {self.status_code}")


def _fake_post(url, json=None, timeout=None, headers=None, **kw):
    if "/append" in url and json:
        evt = dict(json)
        evt["seq"] = len(_FAKE_FR["events"]) + 1
        evt["timestamp"] = "2026-05-04T12:00:00Z"
        _FAKE_FR["events"].append(evt)
        return _FakeResponse({"ok": True, "seq": evt["seq"]})
    return _FakeResponse({"ok": True})


def _fake_get(url, params=None, timeout=None, headers=None, **kw):
    if "/replay" in url:
        iid = (params or {}).get("intent_id")
        if iid:
            return _FakeResponse([e for e in _FAKE_FR["events"]
                                  if (e.get("evidence") or {}).get("intent_id") == iid])
        limit = (params or {}).get("limit", 100)
        return _FakeResponse(list(reversed(_FAKE_FR["events"][-limit:])))
    if "/pending" in url:
        return _FakeResponse({"queue": {}})
    if "/health" in url:
        return _FakeResponse({"ok": True})
    return _FakeResponse({})


class DashboardApiSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Patches must remain active for the lifetime of the test class so the
        # blueprint sees the fake transport on every request, not just at import.
        cls._patches = [
            mock.patch("requests.post", side_effect=_fake_post),
            mock.patch("requests.get",  side_effect=_fake_get),
        ]
        for p in cls._patches: p.start()

        # Reset shared chain
        _FAKE_FR["events"].clear()

        # Fresh module load with the patches active
        if "dashboard_api" in sys.modules:
            del sys.modules["dashboard_api"]
        import dashboard_api as _da
        cls.da = _da
        from flask import Flask
        cls.app = Flask(__name__)
        cls.da.register(cls.app)
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        for p in cls._patches: p.stop()

    def setUp(self):
        # Force the FR cache to refresh on each test so writes from prior tests
        # are visible to idempotency lookups.
        self.da._FR_CACHE.update({"ts": 0.0, "events": [], "by_intent": {}, "by_action_id": {}})

    def _post(self, path, body=None):
        return self.client.post(path, data=json.dumps(body or {}),
                                headers={"Content-Type": "application/json"})

    # ------------------------------------------------------------------
    def test_01_health(self):
        r = self.client.get("/api/dashboard/health")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["service"], "directors-dashboard-api")
        self.assertEqual(body["version"], "0.2")

    def test_02_bootstrap(self):
        r = self.client.get("/api/dashboard/bootstrap")
        body = r.get_json()
        self.assertTrue(body["ok"])
        self.assertGreaterEqual(len(body["directors"]), 5)
        ids = [d["id"] for d in body["directors"]]
        for must in ("ceo", "cfo", "legal_director", "market_director", "ciso"):
            self.assertIn(must, ids)
        self.assertIn("cpo", ids)
        self.assertIn("cto", ids)
        for d in body["directors"]:
            if d["id"] in ("ceo", "ciso"):
                self.assertTrue(d["edit_all"])

    def test_03_state_demo(self):
        r = self.client.get("/api/dashboard/state?mode=demo")
        body = r.get_json()
        self.assertEqual(body["meta"]["mode"], "demo")
        self.assertIn("queue", body)
        self.assertIn("agent_classes", body)

    def test_04_state_live_falls_back_to_demo_when_empty(self):
        r = self.client.get("/api/dashboard/state?mode=live")
        body = r.get_json()
        self.assertIn("queue", body)
        self.assertIn("flight_recorder", body)

    def test_05_director_scope_ceo_full(self):
        r = self.client.get("/api/dashboard/director/ceo/scope")
        body = r.get_json()
        self.assertGreaterEqual(body["count"], 1)
        self.assertTrue(body["rules"].get("edit_all"))

    def test_06_director_scope_cfo_subset(self):
        ceo  = self.client.get("/api/dashboard/director/ceo/scope").get_json()
        cfo  = self.client.get("/api/dashboard/director/cfo/scope").get_json()
        self.assertGreater(ceo["count"], 0)
        self.assertGreater(cfo["count"], 0)
        self.assertLess(cfo["count"], ceo["count"])

    def test_07_agent_card_demo(self):
        r = self.client.get("/api/dashboard/agent/wg-fin-txn?mode=demo")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["agent_id"], "wg-fin-txn")
        self.assertIn("controls_supported", body)

    def test_08_agent_control_idempotent(self):
        a1 = self._post("/api/dashboard/agent/wg-fin-txn/control",
                        {"action": "restart", "director_id": "ceo", "comment": "test", "idempotency_key": "k1"}).get_json()
        self.assertTrue(a1["ok"])
        self.assertFalse(a1["idempotent"])
        a2 = self._post("/api/dashboard/agent/wg-fin-txn/control",
                        {"action": "restart", "director_id": "ceo", "comment": "test", "idempotency_key": "k1"}).get_json()
        self.assertTrue(a2["ok"])
        self.assertTrue(a2["idempotent"], f"Second submit should be idempotent: {a2}")
        a3 = self._post("/api/dashboard/agent/wg-fin-txn/control",
                        {"action": "restart", "director_id": "ceo", "comment": "test", "idempotency_key": "k2"}).get_json()
        self.assertFalse(a3["idempotent"])

    def test_09_agent_control_scope_denied(self):
        r = self._post("/api/dashboard/agent/wg-sec-threat/control",
                       {"action": "restart", "director_id": "cfo", "comment": "x"}).get_json()
        self.assertFalse(r["ok"])
        self.assertEqual(r["error"], "out_of_scope_for_director")

    def test_10_intent_decision_cross_director_blocked(self):
        r = self._post("/api/dashboard/intent/55555555-5555-4000-8000-000000000005/decision",
                       {"decision": "approve", "director_id": "cfo", "owning_director": "ceo",
                        "comment": "n/a"}).get_json()
        self.assertFalse(r["ok"])
        self.assertEqual(r["error"], "director_cannot_edit_other")

    def test_11_intent_decision_idempotent(self):
        body = {"decision": "approve", "director_id": "ceo", "owning_director": "cfo",
                "comment": "approved", "idempotency_key": "abc"}
        first  = self._post("/api/dashboard/intent/11111111-1111-4000-8000-000000000001/decision", body).get_json()
        second = self._post("/api/dashboard/intent/11111111-1111-4000-8000-000000000001/decision", body).get_json()
        self.assertTrue(first["ok"])
        self.assertFalse(first["idempotent"])
        self.assertTrue(second["ok"])
        self.assertTrue(second["idempotent"], f"Second submit should be idempotent: {second}")

    def test_12_what_if_recompute(self):
        r = self._post("/api/dashboard/intent/11111111-1111-4000-8000-000000000001/what_if",
                       {"dimension_overrides": {"financial_exposure": 90}, "non_idempotent": True}).get_json()
        self.assertTrue(r["ok"])
        self.assertIn("base", r)
        self.assertIn("modified", r)
        self.assertGreater(r["modified"]["score"], r["base"]["score"])

    def test_13_intent_card(self):
        r = self.client.get("/api/dashboard/intent/11111111-1111-4000-8000-000000000001?mode=demo")
        body = r.get_json()
        self.assertTrue(body["ok"])
        self.assertIn("composite", body)
        self.assertGreater(body["composite"]["score"], 0)

    def test_14_intent_card_404(self):
        r = self.client.get("/api/dashboard/intent/no-such-intent?mode=demo")
        self.assertEqual(r.status_code, 404)

    def test_15_proxy_acting_companion_event_written(self):
        n_before = sum(1 for e in _FAKE_FR["events"] if e.get("event_type") == "director_proxy_acting")
        self._post("/api/dashboard/intent/22222222-2222-4000-8000-000000000002/decision",
                   {"decision": "approve", "director_id": "ciso", "owning_director": "ciso",
                    "comment": "isolate confirmed", "idempotency_key": "z1"})
        n_after = sum(1 for e in _FAKE_FR["events"] if e.get("event_type") == "director_proxy_acting")
        self.assertGreater(n_after, n_before)


def main():
    runner = unittest.TextTestRunner(verbosity=2)
    suite  = unittest.defaultTestLoader.loadTestsFromTestCase(DashboardApiSmoke)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
