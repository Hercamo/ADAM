"""Deploy the ADAM skeleton into the running k3d cluster.

Each layer is just `kubectl apply -f <manifest>` against a yaml file shipped
with the connector. The manifests are deliberately minimal but real —
namespaces, ServiceAccounts, RBAC, small FastAPI placeholder services for
the CORE Engine / BOSS Score / Flight Recorder / 5-Director Constitution, and
a StatefulSet for the 81-agent mesh. You replace the placeholder images with
your real implementations as you build them.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from adam_sovereignty_connector.deploy.cluster import manifests_dir
from adam_sovereignty_connector.installers.base import run_cmd

log = logging.getLogger("adam.deploy.stack")


def _apply(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"status": "missing", "path": str(path)}
    return run_cmd(["kubectl", "apply", "-f", str(path)], check=False, timeout=180)


def deploy_namespaces(args: Dict[str, Any], ctx) -> Dict[str, Any]:
    return {"namespaces": _apply(manifests_dir() / "00-namespaces.yaml")}


def deploy_security_policies(args: Dict[str, Any], ctx) -> Dict[str, Any]:
    return {"security_policies": _apply(manifests_dir() / "10-security-policies.yaml")}


def deploy_constitution(args: Dict[str, Any], ctx) -> Dict[str, Any]:
    return {"constitution": _apply(manifests_dir() / "20-constitution-directors.yaml")}


def deploy_core_engine(args: Dict[str, Any], ctx) -> Dict[str, Any]:
    return {"core_engine": _apply(manifests_dir() / "30-core-engine.yaml")}


def deploy_boss_score(args: Dict[str, Any], ctx) -> Dict[str, Any]:
    return {"boss_score": _apply(manifests_dir() / "40-boss-score.yaml")}


def deploy_flight_recorder(args: Dict[str, Any], ctx) -> Dict[str, Any]:
    return {"flight_recorder": _apply(manifests_dir() / "50-flight-recorder.yaml")}


def deploy_agent_mesh(args: Dict[str, Any], ctx) -> Dict[str, Any]:
    return {"agent_mesh": _apply(manifests_dir() / "60-agent-mesh.yaml")}


def deploy_all(args: Dict[str, Any], ctx) -> Dict[str, Any]:
    """Deploy every layer in doctrinal order.

    If a DNA profile can be auto-discovered (NetStreamX when the ADAM book
    corpus is mounted), the catalog's ``apply_dna_profile`` handler is
    invoked first to emit ``%PROGRAMDATA%/.../profile-values.yaml``. A
    future helm-driven deploy path will pick this up automatically; the
    plain-manifest path today just records it in the return payload so the
    operator can see which DNA was layered in.

    Optional args:
        skip_dna:  bool — don't try to auto-load a DNA profile.
        scale:     str  — one of ``minimal``, ``showcase``, ``production-like``.
        assets, subscribers, agent_mesh_replicas, core_engine_replicas,
            boss_score_replicas, flight_recorder_storage_gi — passed to
            ``apply_dna_profile`` as scale overrides.
    """
    out: Dict[str, Any] = {}

    if not args.get("skip_dna"):
        try:
            from adam_sovereignty_connector.core.dna import (
                resolve_profile_path, build_values_overlay, write_values_overlay,
            )
            from adam_sovereignty_connector.config import program_data_dir
            prof = resolve_profile_path(
                args.get("name_or_path"), getattr(ctx.config, "corpus_dir", None)
            )
            overrides = {
                k: args[k] for k in (
                    "assets", "subscribers", "agent_mesh_replicas",
                    "core_engine_replicas", "boss_score_replicas",
                    "flight_recorder_storage_gi",
                ) if k in args
            }
            values = build_values_overlay(
                prof, scale=args.get("scale"), overrides=overrides or None
            )
            written = write_values_overlay(
                values, program_data_dir() / "profile-values.yaml"
            )
            out["dna"] = {
                "profile": prof.name,
                "slug": prof.slug,
                "values_path": str(written),
                "scale": args.get("scale"),
                "overrides": overrides,
            }
        except Exception as exc:
            out["dna"] = {"skipped": str(exc)}

    for step, fn in [
        ("namespaces", deploy_namespaces),
        ("security_policies", deploy_security_policies),
        ("constitution", deploy_constitution),
        ("core_engine", deploy_core_engine),
        ("boss_score", deploy_boss_score),
        ("flight_recorder", deploy_flight_recorder),
        ("agent_mesh", deploy_agent_mesh),
    ]:
        out[step] = fn({}, ctx)
    return out
