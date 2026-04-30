"""Command-line interface for ADAM Sovereignty Connector."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from adam_sovereignty_connector import __version__
from adam_sovereignty_connector.config import Config


log = logging.getLogger("adam.cli")


BANNER = r"""
  ___  ____    _    __  __   ___                                 _             _
 / _ \|  _ \  / \  |  \/  | / _ \ ___  _ _ ___ _ _ ___ ___ ___ _(_)_ _  ___ ___| |_ ___ _ _
| | | | | | |/ _ \ | |\/| |( (_) / _ \| '_| -_) '_/ -_) -_) -_)_| | ' \/ -_) _ \  _/ _ \ '_|
|_| |_|____//_/ \_\|_|  |_| \___/\___/|_|  \___|_| \___\___\___(_)_|_||_\___\___/\__\___/_|
                                      ADAM Sovereignty Connector v{version}
""".lstrip("\n")


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="adam-sovereignty-connector",
        description="ADAM Sovereignty Connector — local AI-drivable installer & orchestrator for the ADAM reference stack.",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("--config", type=Path, help="Path to a config.yaml / config.json")
    p.add_argument("--log-level", default=None, help="DEBUG / INFO / WARNING / ERROR")

    sub = p.add_subparsers(dest="command", required=False, metavar="<command>")

    sub.add_parser("banner", help="Print the banner and version")

    p_init = sub.add_parser("init", help="Interactive first-run setup (writes config.yaml)")
    p_init.add_argument("--non-interactive", action="store_true")

    p_check = sub.add_parser("check", help="Pre-flight: verify host, media folder, tools")
    p_check.add_argument("--media-dir", type=Path)

    p_plan = sub.add_parser("plan", help="Show the ordered deployment plan without executing")

    p_install = sub.add_parser("install", help="Install prerequisite host tools (Docker, kubectl, Helm, k3d)")
    p_install.add_argument("--only", nargs="*", help="Only install named tools", default=None)
    p_install.add_argument("--yes", action="store_true", help="Skip confirmation prompts")

    p_bootstrap = sub.add_parser("bootstrap", help="Create the k3d cluster and core infra")
    p_bootstrap.add_argument("--yes", action="store_true")

    p_deploy = sub.add_parser("deploy", help="Deploy the ADAM skeleton into the cluster")
    p_deploy.add_argument("--layer", nargs="*", help="Only deploy named layers", default=None)
    p_deploy.add_argument("--yes", action="store_true")

    p_serve = sub.add_parser("serve", help="Start the HTTP + MCP servers for AI-driven control")
    p_serve.add_argument("--http", action="store_true", help="Enable HTTP server")
    p_serve.add_argument("--mcp-stdio", action="store_true", help="Enable MCP stdio server")
    p_serve.add_argument("--mcp-tcp", action="store_true", help="Enable MCP over TCP")
    p_serve.add_argument("--all", action="store_true", help="Enable every surface")

    p_cmd = sub.add_parser("exec", help="Run a single catalog command (useful for scripting)")
    p_cmd.add_argument("name", help="Command name from the catalog")
    p_cmd.add_argument("--arg", action="append", default=[], metavar="KEY=VALUE")

    sub.add_parser("catalog", help="Print the command catalog as JSON")
    sub.add_parser("status", help="Summarise cluster + ADAM service health")
    sub.add_parser("destroy", help="Tear down the cluster (keeps media folder)")

    p_dna = sub.add_parser("dna", help="Manage DNA profiles (list / show / apply)")
    dna_sub = p_dna.add_subparsers(dest="dna_action", required=True, metavar="<action>")
    dna_sub.add_parser("list", help="List discoverable DNA profiles")
    p_show = dna_sub.add_parser("show", help="Show a profile's normalised summary")
    p_show.add_argument("--name", default=None, help="Profile slug/name/path. Default: NetStreamX.")
    p_apply = dna_sub.add_parser(
        "apply",
        help="Write a Helm values overlay from a DNA profile + optional test-scale knobs.",
    )
    p_apply.add_argument("--name", default=None, help="Profile slug/name/path. Default: NetStreamX.")
    p_apply.add_argument(
        "--scale",
        choices=["minimal", "showcase", "production-like"],
        default=None,
        help="Built-in preset. 'minimal' = 100 assets / 100 subscribers / 9 agents — use for laptop tests.",
    )
    p_apply.add_argument("--assets", type=int, default=None, help="Synthetic asset count (test context)")
    p_apply.add_argument("--subscribers", type=int, default=None, help="Synthetic subscriber count (test context)")
    p_apply.add_argument("--agents", type=int, default=None, dest="agent_mesh_replicas",
                         help="Agent mesh pod count (doctrine = 81, laptop = 9)")

    return p


def _parse_kv_args(pairs):
    """Parse ``--arg KEY=VALUE`` pairs with light type coercion.

    ``true``/``false`` become booleans; purely numeric strings become int or
    float; everything else stays a string. This matches what the catalog's
    JSON-Schema validation expects (integers for counts, booleans for flags).
    Prefix with ``s:`` to force a literal string — e.g. ``--arg name=s:123``.
    """
    out = {}
    for p in pairs or []:
        if "=" not in p:
            raise SystemExit(f"--arg expects KEY=VALUE, got: {p}")
        k, v = p.split("=", 1)
        k = k.strip()
        v = v.strip()
        if v.startswith("s:"):
            out[k] = v[2:]
            continue
        low = v.lower()
        if low in ("true", "false"):
            out[k] = (low == "true")
            continue
        try:
            if v.lstrip("-").isdigit():
                out[k] = int(v)
                continue
            out[k] = float(v)  # raises if not numeric
        except ValueError:
            out[k] = v
    return out


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    cfg = Config.load(args.config)
    if args.log_level:
        cfg.log_level = args.log_level
    _configure_logging(cfg.log_level)

    cmd = args.command or "banner"

    # Lazy imports keep CLI startup snappy and let `--help` work even if
    # optional deps (anthropic, openai, kubernetes) are missing.
    if cmd == "banner":
        print(BANNER.format(version=__version__))
        print("Run 'adam-sovereignty-connector --help' for command list.")
        return 0

    if cmd == "init":
        from adam_sovereignty_connector.core.setup import run_init
        return run_init(cfg, non_interactive=args.non_interactive)

    if cmd == "check":
        from adam_sovereignty_connector.core.preflight import run_preflight
        return run_preflight(cfg, media_dir=args.media_dir)

    if cmd == "plan":
        from adam_sovereignty_connector.core.orchestrator import Orchestrator
        Orchestrator(cfg).print_plan()
        return 0

    if cmd == "install":
        from adam_sovereignty_connector.core.orchestrator import Orchestrator
        return Orchestrator(cfg).install_prereqs(only=args.only, assume_yes=args.yes)

    if cmd == "bootstrap":
        from adam_sovereignty_connector.core.orchestrator import Orchestrator
        return Orchestrator(cfg).bootstrap_cluster(assume_yes=args.yes)

    if cmd == "deploy":
        from adam_sovereignty_connector.core.orchestrator import Orchestrator
        return Orchestrator(cfg).deploy_adam(layers=args.layer, assume_yes=args.yes)

    if cmd == "serve":
        from adam_sovereignty_connector.core.orchestrator import Orchestrator
        enable_http = args.http or args.all
        enable_stdio = args.mcp_stdio or args.all
        enable_tcp = args.mcp_tcp or args.all
        if not (enable_http or enable_stdio or enable_tcp):
            enable_http = True  # sensible default
        return Orchestrator(cfg).serve(
            enable_http=enable_http,
            enable_mcp_stdio=enable_stdio,
            enable_mcp_tcp=enable_tcp,
        )

    if cmd == "exec":
        from adam_sovereignty_connector.core.orchestrator import Orchestrator
        kv = _parse_kv_args(args.arg)
        return Orchestrator(cfg).execute_command(args.name, kv)

    if cmd == "catalog":
        from adam_sovereignty_connector.core.command_catalog import load_catalog
        import json
        print(json.dumps(load_catalog().describe(), indent=2))
        return 0

    if cmd == "status":
        from adam_sovereignty_connector.core.orchestrator import Orchestrator
        return Orchestrator(cfg).status()

    if cmd == "destroy":
        from adam_sovereignty_connector.core.orchestrator import Orchestrator
        return Orchestrator(cfg).destroy()

    if cmd == "dna":
        from adam_sovereignty_connector.core.orchestrator import Orchestrator
        orch = Orchestrator(cfg)
        action = getattr(args, "dna_action", None)
        if action == "list":
            return orch.execute_command("list_dna_profiles", {}, actor="cli", assume_yes=True)
        if action == "show":
            kv = {"name_or_path": args.name} if args.name else {}
            return orch.execute_command("load_dna_profile", kv, actor="cli", assume_yes=True)
        if action == "apply":
            kv: dict = {}
            if args.name: kv["name_or_path"] = args.name
            if args.scale: kv["scale"] = args.scale
            if args.assets is not None: kv["assets"] = args.assets
            if args.subscribers is not None: kv["subscribers"] = args.subscribers
            if args.agent_mesh_replicas is not None: kv["agent_mesh_replicas"] = args.agent_mesh_replicas
            return orch.execute_command("apply_dna_profile", kv, actor="cli", assume_yes=True)
        print("Unknown dna action", file=sys.stderr)
        return 2

    print(f"Unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
