"""Host pre-flight checks.

Inspects the local host for ADAM readiness. Every check is **advisory**:
missing bits produce a WARNING but the pre-flight always exits 0 so the
operator can proceed regardless. The ADAM doctrine treats the human
operator as the ultimate authority — the Connector never hard-blocks a
deploy on its own heuristics.

Checks:
  * OS family + release (Windows 11 preferred)
  * Administrator / elevated context
  * Free disk (warn <40 GB, recommend 100 GB for full 81-agent mesh)
  * Installed RAM  (warn <32 GB, recommend 64 GB for full 81-agent mesh)
  * CPU logical cores (warn <8, recommend 16+ for full 81-agent mesh)
  * Virtualization hint (for Docker Desktop / Hyper-V)
  * Required binaries present on PATH
  * Offline media folder populated
"""
from __future__ import annotations

import ctypes
import logging
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from adam_sovereignty_connector.config import Config

log = logging.getLogger("adam.preflight")


# ---------------------------------------------------------------------------
# Canonical hardware recommendations — surfaced in README + pre-flight output.
# These match the 81-agent doctrine mesh default in the umbrella chart.
# ---------------------------------------------------------------------------

HW_MIN_RAM_GB = 32           # below this, the full mesh will be tight
HW_RECOMMENDED_RAM_GB = 64   # comfortable showcase
HW_MIN_CORES = 8
HW_RECOMMENDED_CORES = 16
HW_MIN_DISK_GB = 40
HW_RECOMMENDED_DISK_GB = 100


