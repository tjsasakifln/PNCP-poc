"""Fail-closed errors for manifesto validation and generation."""

from __future__ import annotations


class ManifestError(ValueError):
    """The manifesto is absent, dirty, incomplete, or unsafe. Do not emit config."""
