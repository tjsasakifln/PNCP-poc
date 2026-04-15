"""Pytest configuration for contract tests.

Provides schema fixtures and a ``load_snapshot`` helper so individual
tests can stay declarative (just name the snapshot file).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .contract_validator import load_schema, load_snapshot as _load_snapshot


# ---------------------------------------------------------------------------
# Schema fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def pncp_schema() -> dict:
    return load_schema("pncp_search_response.schema.json")


@pytest.fixture(scope="session")
def pcp_v2_schema() -> dict:
    return load_schema("pcp_v2_search_response.schema.json")


@pytest.fixture(scope="session")
def compras_gov_v3_schema() -> dict:
    return load_schema("compras_gov_v3_search_response.schema.json")


@pytest.fixture(scope="session")
def stripe_schema() -> dict:
    return load_schema("stripe_webhook_event.schema.json")


# ---------------------------------------------------------------------------
# Snapshot helper
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def load_snapshot():
    """Return a session-scoped loader for snapshot files.

    Usage:
        def test_x(load_snapshot, pncp_schema):
            snap = load_snapshot("pncp/pregao_eletronico_modalidade_6.json")
            ...
    """

    def _loader(relative_path: str) -> dict[str, Any]:
        return _load_snapshot(relative_path)

    return _loader


# ---------------------------------------------------------------------------
# Contract tests are self-contained — disable the repo-wide autouse
# fixtures from backend/tests/conftest.py that touch supabase/auth/etc.
# ---------------------------------------------------------------------------


def pytest_collection_modifyitems(config, items):
    """Tag contract tests uniformly.

    All tests under ``tests/contracts/`` carry the ``contract`` marker
    unless they already carry ``external`` (which is opt-in).
    """

    rootpath = Path(__file__).parent.resolve()
    for item in items:
        try:
            if Path(str(item.fspath)).resolve().is_relative_to(rootpath):
                if "external" not in item.keywords and "contract" not in item.keywords:
                    item.add_marker(pytest.mark.contract)
        except (ValueError, OSError):
            continue