REQUIRED_MEDIA_FILES = [
    # These filenames are conventions the Offline Media Builder produces.
    # The builder itself is a separate scripts/build_offline_media.* utility.
    "binaries/docker-desktop-installer.exe",
    "binaries/kubectl.exe",
    "binaries/helm.exe",
    "binaries/k3d.exe",
    "images/adam-core-engine.tar",
    "images/adam-boss-score.tar",
    "images/adam-flight-recorder.tar",
    "images/adam-constitution-director.tar",
    "images/adam-agent.tar",
    "images/k3d-bundle.tar",
    "MANIFEST.json",
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def gather_host_info(cfg: Config) -> Dict[str, Any]:
    ram_gb = _ram_gb()
    cores = _cpu_cores()
    info: Dict[str, Any] = {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "python": sys.version.split()[0],
        "cwd": os.getcwd(),
        "is_admin": _is_admin(),
        "ram_gb": ram_gb,
        "cpu_cores": cores,
        "path_tools": {
            t: bool(shutil.which(t))
            for t in ["docker", "kubectl", "helm", "k3d", "powershell"]
        },
        "media_dir": str(Path(cfg.media_dir).resolve()),
        "media_present": _check_media(Path(cfg.media_dir)),
        "disk_free_gb": _disk_free_gb(Path(cfg.media_dir).anchor or "."),
        "virtualization": _virtualization_hint(),
        "recommendations": {
            "ram_gb_min": HW_MIN_RAM_GB,
            "ram_gb_recommended": HW_RECOMMENDED_RAM_GB,
            "cores_min": HW_MIN_CORES,
            "cores_recommended": HW_RECOMMENDED_CORES,
            "disk_gb_min": HW_MIN_DISK_GB,
            "disk_gb_recommended": HW_RECOMMENDED_DISK_GB,
        },
    }
    return info


def run_preflight(cfg: Config, media_dir: Optional[Path] = None) -> int:
    """Run all advisory checks and print a summary.

    Returns 0 unconditionally — the operator is always allowed to proceed.
    Warnings are printed but never block the install. See module docstring.
    """
    if media_dir:
        cfg.media_dir = str(media_dir)
    info = gather_host_info(cfg)
    _print_preflight(info)

    warnings, notes = _evaluate(info)

    print()
    if warnings:
        print("Pre-flight warnings (install will continue anyway):")
        for w in warnings:
            print(f"  ! {w}")
    if notes:
        print("Pre-flight notes:")
        for n in notes:
            print(f"  - {n}")
    if not warnings and not notes:
        print("Pre-flight OK — host meets recommended specs.")
    else:
        print("\nPre-flight complete. No hard failures — continuing is always allowed.")
    return 0


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def _evaluate(info: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    warnings: List[str] = []
    notes: List[str] = []

    if info["system"] == "Windows":
        if info["release"] not in ("10", "11"):
            warnings.append(
                f"Windows {info['release']} detected — target is Windows 11 "
                f"(Windows 10 22H2 is tolerated but not recommended)."
            )
    else:
        notes.append(
            f"Running on {info['system']}. Installer actions are Windows-only; "
            f"non-install commands (catalog, serve, status, book tools) still work."
        )

    if info["system"] == "Windows" and not info["is_admin"]:
        warnings.append(
            "Not running as Administrator. Host-level steps "
            "(install, bootstrap) need an elevated shell."
        )

    disk = info.get("disk_free_gb")
    if disk is not None:
        if disk < HW_MIN_DISK_GB:
            warnings.append(
                f"Only {disk} GB free on target drive — below minimum "
                f"{HW_MIN_DISK_GB} GB. {HW_RECOMMENDED_DISK_GB} GB recommended "
                f"for the full 81-agent mesh plus Flight Recorder PVC."
            )
        elif disk < HW_RECOMMENDED_DISK_GB:
            notes.append(
                f"Disk free {disk} GB meets the minimum but is below the "
                f"recommended {HW_RECOMMENDED_DISK_GB} GB."
            )

    ram = info.get("ram_gb")
    if ram is not None:
        if ram < HW_MIN_RAM_GB:
            warnings.append(
                f"Host RAM {ram} GB is below the recommended minimum "
                f"{HW_MIN_RAM_GB} GB. The full 81-agent mesh will be tight. "
                f"Consider `helm upgrade adam deploy/helm/adam-umbrella "
                f"--set agentMesh.replicas=9` for a scaled-down showcase. "
                f"Installing anyway."
            )
        elif ram < HW_RECOMMENDED_RAM_GB:
            notes.append(
                f"Host RAM {ram} GB meets the minimum; {HW_RECOMMENDED_RAM_GB} GB "
                f"is the comfortable showcase target."
            )
    else:
        notes.append("Could not read installed RAM on this host.")

    cores = info.get("cpu_cores")
    if cores is not None:
        if cores < HW_MIN_CORES:
            warnings.append(
                f"Host reports {cores} logical CPU cores — below minimum "
                f"{HW_MIN_CORES}. The 81-agent mesh will contend for cycles. "
                f"Installing anyway."
            )
        elif cores < HW_RECOMMENDED_CORES:
            notes.append(
                f"CPU cores {cores} meet the minimum; {HW_RECOMMENDED_CORES}+ "
                f"is the comfortable showcase target."
            )
    else:
        notes.append("Could not read CPU core count on this host.")

    missing_media = [p for p, ok in info["media_present"].items() if not ok]
    if missing_media:
        warnings.append(
            f"Offline media missing {len(missing_media)} required artifact(s). "
            f"`check` and `install` will report which. Run "
            f"`scripts/build_offline_media.ps1` on a connected workstation."
        )

    return warnings, notes


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _print_preflight(info: Dict[str, Any]) -> None:
    rec = info["recommendations"]
    print("ADAM Sovereignty Connector — pre-flight (advisory)")
    print("-" * 64)
    print(f"Platform        : {info['platform']}")
    print(f"Python          : {info['python']}")
    print(f"Administrator   : {info['is_admin']}")
    print(f"RAM (GB)        : {info['ram_gb']}   "
          f"(min {rec['ram_gb_min']}, recommended {rec['ram_gb_recommended']})")
    print(f"CPU cores       : {info['cpu_cores']}   "
          f"(min {rec['cores_min']}, recommended {rec['cores_recommended']})")
    print(f"Disk free (GB)  : {info['disk_free_gb']}   "
          f"(min {rec['disk_gb_min']}, recommended {rec['disk_gb_recommended']})")
    print(f"Virtualization  : {info['virtualization']}")
    print(f"Media directory : {info['media_dir']}")
    print("Tools on PATH   :")
    for tool, present in info["path_tools"].items():
        mark = "yes" if present else "no"
        print(f"   {tool:<10} {mark}")
    print("Offline media artifacts:")
    for name, present in info["media_present"].items():
        mark = "yes" if present else "missing"
        print(f"   {mark:<8} {name}")


# ---------------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------------

def _is_admin() -> bool:
    if os.name == "nt":
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    return os.geteuid() == 0 if hasattr(os, "geteuid") else False


def _check_media(media_dir: Path) -> Dict[str, bool]:
    out: Dict[str, bool] = {}
    for rel in REQUIRED_MEDIA_FILES:
        out[rel] = (media_dir / rel).exists()
    return out


def _disk_free_gb(drive: str) -> Optional[int]:
    try:
        total, used, free = shutil.disk_usage(drive)
        return round(free / (1024 ** 3))
    except Exception:
        return None


def _ram_gb() -> Optional[int]:
    """Installed RAM in gibibytes. Uses psutil if present, otherwise
    platform-native probes (GlobalMemoryStatusEx on Windows, sysconf on POSIX).
    """
    # Preferred: psutil.
    try:
        import psutil  # type: ignore
        return round(psutil.virtual_memory().total / (1024 ** 3))
    except Exception:
        pass

    # Windows native
    if os.name == "nt":
        try:
            class _MEMSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = _MEMSTATUSEX()
            stat.dwLength = ctypes.sizeof(_MEMSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                return round(stat.ullTotalPhys / (1024 ** 3))
        except Exception:
            return None

    # POSIX / Linux fallback
    try:
        if hasattr(os, "sysconf") and "SC_PAGE_SIZE" in os.sysconf_names and "SC_PHYS_PAGES" in os.sysconf_names:
            page = os.sysconf("SC_PAGE_SIZE")
            pages = os.sysconf("SC_PHYS_PAGES")
            if page > 0 and pages > 0:
                return round((page * pages) / (1024 ** 3))
    except Exception:
        pass
    return None


def _cpu_cores() -> Optional[int]:
    try:
        return os.cpu_count() or None
    except Exception:
        return None


def _virtualization_hint() -> str:
    if os.name != "nt":
        return "n/a (non-Windows)"
    try:
        out = subprocess.check_output(
            ["systeminfo"], stderr=subprocess.DEVNULL, text=True, timeout=15
        )
        if "Hyper-V Requirements" in out:
            return "Hyper-V section present; see `systeminfo` for full details."
    except Exception:
        pass
    return "unknown"
