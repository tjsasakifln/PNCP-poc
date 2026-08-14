"""Public surfaces must not grow new SaaS CTAs."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "frontend"
PUBLIC_ROOTS = [
    ROOT / "app/casos",
    ROOT / "app/dados",
    ROOT / "app/sobre",
    ROOT / "app/stack",
    ROOT / "app/perguntas",
    ROOT / "app/blog",
    ROOT / "app/cnpj",
    ROOT / "app/orgaos",
    ROOT / "app/municipios",
    ROOT / "app/contratos",
    ROOT / "app/licitacoes",
    ROOT / "app/licitacoes-publicas-2026",
    ROOT / "app/itens",
    ROOT / "app/observatorio",
    ROOT / "app/compliance",
    ROOT / "app/guia",
    ROOT / "app/masterclass",
    ROOT / "app/calculadora",
    ROOT / "app/comparador",
    ROOT / "app/alertas-publicos",
    ROOT / "app/components/landing",
    ROOT / "components/blog",
]

HREF = re.compile(r"""href\s*=\s*(['"`])/?(signup|planos|pricing|fundadores|founding)""")
# Object form used by OpportunitySignalsPanel / AhaMomentPanel.
HREF_OBJECT = re.compile(
    r"""(?:href|secondaryHref)\s*:\s*(['"`])/?(signup|planos|pricing|fundadores|founding)"""
)
TRIAL = re.compile(r"teste gr[aá]tis|comece gr[aá]tis|14 dias gr[aá]tis", re.I)
FAMILY_ROOTS = [
    ROOT / "app/licitacoes",
    ROOT / "app/contratos",
    ROOT / "app/cnpj",
    ROOT / "app/orgaos",
    ROOT / "app/municipios",
    ROOT / "app/observatorio",
    ROOT / "app/calculadora",
]


def test_public_surfaces_have_no_saas_cta_href_or_trial_copy():
    leaks: list[str] = []
    for root in PUBLIC_ROOTS:
        if not root.exists():
            continue
        files = [root] if root.is_file() else list(root.rglob("*.tsx")) + list(root.rglob("*.ts"))
        for path in files:
            text = path.read_text(encoding="utf-8")
            if HREF.search(text) or TRIAL.search(text):
                leaks.append(str(path.relative_to(ROOT)))
    assert leaks == []


def test_mvp_families_have_no_object_saas_href():
    leaks: list[str] = []
    for root in FAMILY_ROOTS:
        if not root.exists():
            continue
        for path in list(root.rglob("*.tsx")) + list(root.rglob("*.ts")):
            text = path.read_text(encoding="utf-8")
            if HREF_OBJECT.search(text) or HREF.search(text):
                leaks.append(str(path.relative_to(ROOT)))
    assert leaks == []


FAMILY_LEADCAPTURE_FILES = [
    ROOT / "app/licitacoes/[setor]/page.tsx",
    ROOT / "app/contratos/orgao/[cnpj]/page.tsx",
    ROOT / "app/cnpj/[cnpj]/page.tsx",
    ROOT / "app/cnpj/page.tsx",
    ROOT / "app/orgaos/[slug]/page.tsx",
    ROOT / "app/orgaos/page.tsx",
    ROOT / "app/municipios/[slug]/page.tsx",
]
LEAD_SOURCE = re.compile(r'<LeadCapture\b[\s\S]*?\bsource="([^"]+)"')
ALLOWLIST = re.compile(r'ALL_SOURCES = frozenset\(\{([\s\S]*?)\}\)', re.M)
ALLOWLIST_ITEM = re.compile(r'"([^"]+)"')


def test_family_leadcapture_sources_are_allowlisted():
    capture = Path(__file__).resolve().parents[1] / "routes" / "lead_capture.py"
    block = ALLOWLIST.search(capture.read_text(encoding="utf-8"))
    assert block, "ALL_SOURCES must stay a frozenset in lead_capture.py"
    allowed = set(ALLOWLIST_ITEM.findall(block.group(1)))
    found: set[str] = set()
    for path in FAMILY_LEADCAPTURE_FILES:
        found.update(LEAD_SOURCE.findall(path.read_text(encoding="utf-8")))
    assert found, "family pages must still embed LeadCapture"
    assert sorted(src for src in found if src not in allowed) == []
