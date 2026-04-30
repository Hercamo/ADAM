"""Interactive first-run setup (`adam-sovereignty-connector init`)."""
from __future__ import annotations

import logging
from pathlib import Path

from adam_sovereignty_connector.config import Config

log = logging.getLogger("adam.setup")

def run_init(cfg: Config, non_interactive: bool = False) -> int:
    if non_interactive:
        path = cfg.save()
        print(f"Wrote default config to: {path}")
        return 0

    print("ADAM Sovereignty Connector — interactive setup")
    print("-" * 60)

    cfg.ai.kind = _prompt(
        "AI backend [anthropic/openai/ollama/openai_compat]",
        cfg.ai.kind,
        choices={"anthropic", "openai", "ollama", "openai_compat"},
    )
    if cfg.ai.kind == "anthropic":
        cfg.ai.model = _prompt("Claude model", cfg.ai.model or "claude-opus-4-7")
        cfg.ai.api_key_env = _prompt("Env var holding ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY")
    elif cfg.ai.kind == "openai":
        cfg.ai.model = _prompt("OpenAI model", cfg.ai.model or "gpt-4o")
        cfg.ai.api_key_env = _prompt("Env var holding OPENAI_API_KEY", "OPENAI_API_KEY")
    elif cfg.ai.kind == "ollama":
        cfg.ai.model = _prompt("Ollama model tag", cfg.ai.model or "llama3.1:8b")
        cfg.ai.base_url = _prompt("Ollama base URL", cfg.ai.base_url or "http://127.0.0.1:11434")
    elif cfg.ai.kind == "openai_compat":
        cfg.ai.model = _prompt("Model name on the endpoint", cfg.ai.model or "local-model")
        cfg.ai.base_url = _prompt("Endpoint base URL", cfg.ai.base_url or "http://127.0.0.1:8000/v1")
        cfg.ai.api_key_env = _prompt("Env var holding API key (optional)", "OPENAI_COMPAT_API_KEY")

    cfg.server.http_port = int(_prompt("HTTP port", str(cfg.server.http_port)))
    cfg.server.enable_web_ui = _prompt_bool("Enable local web UI?", cfg.server.enable_web_ui)
    cfg.cluster.name = _prompt("k3d cluster name", cfg.cluster.name)
    cfg.cluster.agents = int(_prompt("Number of k3d agents", str(cfg.cluster.agents)))

    default_corpus = cfg.corpus_dir or _guess_corpus()
    cfg.corpus_dir = _prompt("ADAM Book corpus directory (optional)", default_corpus or "")

    cfg.media_dir = _prompt("Offline media directory", cfg.media_dir)

    path = cfg.save()
    print(f"\nConfig written to {path}")
    print("Next steps:")
    print("  adam-sovereignty-connector check")
    print("  adam-sovereignty-connector install --yes")
    print("  adam-sovereignty-connector bootstrap --yes")
    print("  adam-sovereignty-connector deploy --yes")
    print("  adam-sovereignty-connector serve --all")
    return 0

def _prompt(label: str, default: str, choices: set[str] | None = None) -> str:
    while True:
        raw = input(f"{label} [{default}]: ").strip()
        val = raw or default
        if choices and val not in choices:
            print(f"  please pick one of: {sorted(choices)}")
            continue
        return val

def _prompt_bool(label: str, default: bool) -> bool:
    d = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{label} [{d}]: ").strip().lower()
        if not raw:
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False

def _guess_corpus() -> str:
    """Try to locate a sibling 'ADAM Book' directory automatically."""
    here = Path(__file__).resolve()
    for ancestor in [here] + list(here.parents):
        for sibling_name in ("ADAM Book",):
            guess = ancestor.parent / sibling_name
            if guess.is_dir():
                return str(guess)
    return ""
