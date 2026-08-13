"""Lead outbox / handoff — #2117."""

from leads.outbox import accept_lead, build_idempotency_key, classify_referrer, receipt_for


def test_referrer_classes():
    assert classify_referrer(None) == "direct"
    assert classify_referrer("https://www.google.com/search?q=cnpj") == "organic_search"
    assert classify_referrer("https://smartlic.tech/cnpj/123") == "internal"
    assert classify_referrer("https://linkedin.com/in/x") == "social"


def test_accept_is_idempotent_and_returns_receipt(tmp_path, monkeypatch):
    monkeypatch.setenv("LEAD_OUTBOX_PATH", str(tmp_path / "outbox.jsonl"))
    first = accept_lead(
        {
            "email": "lead@example.com",
            "source": "family_company",
            "cta_id": "cta.company.carteira",
            "entity_public_id": "00000000000191",
            "landing_url": "/cnpj/00000000000191",
        }
    )
    second = accept_lead(
        {
            "email": "lead@example.com",
            "source": "family_company",
            "cta_id": "cta.company.carteira",
            "entity_public_id": "00000000000191",
            "landing_url": "/cnpj/00000000000191",
        }
    )
    assert first["receipt_id"] == second["receipt_id"]
    assert second["deduplicated"] is True
    receipt = receipt_for(first)
    assert receipt["accepted"] is True
    assert receipt["receipt_id"]
    assert "email" not in receipt


def test_idempotency_key_stable():
    a = build_idempotency_key("a@b.com", None, "cnpj", "cta.x", "1", "2026-08-13")
    b = build_idempotency_key("A@B.com", None, "cnpj", "cta.x", "1", "2026-08-13")
    assert a == b
