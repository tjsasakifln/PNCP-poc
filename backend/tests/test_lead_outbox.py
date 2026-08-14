"""Lead outbox / handoff — #2117."""

import json

import pytest

from leads.outbox import (
    LeadOutboxError,
    accept_lead,
    build_idempotency_key,
    classify_referrer,
    receipt_for,
    redact_for_log,
    reprocess_unfinished,
    reset_outbox_state,
)


@pytest.fixture(autouse=True)
def _isolated_outbox(tmp_path, monkeypatch):
    monkeypatch.setenv("LEAD_OUTBOX_PATH", str(tmp_path / "outbox.jsonl"))
    reset_outbox_state()
    yield
    reset_outbox_state()


def test_referrer_classes():
    assert classify_referrer(None) == "direct"
    assert classify_referrer("https://www.google.com/search?q=cnpj") == "organic_search"
    assert classify_referrer("https://smartlic.tech/cnpj/123") == "internal"
    assert classify_referrer("https://linkedin.com/in/x") == "social"
    assert classify_referrer("https://x.com/confenge") == "social"
    assert classify_referrer("https://twitter.com/confenge") == "social"
    assert classify_referrer("https://not-x.com/path") == "referral"
    assert classify_referrer("https://evilx.com") == "referral"


def _payload(**overrides):
    body = {
        "email": "lead@example.com",
        "source": "family_company",
        "cta_id": "cta.company.carteira",
        "entity_public_id": "00000000000191",
        "landing_url": "/cnpj/00000000000191",
        "nome": "Ana",
        "telefone": "11999999999",
        "mensagem": "segredo",
    }
    body.update(overrides)
    return body


def test_accept_is_idempotent_and_returns_receipt():
    first = accept_lead(_payload())
    second = accept_lead(_payload())
    assert first["receipt_id"] == second["receipt_id"]
    assert second["deduplicated"] is True
    receipt = receipt_for(first)
    assert receipt["accepted"] is True
    assert receipt["receipt_id"]
    assert "email" not in receipt
    assert "nome" not in receipt
    assert "telefone" not in receipt


def test_idempotency_survives_process_restart():
    first = accept_lead(_payload())
    reset_outbox_state()
    second = accept_lead(_payload())
    assert first["receipt_id"] == second["receipt_id"]
    assert second["deduplicated"] is True


def test_persist_failure_does_not_mint_lead(tmp_path, monkeypatch):
    blocked = tmp_path / "missing-dir" / "outbox.jsonl"
    monkeypatch.setenv("LEAD_OUTBOX_PATH", str(blocked))
    reset_outbox_state()
    monkeypatch.setattr("leads.outbox.outbox_path", lambda: blocked)
    # Make parent unwritable by pointing at a file-as-directory.
    blocked.parent.write_text("not-a-dir")
    with pytest.raises(LeadOutboxError):
        accept_lead(_payload(email="fail@example.com"))


def test_handoff_failure_keeps_single_lead(monkeypatch):
    def _boom(record):
        record["attempts"] = int(record.get("attempts") or 0) + 1
        raise RuntimeError("destination down")

    monkeypatch.setattr("leads.handoff.deliver_handoff", _boom)
    first = accept_lead(_payload(email="retry@example.com"))
    assert first["handoff_state"] == "failed"
    replayed = reprocess_unfinished()
    assert len(replayed) == 1
    assert replayed[0]["receipt_id"] == first["receipt_id"]


def test_jsonl_has_no_mensagem_and_receipt_has_no_pii(tmp_path):
    record = accept_lead(_payload())
    raw = (tmp_path / "outbox.jsonl").read_text(encoding="utf-8")
    assert "segredo" not in raw
    assert "lead@example.com" in raw
    redacted = redact_for_log(record)
    assert "email" not in redacted
    assert "mensagem" not in redacted
    assert redacted["receipt_id"] == record["receipt_id"]
    lines = [json.loads(line) for line in raw.splitlines() if line.strip()]
    assert lines[0]["idempotency_key"] == record["idempotency_key"]


def test_analytics_failure_does_not_drop_lead(monkeypatch):
    first = accept_lead(_payload(email="analytics@example.com"))

    def _explode(*_a, **_k):
        raise RuntimeError("mixpanel down")

    monkeypatch.setattr("metrics.INBOUND_LEAD_ACCEPTED.labels", _explode, raising=False)
    second = accept_lead(_payload(email="analytics@example.com"))
    assert first["receipt_id"] == second["receipt_id"]


def test_idempotency_key_stable():
    a = build_idempotency_key("a@b.com", None, "cnpj", "cta.x", "1", "2026-08-13")
    b = build_idempotency_key("A@B.com", None, "cnpj", "cta.x", "1", "2026-08-13")
    assert a == b


def test_tenders_vertical_attribution_and_no_pii_in_receipt():
    first = accept_lead(
        _payload(
            source="licitacoes-setor",
            cta_id="cta.tender.go_nogo",
            route_family="tender",
            entity_public_id="saude",
            landing_url="https://smartlic.tech/licitacoes/saude?utm_source=google&utm_medium=organic",
            referrer="https://www.google.com/search?q=licitacoes+saude",
            utm_source="google",
            utm_medium="organic",
            correlation_id="corr-tenders-1",
        )
    )
    second = accept_lead(
        _payload(
            source="licitacoes-setor",
            cta_id="cta.tender.go_nogo",
            route_family="tender",
            entity_public_id="saude",
            landing_url="https://smartlic.tech/licitacoes/saude?utm_source=google&utm_medium=organic",
            referrer="https://www.google.com/search?q=licitacoes+saude",
            utm_source="google",
            utm_medium="organic",
            correlation_id="corr-tenders-1",
        )
    )
    assert first["receipt_id"] == second["receipt_id"]
    assert second["deduplicated"] is True
    assert first["landing_url"].startswith("https://smartlic.tech/licitacoes/saude")
    assert first["route_family"] == "tender"
    assert first["cta_id"] == "cta.tender.go_nogo"
    assert first["utm_source"] == "google"
    assert first["utm_medium"] == "organic"
    assert first["referrer_class"] == "organic_search"
    assert first["correlation_id"] == "corr-tenders-1"
    receipt = receipt_for(first)
    redacted = redact_for_log(first)
    for payload in (receipt, redacted):
        assert "email" not in payload
        assert "nome" not in payload
        assert "telefone" not in payload
        assert "mensagem" not in payload
    assert receipt["accepted"] is True
    assert redacted["landing_url"]
    assert redacted["cta_id"] == "cta.tender.go_nogo"
    assert redacted["route_family"] == "tender"
    assert redacted["correlation_id"] == "corr-tenders-1"
