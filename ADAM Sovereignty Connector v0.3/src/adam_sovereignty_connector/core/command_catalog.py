"""Vetted command catalog.

The AI never runs arbitrary shell. Every action it can invoke is declared in
``deploy/catalog/command_catalog.yaml`` with an explicit argument schema, a
risk tier, and the Python callable that executes it. This gives us a narrow,
auditable control surface.

Risk tiers:
    read       -- inspect only (no state change)
    low        -- writes to the cluster, easy to undo
    high       -- installs or modifies the host
    privileged -- destructive or requires elevation (human approval gated)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from adam_sovereignty_connector.config import resource_root

try:
    import yaml
    _HAS_YAML = True
except Exception:  # pragma: no cover
    _HAS_YAML = False


# The registry is populated lazily on first use, mapping command name to
# the Python callable that implements it.
Handler = Callable[[Dict[str, Any], "Context"], Dict[str, Any]]


@dataclass
class CommandSpec:
    name: str
    summary: str
    risk: str                        # read | low | high | privileged
    args_schema: Dict[str, Any] = field(default_factory=dict)
    requires_approval: bool = False
    tags: List[str] = field(default_factory=list)

    def describe(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "summary": self.summary,
            "risk": self.risk,
            "args_schema": self.args_schema,
            "requires_approval": self.requires_approval,
            "tags": self.tags,
        }


@dataclass
class Context:
    """Passed to every handler. Carries config, audit log, and helpers."""
    config: Any
    audit: Any
    orchestrator: Any = None  # set when running inside the orchestrator


class CommandCatalog:
    def __init__(self, specs: List[CommandSpec]) -> None:
        self._specs: Dict[str, CommandSpec] = {s.name: s for s in specs}
        self._handlers: Dict[str, Handler] = {}

    # ---- registration -----------------------------------------------------
    def register(self, name: str, handler: Handler) -> None:
        if name not in self._specs:
            raise KeyError(f"No spec for command: {name}")
        self._handlers[name] = handler

    def bind_defaults(self) -> None:
        """Wire up built-in handlers from installers/ and deploy/ modules."""
        from adam_sovereignty_connector.installers import docker_desktop, k3d, kubectl, helm
        from adam_sovereignty_connector.deploy import cluster, adam_stack

        mapping: Dict[str, Handler] = {
            # --- host prereqs ---
            "check_host": _handler_check_host,
            "install_docker_desktop": docker_desktop.install,
            "install_kubectl": kubectl.install,
            "install_helm": helm.install,
            "install_k3d": k3d.install,
            # --- cluster lifecycle ---
            "bootstrap_cluster": cluster.bootstrap,
            "cluster_status": cluster.status,
            "destroy_cluster": cluster.destroy,
            "import_offline_images": cluster.import_offline_images,
            # --- adam stack ---
            "deploy_namespaces": adam_stack.deploy_namespaces,
            "deploy_constitution": adam_stack.deploy_constitution,
            "deploy_core_engine": adam_stack.deploy_core_engine,
            "deploy_boss_score": adam_stack.deploy_boss_score,
            "deploy_flight_recorder": adam_stack.deploy_flight_recorder,
            "deploy_agent_mesh": adam_stack.deploy_agent_mesh,
            "deploy_security_policies": adam_stack.deploy_security_policies,
            "deploy_all": adam_stack.deploy_all,
            # --- introspection (read-only) ---
            "list_namespaces": cluster.list_namespaces,
            "list_workloads": cluster.list_workloads,
            "describe_workload": cluster.describe_workload,
            "get_logs": cluster.get_logs,
            # --- corpus access for the AI ---
            "list_book_documents": _handler_list_book,
            "read_book_document": _handler_read_book,
            # --- DNA profiles ---
            "list_dna_profiles": _handler_list_dna,
            "load_dna_profile": _handler_load_dna,
            "apply_dna_profile": _handler_apply_dna,
        }
        for name, handler in mapping.items():
            if name in self._specs:
                self.register(name, handler)

    # ---- lookup -----------------------------------------------------------
    def __contains__(self, name: str) -> bool:
        return name in self._specs

    def spec(self, name: str) -> CommandSpec:
        return self._specs[name]

    def specs(self) -> List[CommandSpec]:
        return list(self._specs.values())

    def describe(self) -> List[Dict[str, Any]]:
        return [s.describe() for s in self._specs.values()]

    # ---- execution --------------------------------------------------------
    def execute(
        self,
        name: str,
        args: Dict[str, Any],
        ctx: Context,
    ) -> Dict[str, Any]:
        if name not in self._specs:
            raise KeyError(f"Unknown command: {name}")
        handler = self._handlers.get(name)
        if handler is None:
            raise RuntimeError(
                f"Command '{name}' has no handler bound. Did you call bind_defaults()?"
            )
        self._validate_args(name, args)
        return handler(args, ctx)

    def _validate_args(self, name: str, args: Dict[str, Any]) -> None:
        spec = self._specs[name]
        schema = spec.args_schema or {}
        required = schema.get("required", [])
        for key in required:
            if key not in args:
                raise ValueError(f"Missing required arg '{key}' for '{name}'")
        # light type checks
        props = schema.get("properties", {})
        for key, meta in props.items():
            if key in args and "type" in meta:
                _check_type(name, key, args[key], meta["type"])


def _check_type(cmd: str, key: str, value: Any, expected: str) -> None:
    py_types = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    exp = py_types.get(expected)
    if exp and not isinstance(value, exp):
        raise TypeError(
            f"Arg '{key}' for '{cmd}' must be {expected}, got {type(value).__name__}"
        )


# ---------------------------------------------------------------------------
# Catalog loader
# ---------------------------------------------------------------------------

def catalog_path() -> Path:
    return resource_root() / "deploy" / "catalog" / "command_catalog.yaml"


def load_catalog(path: Optional[Path] = None) -> CommandCatalog:
    p = Path(path) if path else catalog_path()
    if not p.exists():
        raise FileNotFoundError(f"Command catalog not found: {p}")
    text = p.read_text(encoding="utf-8")
    data = _parse(text, p.suffix)
    specs = [_spec_from_dict(d) for d in data.get("commands", [])]
    cat = CommandCatalog(specs)
    cat.bind_defaults()
    return cat


def _parse(text: str, suffix: str) -> Dict[str, Any]:
    if suffix.lower() in {".yaml", ".yml"} and _HAS_YAML:
        return yaml.safe_load(text) or {}
    if suffix.lower() == ".json":
        return json.loads(text or "{}")
    # fallback
    if _HAS_YAML:
        try:
            return yaml.safe_load(text) or {}
        except Exception:
            pass
    return json.loads(text)


def _spec_from_dict(d: Dict[str, Any]) -> CommandSpec:
    return CommandSpec(
        name=d["name"],
        summary=d.get("summary", ""),
        risk=d.get("risk", "low"),
        args_schema=d.get("args_schema", {}),
        requires_approval=bool(d.get("requires_approval", False)),
        tags=list(d.get("tags", [])),
    )


# ---------------------------------------------------------------------------
# Built-in handlers that don't belong to installers/ or deploy/
# ---------------------------------------------------------------------------

def _handler_check_host(args: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
    from adam_sovereignty_connector.core.preflight import gather_host_info
    return gather_host_info(ctx.config)


def _handler_list_book(args: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
    from adam_sovereignty_connector.core.corpus import list_documents
    corpus_dir = args.get("corpus_dir") or ctx.config.corpus_dir
    return {"documents": list_documents(corpus_dir)}


def _handler_read_book(args: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
    from adam_sovereignty_connector.core.corpus import read_document
    corpus_dir = args.get("corpus_dir") or ctx.config.corpus_dir
    return read_document(args["path"], corpus_dir, max_chars=args.get("max_chars", 20000))


def _handler_list_dna(args: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
    from adam_sovereignty_connector.core.dna import discover_profiles
    corpus_dir = args.get("corpus_dir") or ctx.config.corpus_dir
    return {"profiles": discover_profiles(corpus_dir)}


def _handler_load_dna(args: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
    from adam_sovereignty_connector.core.dna import resolve_profile_path
    corpus_dir = args.get("corpus_dir") or ctx.config.corpus_dir
    prof = resolve_profile_path(args.get("name_or_path"), corpus_dir)
    # Return the normalised view — drop the verbose raw payload so the AI
    # doesn't get a 100 KB blob pushed into its context for every call.
    d = prof.to_dict()
    d.pop("raw", None)
    return d


def _handler_apply_dna(args: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
    from adam_sovereignty_connector.core.dna import (
        resolve_profile_path,
        build_values_overlay,
        write_values_overlay,
    )
    from adam_sovereignty_connector.config import program_data_dir

    corpus_dir = args.get("corpus_dir") or ctx.config.corpus_dir
    prof = resolve_profile_path(args.get("name_or_path"), corpus_dir)

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
    out_path = program_data_dir() / "profile-values.yaml"
    written = write_values_overlay(values, out_path)
    return {
        "profile": prof.name,
        "slug": prof.slug,
        "scale": args.get("scale"),
        "overrides": overrides,
        "values_path": str(written),
        "values": values,
    }
