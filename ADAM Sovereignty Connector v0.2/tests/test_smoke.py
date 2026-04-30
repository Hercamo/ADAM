"""Smoke tests — no cluster required.

Run with:
    PYTHONPATH=src pytest tests/
"""
from __future__ import annotations

import tempfile
from pathlib import Path

def test_config_roundtrip():
    from adam_sovereignty_connector.config import Config
    cfg = Config()
    data = cfg.to_dict()
    assert "ai" in data and "server" in data and "cluster" in data

def test_catalog_loads_and_has_all_commands():
    from adam_sovereignty_connector.core.command_catalog import load_catalog
    cat = load_catalog()
    names = {s.name for s in cat.specs()}
    for required in [
        "check_host", "install_docker_desktop", "bootstrap_cluster",
        "deploy_namespaces", "deploy_core_engine", "deploy_boss_score",
        "deploy_flight_recorder", "deploy_agent_mesh", "cluster_status",
        "read_book_document", "list_book_documents",
        "list_dna_profiles", "load_dna_profile", "apply_dna_profile",
    ]:
        assert required in names, f"catalog missing {required}"

def test_dna_overlay_minimal_scale():
    from adam_sovereignty_connector.core.dna import (
        DNAProfile, build_values_overlay, TEST_SCALE_PROFILES,
    )
    prof = DNAProfile(
        name="TestCo", slug="testco", source_path="<test>",
        mission="m", vision="v",
        directors=["ceo", "cfo", "legal_director", "market_director", "ciso"],
        boss_dimensions={
            "security_impact": 5.0,
            "sovereignty_action": 4.0,
            "financial_exposure": 4.0,
            "regulatory_impact": 3.0,
            "reputational_risk": 3.0,
            "rights_certainty": 3.0,
            "doctrinal_alignment": 2.0,
        },
        boss_thresholds={
            "soap":     {"min": 0,  "max": 10},
            "moderate": {"min": 11, "max": 30},
            "elevated": {"min": 31, "max": 50},
            "high":     {"min": 51, "max": 75},
            "ohshat":   {"min": 76, "max": 100},
        },
    )
    overlay = build_values_overlay(
        prof, scale="minimal",
        overrides={"assets": 100, "subscribers": 100},
    )
    assert overlay["company"]["slug"] == "testco"
    assert overlay["agentMesh"]["replicas"] == TEST_SCALE_PROFILES["minimal"]["agent_mesh_replicas"]
    assert overlay["testContext"]["assets"] == 100
    assert overlay["testContext"]["subscribers"] == 100
    assert overlay["testContext"]["scaleProfile"] == "minimal"

def test_audit_chain_is_consistent():
    from adam_sovereignty_connector.core.audit import AuditLog
    with tempfile.TemporaryDirectory() as tmp:
        log = AuditLog(Path(tmp) / "audit.log")
        r1 = log.record("cli", "x", {"a": 1}, result="ok")
        r2 = log.record("cli", "y", {"b": 2}, result="ok")
        assert r1.prev_hash == ""
        assert r2.prev_hash == r1.hash

def test_audit_redacts_secrets():
    from adam_sovereignty_connector.core.audit import AuditLog
    with tempfile.TemporaryDirectory() as tmp:
        log = AuditLog(Path(tmp) / "audit.log")
        r = log.record("cli", "x", {"api_key": "sk-ant-xxxxx", "model": "claude"}, result="ok")
        assert r.arguments["api_key"] == "[REDACTED]"
        assert r.arguments["model"] == "claude"

def test_mcp_handler_initialize_and_list():
    from adam_sovereignty_connector.config import Config
    from adam_sovereignty_connector.core.orchestrator import Orchestrator
    from adam_sovereignty_connector.mcp.server import MCPHandler
    orch = Orchestrator(Config())
    h = MCPHandler(orch)

    init_resp = h.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert init_resp["result"]["serverInfo"]["name"] == "adam-sovereignty-connector"

    list_resp = h.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    assert len(list_resp["result"]["tools"]) >= 20

def test_command_catalog_argument_validation():
    from adam_sovereignty_connector.config import Config
    from adam_sovereignty_connector.core.command_catalog import load_catalog, Context
    from adam_sovereignty_connector.core.audit import AuditLog
    import pytest

    cat = load_catalog()
    cfg = Config()
    with tempfile.TemporaryDirectory() as tmp:
        ctx = Context(config=cfg, audit=AuditLog(Path(tmp) / "a.log"))
        # read_book_document requires 'path'
        with pytest.raises(ValueError):
            cat.execute("read_book_document", {}, ctx)
