"""ADAM DNA profile loader + applier.

The ADAM DNA Deployment Tool produces two artefacts for each company:

  * ``adam-dna-parsed.json``                — the raw questionnaire answers
  * ``config-bundle/adam-master-config.yaml`` — the normalised master config

The Connector can consume either. This module:

  1. Locates a profile (by name, by path, or by scanning the ADAM Book
     corpus for ``example-output-*`` / ``*/config-bundle/`` folders).
  2. Normalises it into a :class:`DNAProfile` dataclass.
  3. Emits a Helm values overlay (``profile-values.yaml``) so that
     ``deploy_all`` can apply company-specific defaults on top of the
     umbrella chart's doctrinal defaults.
  4. Supports *test-scale overrides* — callers can force a scaled-down
     showcase (e.g. 100 assets, 100 subscribers, 9-agent mesh) without
     editing the underlying DNA files.

NetStreamX is the reference profile shipped with the ADAM book and is
auto-discovered when the operator points ``cfg.corpus_dir`` at the book
directory. If nothing is found, the Connector falls back to a built-in
"generic" profile that the operator can edit to taste.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml  # optional but strongly preferred
    _HAS_YAML = True
except Exception:  # pragma: no cover
    _HAS_YAML = False

log = logging.getLogger("adam.dna")

# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass
class DNAProfile:
    """Normalised subset of a DNA bundle that the Connector uses."""

    name: str
    slug: str
    source_path: str

    mission: str = ""
    vision: str = ""
    directors: List[str] = field(default_factory=list)
    boss_dimensions: Dict[str, float] = field(default_factory=dict)
    boss_thresholds: Dict[str, Any] = field(default_factory=dict)
    delegation: Dict[str, Any] = field(default_factory=dict)
    scale: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def _candidate_profile_roots(corpus_dir: Optional[str]) -> List[Path]:
    roots: List[Path] = []
    if corpus_dir:
        roots.append(Path(corpus_dir))
    # APPDATA fallback — where operators might drop their own company profile
    from adam_sovereignty_connector.config import user_config_dir
    roots.append(user_config_dir() / "dna-profiles")
    return roots

def discover_profiles(corpus_dir: Optional[str]) -> List[Dict[str, str]]:
    """Return a list of ``{name, slug, path}`` for every profile found.

    Looks for ``adam-dna-parsed.json`` and/or ``adam-master-config.yaml``
    (and .json equivalents) anywhere under the candidate roots. Dedups by
    directory.
    """
    seen: set = set()
    out: List[Dict[str, str]] = []
    for root in _candidate_profile_roots(corpus_dir):
        if not root.exists():
            continue
        for candidate in root.rglob("adam-dna-parsed.json"):
            d = candidate.parent
            if d in seen:
                continue
            seen.add(d)
            p = _try_load_profile(d)
            if p is not None:
                out.append({"name": p.name, "slug": p.slug, "path": str(d)})
        for candidate in root.rglob("adam-master-config.yaml"):
            d = candidate.parent.parent  # up out of config-bundle/
            if d in seen:
                continue
            seen.add(d)
            p = _try_load_profile(d)
            if p is not None:
                out.append({"name": p.name, "slug": p.slug, "path": str(d)})
    return out

def _try_load_profile(directory: Path) -> Optional[DNAProfile]:
    try:
        return load_profile(directory)
    except Exception as exc:  # pragma: no cover - diagnostic only
        log.debug("skipping %s: %s", directory, exc)
        return None

# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_profile(path_or_name: Path | str, corpus_dir: Optional[str] = None) -> DNAProfile:
    """Load a DNA profile from a directory, file, or friendly name.

    Resolution order:
      1. If ``path_or_name`` is an existing path, use it.
      2. Otherwise, scan ``corpus_dir`` (and APPDATA/dna-profiles) for a
         folder whose slug or company name matches.
      3. Failing both, raise ``FileNotFoundError``.
    """
    p = Path(path_or_name)
    if p.exists():
        return _load_from(p)

    # treat as name / slug
    candidates = discover_profiles(corpus_dir)
    needle = str(path_or_name).strip().lower()
    for c in candidates:
        if c["slug"].lower() == needle or c["name"].lower() == needle:
            return _load_from(Path(c["path"]))

    raise FileNotFoundError(
        f"No DNA profile matching {path_or_name!r}. "
        f"Tried {len(candidates)} discovered profile(s)."
    )

def _load_from(target: Path) -> DNAProfile:
    if target.is_file():
        return _load_from_file(target)
    if target.is_dir():
        master = _first_existing(
            target / "config-bundle" / "adam-master-config.yaml",
            target / "config-bundle" / "adam-master-config.json",
            target / "adam-master-config.yaml",
            target / "adam-master-config.json",
        )
        parsed = _first_existing(
            target / "adam-dna-parsed.json",
            target / "adam-dna-parsed.yaml",
        )
        if master is not None:
            prof = _load_from_file(master)
        elif parsed is not None:
            prof = _load_from_file(parsed)
        else:
            raise FileNotFoundError(
                f"{target} contains neither adam-master-config nor adam-dna-parsed."
            )
        prof.source_path = str(target)
        return prof
    raise FileNotFoundError(str(target))

def _first_existing(*paths: Path) -> Optional[Path]:
    for p in paths:
        if p.is_file():
            return p
    return None

def _load_from_file(path: Path) -> DNAProfile:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        if not _HAS_YAML:
            raise RuntimeError("PyYAML not available; cannot read YAML DNA profile.")
        data = yaml.safe_load(text) or {}
    else:
        data = json.loads(text or "{}")

    # Heuristically pull the canonical fields out of either format.
    company = data.get("company") or data.get("meta") or {}
    name = company.get("company_name") or company.get("name") or "adam-company"
    slug = company.get("slug") or _slugify(name)

    mission = company.get("mission") or _dig_answer(data, "1.1.2")
    vision = company.get("vision") or _dig_answer(data, "1.1.3")

    directors = _extract_directors(data)
    boss_dims = _extract_boss_dimensions(data)
    boss_thresholds = _extract_boss_thresholds(data)
    delegation = _extract_delegation(data)

    return DNAProfile(
        name=str(name),
        slug=str(slug),
        source_path=str(path),
        mission=str(mission) if mission else "",
        vision=str(vision) if vision else "",
        directors=directors,
        boss_dimensions=boss_dims,
        boss_thresholds=boss_thresholds,
        delegation=delegation,
        scale={},
        raw=data,
    )

def _slugify(s: str) -> str:
    out = []
    for ch in s.lower():
        if ch.isalnum():
            out.append(ch)
        elif out and out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-") or "adam-company"

# ---------------------------------------------------------------------------
# Field extractors (tolerant of both master-config and questionnaire JSON)
# ---------------------------------------------------------------------------

def _extract_directors(data: Dict[str, Any]) -> List[str]:
    # 1. master-config "constitution.directors" (preferred)
    constitution = data.get("constitution") or {}
    if isinstance(constitution, dict):
        ds = constitution.get("directors")
        if isinstance(ds, list):
            out = []
            for d in ds:
                if isinstance(d, str):
                    out.append(d)
                elif isinstance(d, dict):
                    out.append(str(d.get("name") or d.get("role") or d.get("id") or ""))
            return [d for d in out if d]
    # 2. doctrinal default (ADAM v1.4 canonical 5-Director Constitution)
    return ["ceo", "cfo", "legal_director", "market_director", "ciso"]

def _extract_boss_dimensions(data: Dict[str, Any]) -> Dict[str, float]:
    boss = data.get("boss") or {}
    if not isinstance(boss, dict):
        return {}
    dims = boss.get("dimensions") or {}
    if isinstance(dims, dict):
        out: Dict[str, float] = {}
        for k, v in dims.items():
            try:
                out[str(k)] = float(v)
            except Exception:
                continue
        return out
    return {}

def _extract_boss_thresholds(data: Dict[str, Any]) -> Dict[str, Any]:
    boss = data.get("boss") or {}
    if not isinstance(boss, dict):
        return {}
    return boss.get("thresholds") or {}

def _extract_delegation(data: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    gov = data.get("governance") or {}
    if isinstance(gov, dict):
        d = gov.get("delegation") or gov.get("thresholds")
        if isinstance(d, dict):
            out.update(d)
    # Also dig answers like "CEO may approve up to $5M per transaction"
    dig = _dig_answer(data, "1.3.1") or _dig_answer(data, "1.3.2")
    if dig:
        out.setdefault("narrative", dig)
    return out

def _dig_answer(data: Dict[str, Any], q_number: str) -> Optional[str]:
    sections = data.get("sections")
    if not isinstance(sections, dict):
        return None
    for _, sec in sections.items():
        if not isinstance(sec, dict):
            continue
        questions = sec.get("questions") or {}
        if q_number in questions and isinstance(questions[q_number], dict):
            ans = questions[q_number].get("answer")
            if ans:
                return str(ans)
    return None

# ---------------------------------------------------------------------------
# Helm values overlay
# ---------------------------------------------------------------------------

# Sensible defaults when the operator wants a scaled-down *test* deploy.
TEST_SCALE_PROFILES: Dict[str, Dict[str, Any]] = {
    "minimal": {
        # For a dev laptop / smoke test.
        "assets": 100,
        "subscribers": 100,
        "agent_mesh_replicas": 9,
        "core_engine_replicas": 1,
        "boss_score_replicas": 1,
        "flight_recorder_storage_gi": 2,
    },
    "showcase": {
        # Default when running on a 64 GB / 16-core workstation.
        "assets": 10_000,
        "subscribers": 10_000,
        "agent_mesh_replicas": 81,
        "core_engine_replicas": 2,
        "boss_score_replicas": 1,
        "flight_recorder_storage_gi": 5,
    },
    "production-like": {
        "assets": 1_000_000,
        "subscribers": 1_000_000,
        "agent_mesh_replicas": 81,
        "core_engine_replicas": 3,
        "boss_score_replicas": 2,
        "flight_recorder_storage_gi": 20,
    },
}

def build_values_overlay(
    profile: DNAProfile,
    scale: Optional[str] = None,
    overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Produce a dict suitable for ``helm -f profile-values.yaml``.

    Parameters
    ----------
    profile
        Loaded DNA profile.
    scale
        Optional name from ``TEST_SCALE_PROFILES`` (``minimal``, ``showcase``,
        ``production-like``). If omitted, uses the chart defaults (81 agents,
        no scale hints).
    overrides
        Ad-hoc overrides merged on top of ``scale``. Keys understood:
        ``assets``, ``subscribers``, ``agent_mesh_replicas``,
        ``core_engine_replicas``, ``boss_score_replicas``,
        ``flight_recorder_storage_gi``.
    """
    s: Dict[str, Any] = {}
    if scale and scale in TEST_SCALE_PROFILES:
        s.update(TEST_SCALE_PROFILES[scale])
    if overrides:
        s.update({k: v for k, v in overrides.items() if v is not None})

    values: Dict[str, Any] = {
        "company": {
            "name": profile.name,
            "slug": profile.slug,
            "mission": profile.mission,
            "vision": profile.vision,
        },
        "constitution": {},
        "coreEngine": {},
        "bossScore": {},
        "flightRecorder": {},
        "agentMesh": {},
    }
    if profile.directors:
        values["constitution"]["directors"] = profile.directors
    if profile.boss_dimensions:
        values["bossScore"]["dimensionsWeights"] = profile.boss_dimensions
    if profile.boss_thresholds:
        values["bossScore"]["thresholds"] = profile.boss_thresholds

    # Scale-driven fields
    if "agent_mesh_replicas" in s:
        values["agentMesh"]["replicas"] = int(s["agent_mesh_replicas"])
    if "core_engine_replicas" in s:
        values["coreEngine"]["replicas"] = int(s["core_engine_replicas"])
    if "boss_score_replicas" in s:
        values["bossScore"]["replicas"] = int(s["boss_score_replicas"])
    if "flight_recorder_storage_gi" in s:
        values["flightRecorder"]["storageGi"] = int(s["flight_recorder_storage_gi"])

    # Test-only scale facts (surfaced as ConfigMap by the chart, used by
    # placeholder services as a sanity-check scale knob).
    test_ctx: Dict[str, Any] = {}
    if "assets" in s:
        test_ctx["assets"] = int(s["assets"])
    if "subscribers" in s:
        test_ctx["subscribers"] = int(s["subscribers"])
    if test_ctx:
        test_ctx["scaleProfile"] = scale or "custom"
        values["testContext"] = test_ctx

    return values

