"""Public pages must consult the shipped adapter, not only render a CTA."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_six_mvp_hubs_call_public_family_read():
    pages = {
        "tender": ROOT / "frontend/app/licitacoes/page.tsx",
        "contract": ROOT / "frontend/app/contratos/page.tsx",
        "company": ROOT / "frontend/app/cnpj/page.tsx",
        "organ": ROOT / "frontend/app/orgaos/page.tsx",
        "municipality": ROOT / "frontend/app/municipios/page.tsx",
        "observatory": ROOT / "frontend/app/observatorio/page.tsx",
    }
    for family, path in pages.items():
        text = path.read_text(encoding="utf-8")
        assert "PublicFamilyRead" in text, path
        assert f'family="{family}"' in text or f"family='{family}'" in text


def test_loader_hits_adapter_route():
    text = (ROOT / "frontend/lib/intelligence/loadPublicFamily.ts").read_text(encoding="utf-8")
    assert "/v1/public-read/" in text
    assert "BACKEND_URL" in text
    assert "PUBLIC_READ_V1_DSN" not in text


def test_hub_read_probes_snapshot_latest_without_painting_empty():
    text = (ROOT / "frontend/app/components/intelligence/PublicFamilyRead.tsx").read_text(
        encoding="utf-8"
    )
    assert 'hubProbe = !publicId' in text or "hubProbe = !publicId" in text
    assert 'current_snapshot' in text
    assert "surfaceStateFromRead" in text
    assert "hubProbe" in text


def test_licitacoes_hub_no_saas_cta():
    text = (ROOT / "frontend/app/licitacoes/page.tsx").read_text(encoding="utf-8")
    assert "Teste grátis" not in text
    assert "/signup" not in text
    assert "PublicFamilyRead" in text
