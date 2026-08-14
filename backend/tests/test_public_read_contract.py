"""Contract tests for the SmartLic public_read_v1 consumer — #2108."""

from public_read.canary import CANARY_FAMILY, evaluate_canary_gate
from public_read.contract import (
    CONTRACT_FAMILIES,
    CONTRACT_VERSION,
    REQUIRED_ENTITY_FIELDS,
    FamilyRead,
    PublicEntity,
)
from public_read.dual_read import classify_divergences, compare_reads, is_blocking
from public_read.flags import PublicReadMode, get_public_read_mode, should_read_public, should_serve_public
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
    assert should_serve_public() is False


def test_shadow_reads_without_serving(monkeypatch):
    monkeypatch.setenv("PUBLIC_READ_V1_MODE", "shadow")
    assert get_public_read_mode() is PublicReadMode.SHADOW
    assert should_read_public() is True
    assert should_serve_public() is False


def _public(canonical_id, **kwargs):
    entity = PublicEntity(
        canonical_id=canonical_id,
        family="tenders",
        freshness=kwargs.get("freshness", "FRESH"),
        completeness=kwargs.get("completeness", "COMPLETE"),
        reason_codes=kwargs.get("reason_codes", []),
        provenance=kwargs.get("provenance", {"snapshot_id": "snp-1"}),
        payload=kwargs.get("payload", {"contract_value": 10}),
    )
    return FamilyRead(
        family="tenders",
        mode="shadow",
        served_from=kwargs.get("served_from", "public_read_v1"),
        entity=entity,
        row_count=kwargs.get("row_count", 1),
    )


def test_identity_mismatch_is_blocking():
    codes = compare_reads({"canonical_id": "a"}, _public("b"))
    assert "identity_mismatch" in codes
    assert is_blocking(codes) is True


def test_compare_classifies_each_dimension():
    codes = compare_reads(
        {
            "canonical_id": "proc-1",
            "row_count": 2,
            "value": "10",
            "freshness": "FRESH",
            "provenance": {"snapshot_id": "snp-legacy"},
            "reason_codes": ["ok"],
        },
        _public(
            "proc-1",
            row_count=1,
            freshness="STALE",
            payload={"contract_value": 99},
            provenance={"snapshot_id": "snp-public"},
            reason_codes=["source_watermark_incomplete"],
        ),
    )
    classified = {item.dimension: item.code for item in classify_divergences(codes)}
    assert classified["count"] == "count_delta"
    assert classified["value"] == "value_delta"
    assert classified["freshness"] in {"freshness_delta", "stale_public"}
    assert classified["provenance"] == "provenance_delta"
    assert classified["reason"] == "reason_code_delta"
    assert "identity" not in classified


def test_empty_and_blocked_are_distinct():
    empty = compare_reads(None, FamilyRead(family="tenders", mode="shadow", served_from="public_read_v1"))
    assert "both_empty" in empty
    blocked = compare_reads(
        {"canonical_id": "x", "blocked": True},
        _public("x", freshness="BLOCKED", served_from="blocked"),
    )
    assert "blocked_public" in blocked
    assert "blocked_legacy" in blocked


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


def test_canary_gate_requires_every_check(monkeypatch):
    monkeypatch.setenv("PUBLIC_READ_V1_MODE", "shadow")
    denied = evaluate_canary_gate(
        family="contracts",
        contract_ok=True,
        blocking_divergences=0,
        classified_divergences=0,
        credential_leak_count=0,
        isolation_ok=True,
        last_known_good_ok=True,
        seo_regression=False,
        rollback_ok=True,
        query_budget_ok=True,
        no_write_ok=True,
    )
    assert denied.promote is False
    ready = evaluate_canary_gate(
        family=CANARY_FAMILY,
        contract_ok=True,
        blocking_divergences=0,
        classified_divergences=1,
        credential_leak_count=0,
        isolation_ok=True,
        last_known_good_ok=True,
        seo_regression=False,
        rollback_ok=True,
        query_budget_ok=True,
        no_write_ok=True,
    )
    assert ready.promote is True
    assert ready.family == "tenders"
