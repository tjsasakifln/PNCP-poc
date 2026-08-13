#!/usr/bin/env python3
"""Fail if canonical docs still define SmartLic as an independent SaaS.

Guards ADR-STRAT-001 / issue #1262. Stdlib only.

Exit 0 — positioning is coherent.
Exit 1 — one or more contradictions found.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

README = ROOT / "README.md"
LLMS = ROOT / "frontend" / "public" / "llms.txt"
PRD = ROOT / "PRD.md"
ROADMAP = ROOT / "ROADMAP.md"
ADR = ROOT / "docs" / "adr" / "ADR-STRAT-001-smartlic-confenge-inbound.md"
CRITICAL = ROOT / "docs" / "strategy" / "critical-path.md"
RUNTIME = ROOT / "docs" / "strategy" / "runtime-destination.md"
CAPABILITIES = ROOT / "docs" / "strategy" / "capability-disposition-1262.md"

# Claims that define *current* product as independent SaaS.
# Historical mentions in completed ROADMAP phases are outside the header window.
README_FORBIDDEN = [
    r"Paid trials",
    r"Stripe live billing",
    r"SaaS, 14-day free trial",
    r"Business Model\s*\n\s*SaaS",
    r"Production SaaS",
    r"b2b-saas",
    r"b2g-saas",
]
LLMS_FORBIDDEN = [
    r"plataforma SaaS",
    r"/planos",
    r"R\$297/mês",
    r"R\$397/mês",
]
# Only flag affirmative current-state claims. Negations ("não é um SaaS",
# "não tem MRR") in the supersession banner are required, not violations.
PRD_HEADER_FORBIDDEN = [
    r"(?<!não tem )MRR(?!.{0,40}como objetivo)",
    r"objetivo do produto é.{0,40}assinatura",
    r"(?<!não é um )SaaS independente",
]
ROADMAP_HEADER_FORBIDDEN = [
    r"K-factor B2B",
    r"30% signups via viral",
    r"Wave 5 Monetization",
]

REQUIRED_PHRASES = {
    README: [
        "extra-cli",
        "CONFENGE",
        "ADR-STRAT-001",
        "public_read_v1",
        "#1262",
    ],
    LLMS: [
        "CONFENGE",
        "extra-cli",
        "Não é um produto de assinatura",
    ],
    ADR: [
        "Status",
        "Accepted",
        "extra-cli",
        "Warmbly",
        "public_read_v1",
    ],
    CRITICAL: [
        "#1262",
        "#2111",
        "#2113",
        "extra-cli#354",
        "#2108",
        "#2112",
        "Warmbly",
    ],
    RUNTIME: [
        "FastAPI",
        "Redis",
        "ARQ",
        "Supabase",
        "Railway",
        "Warmbly",
    ],
    CAPABILITIES: [
        "KEEP + PRIORITIZE",
        "KEEP + ADAPT",
        "SUNSET",
        "REPLACE",
        "DEFER",
    ],
}


def _read(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def _header(text: str, n_lines: int) -> str:
    return "\n".join(text.splitlines()[:n_lines])


def _search_any(pattern_list: list[str], text: str) -> list[str]:
    hits: list[str] = []
    for pat in pattern_list:
        if re.search(pat, text, flags=re.IGNORECASE | re.MULTILINE):
            hits.append(pat)
    return hits


def main() -> int:
    errors: list[str] = []

    try:
        readme = _read(README)
        llms = _read(LLMS)
        prd = _read(PRD)
        roadmap = _read(ROADMAP)
        adr = _read(ADR)
        contents = {
            README: readme,
            LLMS: llms,
            ADR: adr,
            CRITICAL: _read(CRITICAL),
            RUNTIME: _read(RUNTIME),
            CAPABILITIES: _read(CAPABILITIES),
        }
    except FileNotFoundError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    if "ADR-STRAT-001" not in _header(prd, 40):
        errors.append("PRD.md header (first 40 lines) must cite ADR-STRAT-001")
    if "não é um SaaS independente" not in _header(prd, 40).lower() and "nao e um SaaS independente" not in _header(prd, 40).lower():
        if "não é um produto de assinatura" not in _header(prd, 40).lower() and "inbound da CONFENGE" not in _header(prd, 40):
            errors.append("PRD.md header must state inbound/CONFENGE positioning")

    if "ADR-STRAT-001" not in _header(roadmap, 40):
        errors.append("ROADMAP.md header must cite ADR-STRAT-001")
    if "#1262" not in _header(roadmap, 80):
        errors.append("ROADMAP.md header must cite issue #1262")

    for pat in _search_any(README_FORBIDDEN, readme):
        errors.append(f"README.md still contains forbidden current-SaaS claim: {pat}")
    for pat in _search_any(LLMS_FORBIDDEN, llms):
        errors.append(f"frontend/public/llms.txt still contains forbidden SaaS claim: {pat}")
    for pat in _search_any(PRD_HEADER_FORBIDDEN, _header(prd, 40)):
        errors.append(f"PRD.md header still contains forbidden claim: {pat}")
    for pat in _search_any(ROADMAP_HEADER_FORBIDDEN, _header(roadmap, 25)):
        errors.append(f"ROADMAP.md header still contains superseded growth/SaaS objective: {pat}")

    if not re.search(r"\*\*Status:\*\*\s*Accepted|Status \| Accepted", adr):
        errors.append("ADR-STRAT-001 must have Status Accepted")

    for path, phrases in REQUIRED_PHRASES.items():
        text = contents[path]
        for phrase in phrases:
            if phrase not in text:
                errors.append(f"{path.relative_to(ROOT)} missing required phrase: {phrase!r}")

    if errors:
        print("Strategic positioning check FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("Strategic positioning check passed (ADR-STRAT-001 / #1262).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