def write_values_overlay(values: Dict[str, Any], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if _HAS_YAML:
        with out_path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(values, fh, sort_keys=False)
    else:
        out_path = out_path.with_suffix(".json")
        with out_path.open("w", encoding="utf-8") as fh:
            json.dump(values, fh, indent=2)
    return out_path

# ---------------------------------------------------------------------------
# Entry-point helpers (used by the command catalog)
# ---------------------------------------------------------------------------

def resolve_profile_path(name_or_path: Optional[str], corpus_dir: Optional[str]) -> DNAProfile:
    """Resolve by explicit path, by profile name, or — when ``name_or_path``
    is falsy — pick the first discovered profile (NetStreamX when the ADAM
    book corpus is mounted).
    """
    if name_or_path:
        return load_profile(name_or_path, corpus_dir=corpus_dir)

    profiles = discover_profiles(corpus_dir)
    if not profiles:
        raise FileNotFoundError(
            "No DNA profile found. Set cfg.corpus_dir to the ADAM Book directory "
            "or drop a profile folder into %APPDATA%/AdamSovereigntyConnector/dna-profiles/."
        )
    # Prefer NetStreamX when present; else first.
    for candidate in profiles:
        if candidate["slug"] == "netstreamx":
            return load_profile(candidate["path"])
    return load_profile(profiles[0]["path"])
