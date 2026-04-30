"""Install Docker Desktop on Windows 11 from the offline media folder.

We expect ``<media>/binaries/docker-desktop-installer.exe`` to be present.
On non-Windows hosts this is a dry-run (logs what it would do).
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from adam_sovereignty_connector.installers.base import (
    is_windows,
    on_path,
    require_media_file,
    run_cmd,
)

log = logging.getLogger("adam.install.docker")


def install(args: Dict[str, Any], ctx) -> Dict[str, Any]:
    if on_path("docker") and not args.get("force"):
        return {"status": "already_installed", "tool": "docker"}

    if not is_windows():
        return {
            "status": "dry_run",
            "message": "Docker Desktop install skipped on non-Windows host.",
        }

    installer = require_media_file(ctx.config, "binaries/docker-desktop-installer.exe")
    flags = [
        "install",
        "--quiet",
        "--accept-license",
        "--backend=wsl-2",
    ]
    result = run_cmd([str(installer), *flags], timeout=1800)
    return {
        "status": "installed" if result.get("returncode", 0) == 0 else "error",
        "tool": "docker-desktop",
        "details": result,
        "next": "A reboot may be required before Docker Desktop is fully operational.",
    }
