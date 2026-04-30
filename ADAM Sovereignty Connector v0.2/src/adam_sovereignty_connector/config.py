"""Centralised configuration for ADAM Sovereignty Connector.

Resolution order (highest precedence first):
    1. CLI flags
    2. Environment variables (ADAM_* prefix)
    3. %PROGRAMDATA%/AdamSovereigntyConnector/config.yaml (Windows)
       or ~/.config/adam-sovereignty-connector/config.yaml (POSIX)
    4. Bundled defaults shipped with the frozen .exe

No secrets are persisted in plaintext; API keys live in Windows Credential
Manager via the `keyring` library when available.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml  # optional
    _HAS_YAML = True
except Exception:  # pragma: no cover
    _HAS_YAML = False


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def resource_root() -> Path:
    """Folder the bundled resources (manifests, catalog, web UI) live in.

    When frozen by PyInstaller, PyInstaller extracts data files under
    ``sys._MEIPASS``. In dev mode we resolve relative to the repo root.
    """
    if _is_frozen():
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[2]


def program_data_dir() -> Path:
    """Per-machine state directory for logs, cluster metadata, audit trail."""
    if os.name == "nt":
        base = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
        return Path(base) / "AdamSovereigntyConnector"
    return Path.home() / ".local" / "share" / "adam-sovereignty-connector"


def user_config_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        return Path(base) / "AdamSovereigntyConnector"
    return Path.home() / ".config" / "adam-sovereignty-connector"


def default_media_dir() -> Path:
    """Sibling 'ADAM_Offline_Media' folder next to the .exe / repo."""
    if _is_frozen():
        exe_dir = Path(sys.executable).resolve().parent
    else:
        exe_dir = resource_root()
    return exe_dir / "ADAM_Offline_Media"


# ---------------------------------------------------------------------------
# Config dataclasses
# ---------------------------------------------------------------------------

@dataclass
class AIBackendConfig:
    kind: str = "anthropic"          # anthropic | openai | ollama | openai_compat
    model: str = "claude-opus-4-7"
    api_key_env: str = "ANTHROPIC_API_KEY"
    base_url: Optional[str] = None   # for openai_compat / ollama
    temperature: float = 0.2
    max_tokens: int = 4096


@dataclass
class ServerConfig:
    http_host: str = "127.0.0.1"
    http_port: int = 8765
    mcp_stdio: bool = True
    mcp_tcp_host: Optional[str] = "127.0.0.1"
    mcp_tcp_port: Optional[int] = 8766
    enable_web_ui: bool = True


@dataclass
class ClusterConfig:
    name: str = "adam-sovereignty"
    k8s_flavor: str = "k3d"          # k3d | kind | rancher-desktop
    servers: int = 1
    agents: int = 2
    registry_port: int = 5001
    api_port: int = 6550
    http_ingress_port: int = 8080
    https_ingress_port: int = 8443


@dataclass
class SecurityConfig:
    require_human_approval: List[str] = field(default_factory=lambda: [
        "install_docker_desktop",
        "reboot_host",
        "destroy_cluster",
        "apply_raw_kubectl",
    ])
    enable_audit_log: bool = True
    audit_log_path: Optional[str] = None  # defaults to program_data_dir()/audit.log


@dataclass
class Config:
    ai: AIBackendConfig = field(default_factory=AIBackendConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    cluster: ClusterConfig = field(default_factory=ClusterConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    media_dir: str = field(default_factory=lambda: str(default_media_dir()))
    corpus_dir: Optional[str] = None  # path to the ADAM Book directory
    program_data: str = field(default_factory=lambda: str(program_data_dir()))
    log_level: str = "INFO"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    # ---- loading / saving -------------------------------------------------
    @classmethod
    def load(cls, explicit_path: Optional[Path] = None) -> "Config":
        cfg = cls()
        candidates: List[Path] = []
        if explicit_path:
            candidates.append(explicit_path)
        candidates.append(user_config_dir() / "config.yaml")
        candidates.append(user_config_dir() / "config.json")

        loaded: Dict[str, Any] = {}
        for path in candidates:
            if path.is_file():
                loaded = _read_structured(path)
                break

        _merge(cfg, loaded)
        _apply_env_overrides(cfg)
        return cfg

    def save(self, path: Optional[Path] = None) -> Path:
        target = path or (user_config_dir() / "config.yaml")
        target.parent.mkdir(parents=True, exist_ok=True)
        data = self.to_dict()
        if _HAS_YAML:
            with target.open("w", encoding="utf-8") as fh:
                yaml.safe_dump(data, fh, sort_keys=False)
        else:
            target = target.with_suffix(".json")
            with target.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
        return target


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _read_structured(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"} and _HAS_YAML:
        return yaml.safe_load(text) or {}
    if path.suffix.lower() == ".json":
        return json.loads(text or "{}")
    # fallback: try YAML if available, else JSON
    if _HAS_YAML:
        try:
            return yaml.safe_load(text) or {}
        except Exception:
            pass
    try:
        return json.loads(text or "{}")
    except Exception:
        return {}


def _merge(cfg: Config, data: Dict[str, Any]) -> None:
    for section_name in ("ai", "server", "cluster", "security"):
        section_data = data.get(section_name)
        if not isinstance(section_data, dict):
            continue
        section_obj = getattr(cfg, section_name)
        for k, v in section_data.items():
            if hasattr(section_obj, k):
                setattr(section_obj, k, v)
    for flat_key in ("media_dir", "corpus_dir", "program_data", "log_level"):
        if flat_key in data and data[flat_key] is not None:
            setattr(cfg, flat_key, data[flat_key])


def _apply_env_overrides(cfg: Config) -> None:
    env = os.environ
    # AI
    if env.get("ADAM_AI_KIND"):
        cfg.ai.kind = env["ADAM_AI_KIND"]
    if env.get("ADAM_AI_MODEL"):
        cfg.ai.model = env["ADAM_AI_MODEL"]
    if env.get("ADAM_AI_BASE_URL"):
        cfg.ai.base_url = env["ADAM_AI_BASE_URL"]
    # Server
    if env.get("ADAM_HTTP_HOST"):
        cfg.server.http_host = env["ADAM_HTTP_HOST"]
    if env.get("ADAM_HTTP_PORT"):
        cfg.server.http_port = int(env["ADAM_HTTP_PORT"])
    # Paths
    if env.get("ADAM_MEDIA_DIR"):
        cfg.media_dir = env["ADAM_MEDIA_DIR"]
    if env.get("ADAM_CORPUS_DIR"):
        cfg.corpus_dir = env["ADAM_CORPUS_DIR"]
    if env.get("ADAM_LOG_LEVEL"):
        cfg.log_level = env["ADAM_LOG_LEVEL"]
