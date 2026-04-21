"""Smoke tests for ADAM DNA Tool backend.

These are intentionally minimal — enough to make sure the package imports,
configuration loads, and the DNA builder can be instantiated without side
effects. Run with:  pytest backend/tests/ -v
"""
from __future__ import annotations


def test_package_imports():
    """The root backend package must import cleanly and advertise a version."""
    import app  # noqa: F401

    assert hasattr(app, "__version__"), "app.__version__ missing"
    # Version is advertised at /api/info and /api/health, so it must not drift.
    assert app.__version__ == "1.1.0", f"unexpected __version__: {app.__version__!r}"


def test_settings_load():
    """Settings must load without env vars (pydantic-settings defaults)."""
    from app.core.config import Settings

    s = Settings()
    assert s.APP_NAME == "ADAM DNA Tool"
    assert s.APP_VERSION == "1.1.0"


def test_dna_export_has_no_adam_version():
    """Per 2026-04-20 Section 1.3 directive: adam_version is STRIPPED from
    emitted DNA JSON. Downstream tools resolve the latest ADAM book by name.
    """
    from app.models.session import Session
    from app.dna.dna_builder import DNABuilder

    session = Session(company_name="SmokeCo")
    builder = DNABuilder(session)
    dna = builder.export_for_deployment()

    assert "meta" in dna, "emitted DNA is missing the meta block"
    assert "adam_version" not in dna["meta"], (
        "adam_version must be stripped from emitted DNA JSON (Section 1.3)"
    )
    assert dna["meta"]["source"] == "ADAM DNA Tool v1.1"
    assert dna["meta"]["questionnaire_version"] == "1.1"
    assert dna["meta"]["company_name"] == "SmokeCo"


def test_question_inventory_is_13_sections():
    """The 13-section DNA Questionnaire is canonical — guard the count so a
    stray section removal or typo in the dict key can't slip past review.
    """
    from app.dna.dna_builder import QUESTION_INVENTORY

    assert set(QUESTION_INVENTORY.keys()) == {str(n) for n in range(1, 14)}, (
        f"QUESTION_INVENTORY must span sections 1..13, got {sorted(QUESTION_INVENTORY.keys())}"
    )
