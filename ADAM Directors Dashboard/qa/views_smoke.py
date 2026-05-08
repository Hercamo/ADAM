#!/usr/bin/env python3
"""
ADAM Directors Dashboard — production views smoke
==================================================

Verifies the four director-facing views against live deployment data.

  python3 deployment/NetStreamX/qa/views_smoke.py

Tests, in order:
  1. /api/dashboard/views/health    — service mounted; live paths resolve.
  2. /api/dashboard/dna/sections    — 13 DNA sections; Q + A sourced from
                                       the deployed netstreamx-dna.json;
                                       canonical title fragments present.
  3. /api/dashboard/dna/section/<n> — single-section payload; out-of-range 404.
  4. /api/dashboard/boss/dimension/<dim> — all seven canonical dims;
                                       weight, framework, tier interpretation,
                                       matched rules. Unknown dim 404.
  5. /api/dashboard/lifecycle/<intent_id> — reads chain.sqlite read-only;
                                       returns explicit empty-list on
                                       absent intent (no synthesised events).
  6. Live chain mtime untouched after the suite.

Exit code 0 on full pass; 1 on any failure.
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # deployment/NetStreamX
sys.path.insert(0, str(ROOT / "netstreamx_app"))

from flask import Flask  # noqa: E402

app = Flask(__name__)
import dashboard_views  # noqa: E402
dashboard_views.register(app)
client = app.test_client()

PASS, FAIL = 0, 0
FAILS: list = []


def check(name: str, ok: bool, detail: str = ""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        FAILS.append((name, detail))
        print(f"  FAIL  {name}  ::  {detail}")


def test_health():
    print("\n[1] /api/dashboard/views/health")
    r = client.get("/api/dashboard/views/health")
    check("status 200", r.status_code == 200, f"got {r.status_code}")
    j = r.get_json() or {}
    check("ok=true", j.get("ok") is True, json.dumps(j)[:120])
    check("dna file exists", j.get("dna_exists") is True, str(j.get("dna_path")))
    check("boss config exists", j.get("boss_exists") is True, str(j.get("boss_cfg")))
    check("rules seed exists", j.get("rules_exists") is True, str(j.get("rules_seed")))


def test_dna():
    print("\n[2] /api/dashboard/dna/sections")
    r = client.get("/api/dashboard/dna/sections")
    check("status 200", r.status_code == 200)
    j = r.get_json() or {}
    check("ok=true", j.get("ok") is True)
    check("section_count == 13", j.get("section_count") == 13, str(j.get("section_count")))
    titles = [s["title"] for s in (j.get("sections") or [])]
    must_include = ["Doctrine Identity", "Culture Graph", "Objectives Graph",
                    "Rules & Expectations", "CORE Subgraphs", "BOSS Scoring",
                    "Intent Object", "Agentic Architecture", "Flight Recorder",
                    "Products, Services", "Temporal & Regional", "Cloud Infrastructure",
                    "Resilience"]
    for fragment in must_include:
        check(f"section title contains '{fragment}'",
              any(fragment in t for t in titles), str(titles))
    s1 = next((s for s in j["sections"] if s["id"] == 1), {})
    qs = sum(len(ss["questions"]) for ss in s1.get("subsections", []))
    check("section 1 has questions", qs > 0, f"got {qs}")
    answer = ""
    for ss in s1.get("subsections", []):
        for q in ss.get("questions", []):
            if q.get("id") == "1.1.1":
                answer = q.get("a", "")
    check("1.1.1 answer mentions NetStreamX, Inc.", "NetStreamX" in answer, answer[:120])

    print("\n[3] /api/dashboard/dna/section/<n>")
    r = client.get("/api/dashboard/dna/section/6")
    check("status 200", r.status_code == 200)
    j = r.get_json() or {}
    check("ok=true", j.get("ok") is True)
    check("returns section 6 only", len(j.get("sections", [])) == 1)
    check("section 6 is BOSS",
          "BOSS" in (j["sections"][0]["title"] if j.get("sections") else ""))
    r404 = client.get("/api/dashboard/dna/section/99")
    check("section 99 = 404", r404.status_code == 404)


def test_boss_dimension():
    print("\n[4] /api/dashboard/boss/dimension/<dim>")
    for dim in ("security_impact", "sovereignty_action", "financial_exposure",
                "regulatory_impact", "reputational_risk", "rights_certainty",
                "doctrinal_alignment"):
        r = client.get(f"/api/dashboard/boss/dimension/{dim}")
        check(f"{dim} 200", r.status_code == 200, f"got {r.status_code}")
        j = r.get_json() or {}
        check(f"{dim} ok", j.get("ok") is True, json.dumps(j)[:80])
        check(f"{dim} has weight", isinstance(j.get("weight"), (int, float)),
              str(j.get("weight")))
        check(f"{dim} has tier_interpretation (5 tiers)",
              len(j.get("tier_interpretation") or []) == 5)
        check(f"{dim} has framework string",
              isinstance(j.get("framework"), str) and len(j["framework"]) > 0)
    r404 = client.get("/api/dashboard/boss/dimension/not_a_dim")
    check("unknown dim = 404", r404.status_code == 404)


def test_lifecycle_live_only():
    print("\n[5] /api/dashboard/lifecycle/<intent_id>  (live chain.sqlite, read-only)")
    iid = "00000000-0000-0000-0000-000000000000"
    r = client.get(f"/api/dashboard/lifecycle/{iid}")
    check("status 200", r.status_code == 200)
    j = r.get_json() or {}
    check("ok=true", j.get("ok") is True)
    # Per production spec we never synthesise events. step_count should be
    # 0 for an unknown intent_id when reading from the live chain.
    check("unknown intent returns empty events list (no synthetic data)",
          j.get("step_count") == 0 and isinstance(j.get("events"), list),
          str(j.get("step_count")))
    # Returns the chain path it consulted (production transparency)
    check("chain_path returned",
          isinstance(j.get("chain_path"), str) and j["chain_path"].endswith("chain.sqlite"),
          str(j.get("chain_path")))
    # Out-of-range seq returns 404
    r404 = client.get(f"/api/dashboard/lifecycle/{iid}/event/999999")
    check("event seq 999999 = 404", r404.status_code == 404)


def main():
    chain_path = ROOT.parent.parent / "flight_recorder" / "chain.sqlite"
    chain_mtime_before = chain_path.stat().st_mtime if chain_path.exists() else None

    test_health()
    test_dna()
    test_boss_dimension()
    test_lifecycle_live_only()

    print("\n[6] Live chain integrity")
    if chain_mtime_before is not None:
        chain_mtime_after = chain_path.stat().st_mtime
        check("live chain.sqlite mtime UNCHANGED",
              chain_mtime_before == chain_mtime_after,
              f"before={chain_mtime_before} after={chain_mtime_after}")
    else:
        print("  SKIP no live chain on this host (sandbox)")

    print(f"\n{'='*52}\n{PASS} PASS / {FAIL} FAIL\n{'='*52}")
    if FAIL:
        for n, d in FAILS:
            print(f"  - {n} :: {d}")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
