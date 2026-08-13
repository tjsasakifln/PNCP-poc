"""Contract tests for the SmartLic public_read_v1 consumer — #2108."""

from public_read.contract import CONTRACT_FAMILIES, CONTRACT_VERSION, REQUIRED_ENTITY_FIELDS
from public_read.dual_read import compare_reads, is_blocking
from public_read.flags import PublicReadMode, get_public_read_mode, should_read_public
from public_read.isolation import Backpressure, IsolationBudgets


def test_contract_version_and_families():
    assert CONTRACT_VERSION == "v1.0.0"
    assert "tenders" in CONTRACT_FAMILIES
    assert "contracts" in CONTRACT_FAMILIES
    assert "suppliers" in CONTRACT_FAMILIES
    assert "organs" in CONTRACT_FAMILIES
    assert "municipalities" in CONTRACT_FAMILIES
    assert "as_of" in REQUIRED_ENTITY_FIELDS
    assert "reason_codes" in REQUIRED_ENTITY_FIELDS


def test_mode_defaults_off(monkeypatch):
    monkeypatch.delenv("PUBLIC_READ_V1_MODE", raising=False)
    assert get_public_read_mode() is PublicReadMode.OFF
    assert should_read_public() is False


def test_shadow_reads_without_serving(monkeypatch):
    monkeypatch.setenv("PUBLIC_READ_V1_MODE", "shadow")
    assert get_public_read_mode() is PublicReadMode.SHADOW
    assert should_read_public() is True


def test_identity_mismatch_is_blocking():
    codes = compare_reads(
        {"canonical_id": "a"},
        type("R", (), {"entity": type("E", (), {"canonical_id": "b"})(), "row_count": 1})(),
    )
    assert "identity_mismatch" in codes
    assert is_blocking(codes) is True


def test_backpressure_concurrency():
    gate = Backpressure(
        IsolationBudgets(
            pool_limit=1,
            max_concurrency=1,
            statement_timeout_ms=2000,
            lock_timeout_ms=500,
            query_budget_per_min=2,
            connect_timeout_s=1,
        )
    )
    assert gate.acquire() is None
    assert gate.acquire() == "concurrency_budget_exceeded"
    gate.release()
    assert gate.acquire() is None
    gate.release()
    assert gate.acquire() == "query_budget_exceeded"
