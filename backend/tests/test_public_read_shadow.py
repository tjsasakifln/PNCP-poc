"""Shadow dual-read: legacy serves; public_read is compared, not served."""

from public_read.contract import FamilyRead, PublicEntity
from public_read.page_model import family_read_to_page_model
from public_read.serve import serve_family


def test_shadow_serves_legacy_and_classifies(monkeypatch):
    monkeypatch.setenv("PUBLIC_READ_V1_MODE", "shadow")

    public = FamilyRead(
        family="tenders",
        mode="shadow",
        served_from="public_read_v1",
        entity=PublicEntity(
            canonical_id="proc-1",
            family="tenders",
            display_name="Edital extra-cli",
            completeness="COMPLETE",
            freshness="FRESH",
            reason_codes=[],
            provenance={"snapshot_id": "snp-public"},
            payload={"process_key": "proc-1", "contract_value": 50},
        ),
        row_count=1,
    )

    def _fake_read(family, public_id):
        assert family == "tenders"
        assert public_id == "proc-1"
        return public

    monkeypatch.setattr("public_read.serve.read_family", _fake_read)
    served = serve_family(
        "tenders",
        "proc-1",
        legacy={
            "canonical_id": "proc-1",
            "title": "Edital legado",
            "row_count": 1,
            "value": "10",
            "freshness": "STALE",
            "completeness": "INCOMPLETE",
            "provenance": {"snapshot_id": "snp-legacy"},
            "reason_codes": ["stale_or_unknown_freshness"],
        },
    )
    assert served.served_from == "legacy"
    assert served.entity is not None
    assert served.entity.display_name == "Edital legado"
    assert "value_delta" in served.divergence
    assert "freshness_delta" in served.divergence
    page = family_read_to_page_model(served)
    assert page["served_from"] == "legacy"
    assert page["display_name"] == "Edital legado"
    assert page["stale"] is True


def test_off_never_calls_public(monkeypatch):
    monkeypatch.setenv("PUBLIC_READ_V1_MODE", "off")

    def _boom(*_a, **_k):
        raise AssertionError("public_read must not be consulted in off")

    monkeypatch.setattr("public_read.serve.read_family", _boom)
    served = serve_family("tenders", "proc-1", legacy={"canonical_id": "proc-1", "title": "L"})
    assert served.served_from == "legacy"
    assert served.divergence == []


def test_canary_holds_non_tender_family(monkeypatch):
    monkeypatch.setenv("PUBLIC_READ_V1_MODE", "canary")
    monkeypatch.setenv("PUBLIC_READ_CANARY_FAMILY", "tenders")

    def _public(family, public_id):
        return FamilyRead(
            family=family,
            mode="canary",
            served_from="public_read_v1",
            entity=PublicEntity(canonical_id=public_id, family=family, display_name="public"),
            row_count=1,
        )

    monkeypatch.setattr("public_read.serve.read_family", _public)
    served = serve_family(
        "contracts",
        "ctr-1",
        legacy={"canonical_id": "ctr-1", "title": "legado contrato"},
    )
    assert served.served_from == "legacy"
    assert served.entity.display_name == "legado contrato"


def test_canary_serves_tenders_when_identity_matches(monkeypatch):
    monkeypatch.setenv("PUBLIC_READ_V1_MODE", "canary")
    monkeypatch.setenv("PUBLIC_READ_CANARY_FAMILY", "tenders")

    def _public(family, public_id):
        return FamilyRead(
            family=family,
            mode="canary",
            served_from="public_read_v1",
            entity=PublicEntity(
                canonical_id=public_id,
                family=family,
                display_name="public tender",
                completeness="COMPLETE",
                freshness="FRESH",
                provenance={"snapshot_id": "snp-1"},
                payload={"process_key": public_id},
            ),
            row_count=1,
        )

    monkeypatch.setattr("public_read.serve.read_family", _public)
    served = serve_family(
        "tenders",
        "proc-1",
        legacy={
            "canonical_id": "proc-1",
            "title": "legado",
            "row_count": 1,
            "freshness": "FRESH",
            "provenance": {"snapshot_id": "snp-1"},
        },
    )
    assert served.served_from == "public_read_v1"
    assert served.entity.display_name == "public tender"


def test_rollback_to_off_restores_legacy(monkeypatch):
    monkeypatch.setenv("PUBLIC_READ_V1_MODE", "off")
    served = serve_family("tenders", "proc-1", legacy={"canonical_id": "proc-1", "title": "back"})
    assert served.served_from == "legacy"
    assert served.entity.display_name == "back"
