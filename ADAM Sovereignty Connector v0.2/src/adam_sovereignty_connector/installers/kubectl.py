"""Install the kubectl binary from the offline media folder."""
from __future__ import annotations

import logging
from typing import Any, Dict

from adam_sovereignty_connector.installers.base import (
    install_binary,
    is_windows,
    on_path,
    require_media_file,
    run_cmd,
)

log = logging.getLogger("adam.install.kubectl")


def install(args: Dict[str, Any], ctx) -> Dict[str, Any]:
    if on_path("kubectl") and not args.get("force"):
        return {"status": "already_installed", "tool": "kubectl"}

    name = "kubectl.exe" if is_windows() else "kubectl"
    source = require_media_file(ctx.config, f"binaries/{name}")
    dest = install_binary(source, name)
    ver = run_cmd([str(dest), "version", "--client=true", "--output=yaml"], check=False, timeout=30)
    return {"status": "installed", "tool": "kubectl", "path": str(dest), "version": ver}
