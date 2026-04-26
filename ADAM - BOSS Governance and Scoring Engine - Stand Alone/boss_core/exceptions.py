"""BOSS Engine domain exceptions."""

from __future__ import annotations


class BOSSError(Exception):
    """Base class for BOSS Engine errors."""


class TierConfigurationError(BOSSError):
    """Raised when Priority Tier configuration violates invariants.

    The most common cause is assigning the Top tier to more than one
    dimension, which the ADAM BOSS specification forbids.
    """


class DimensionScoreError(BOSSError):
    """Raised when a dimension scorer receives inputs it cannot score."""


class IntegrityError(BOSSError):
    """Raised when a hash-chained flight recorder append fails integrity checks."""


class AdapterError(BOSSError):
    """Raised when an integration adapter cannot convert external input."""
