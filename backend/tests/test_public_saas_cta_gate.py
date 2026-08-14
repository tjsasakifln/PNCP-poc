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
TRIAL = re.compile(r"teste gr[aá]tis|comece gr[aá]tis|14 dias gr[aá]tis", re.I)


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
