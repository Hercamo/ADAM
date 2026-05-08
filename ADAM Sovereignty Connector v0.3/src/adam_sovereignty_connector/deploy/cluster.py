"""Cluster lifecycle: k3d create / destroy / status / image import."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

from adam_sovereignty_connector.config import resource_root
from adam_sovereignty_connector.installers.base import run_cmd

log = logging.getLogger("adam.deploy.cluster")

def _cluster_name(ctx) -> str:
    return ctx.config.cluster.name

def bootstrap(args: Dict[str, Any], ctx) -> Dict[str, Any]:
    name = _cluster_name(ctx)
    cc = ctx.config.cluster
    cmd = [
        "k3d", "cluster", "create", name,
        "--servers", str(cc.servers),
        "--agents", str(cc.agents),
        "--api-port", str(cc.api_port),
        "-p", f"{cc.http_ingress_port}:80@loadbalancer",
        "-p", f"{cc.https_ingress_port}:443@loadbalancer",
        "--registry-create", f"{name}-registry:0.0.0.0:{cc.registry_port}",
        "--k3s-arg", "--disable=traefik@server:*",
        "--wait",
    ]
    result = run_cmd(cmd, check=False, timeout=600)
    kubeconfig = run_cmd(
        ["k3d", "kubeconfig", "merge", name, "--kubeconfig-merge-default", "--kubeconfig-switch-context"],
        check=False, timeout=60,
    )
    return {
        "status": "created" if result.get("returncode") == 0 else "error",
        "cluster": name,
        "create_result": result,
        "kubeconfig_merge": kubeconfig,
    }

def destroy(args: Dict[str, Any], ctx) -> Dict[str, Any]:
    name = _cluster_name(ctx)
    result = run_cmd(["k3d", "cluster", "delete", name], check=False, timeout=300)
    return {"status": "destroyed", "cluster": name, "result": result}

def status(args: Dict[str, Any], ctx) -> Dict[str, Any]:
    name = _cluster_name(ctx)
    cluster_ls = run_cmd(["k3d", "cluster", "list", name, "-o", "json"], check=False, timeout=30)
    nodes = run_cmd(["kubectl", "get", "nodes", "-o", "wide"], check=False, timeout=30)
    pods = run_cmd(["kubectl", "get", "pods", "-A", "-o", "wide"], check=False, timeout=30)
    events = run_cmd(
        ["kubectl", "get", "events", "-A", "--sort-by=.lastTimestamp"],
        check=False, timeout=30,
    )
    return {
        "cluster": name,
        "k3d": cluster_ls,
        "nodes": nodes,
        "pods": pods,
        "recent_events": events,
    }

def import_offline_images(args: Dict[str, Any], ctx) -> Dict[str, Any]:
    """Side-load container images into the k3d cluster from the media folder."""
    media_dir = Path(ctx.config.media_dir) / "images"
    if not media_dir.exists():
        return {"status": "skipped", "reason": f"No images folder at {media_dir}"}
    tars: List[Path] = sorted(media_dir.glob("*.tar"))
    if not tars:
        return {"status": "skipped", "reason": "No .tar images in media folder."}
    name = _cluster_name(ctx)
    results: List[Dict[str, Any]] = []
    for tar in tars:
        r = run_cmd(["k3d", "image", "import", str(tar), "-c", name], check=False, timeout=600)
        results.append({"image": tar.name, "result": r})
    return {"status": "done", "imported": len(results), "details": results}

def list_namespaces(args: Dict[str, Any], ctx) -> Dict[str, Any]:
    return run_cmd(["kubectl", "get", "namespaces", "-o", "json"], check=False, timeout=30)

def list_workloads(args: Dict[str, Any], ctx) -> Dict[str, Any]:
    ns = args.get("namespace")
    cmd = ["kubectl", "get", "deploy,statefulset,daemonset,svc", "-o", "wide"]
    if ns:
        cmd.extend(["-n", ns])
    else:
        cmd.extend(["-A"])
    return run_cmd(cmd, check=False, timeout=30)

def describe_workload(args: Dict[str, Any], ctx) -> Dict[str, Any]:
    name = args["name"]
    ns = args.get("namespace", "default")
    kind = args.get("kind", "deployment")
    return run_cmd(
        ["kubectl", "describe", kind, name, "-n", ns],
        check=False, timeout=60,
    )

def get_logs(args: Dict[str, Any], ctx) -> Dict[str, Any]:
    name = args["name"]
    ns = args.get("namespace", "default")
    tail = str(args.get("tail", 200))
    return run_cmd(
        ["kubectl", "logs", name, "-n", ns, "--tail", tail, "--all-containers=true"],
        check=False, timeout=60,
    )

def manifests_dir() -> Path:
    return resource_root() / "deploy" / "manifests"
