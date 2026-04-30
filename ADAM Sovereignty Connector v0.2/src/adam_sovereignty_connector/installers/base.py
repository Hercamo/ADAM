"""Shared helpers for installer modules."""
from __future__ import annotations

import hashlib
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("adam.install")

def is_windows() -> bool:
    return os.name == "nt"

def media_dir(cfg) -> Path:
    return Path(cfg.media_dir).resolve()

def require_media_file(cfg, rel: str) -> Path:
    p = media_dir(cfg) / rel
    if not p.exists():
        raise FileNotFoundError(
            f"Offline media missing '{rel}' at {p}. Populate ADAM_Offline_Media first."
        )
    return p

def run_cmd(cmd: List[str], *, check: bool = True, env: Optional[dict] = None, timeout: int = 600) -> Dict[str, object]:
    log.info("exec: %s", " ".join(str(c) for c in cmd))
    if not is_windows() and cmd and isinstance(cmd[0], str) and cmd[0].endswith(".exe"):
        log.warning("Dry-run: %s (non-Windows host)", cmd[0])
        return {"dry_run": True, "cmd": cmd}
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check,
            env={**os.environ, **(env or {})},
            timeout=timeout,
        )
        return {
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
    except subprocess.CalledProcessError as e:
        return {
            "returncode": e.returncode,
            "stdout": (e.stdout or "").strip(),
            "stderr": (e.stderr or "").strip(),
            "error": str(e),
        }

def on_path(name: str) -> bool:
    return bool(shutil.which(name))

def install_dir() -> Path:
    """Where we drop portable binaries (kubectl, helm, k3d)."""
    if is_windows():
        base = Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "AdamSovereigntyConnector" / "bin"
    else:
        base = Path.home() / ".local" / "adam-sovereignty-connector" / "bin"
    base.mkdir(parents=True, exist_ok=True)
    return base

def install_binary(source: Path, target_name: str) -> Path:
    dest = install_dir() / target_name
    log.info("Copying %s -> %s", source, dest)
    shutil.copy2(source, dest)
    if not is_windows():
        dest.chmod(0o755)
    _ensure_on_path(install_dir())
    return dest

def _ensure_on_path(d: Path) -> None:
    """On Windows we append the install dir to PATH via setx (user scope)."""
    if not is_windows():
        return
    current = os.environ.get("PATH", "")
    if str(d) in current.split(os.pathsep):
        return
    try:
        subprocess.run(["setx", "PATH", current + os.pathsep + str(d)], check=False, timeout=15)
    except Exception:
        log.warning("Could not append %s to PATH via setx; do it manually.", d)

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
