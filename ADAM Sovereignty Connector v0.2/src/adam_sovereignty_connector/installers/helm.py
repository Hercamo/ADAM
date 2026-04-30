"""Install Helm from the offline media folder."""
from __future__ import annotations

from typing import Any, Dict

from adam_sovereignty_connector.installers.base import (
    install_binary,
    is_windows,
    on_path,
    require_media_file,
    run_cmd,
)


def install(args: Dict[str, Any], ctx) -> Dict[str, Any]:
    if on_path("helm") and not args.get("force"):
        return {"status": "already_installed", "tool": "helm"}
    name = "helm.exe" if is_windows() else "helm"
    source = require_media_file(ctx.config, f"binaries/{name}")
    dest = install_binary(source, name)
    ver = run_cmd([str(dest), "version", "--short"], check=False, timeout=30)
    return {"status": "installed", "tool": "helm", "path": str(dest), "version": ver}
