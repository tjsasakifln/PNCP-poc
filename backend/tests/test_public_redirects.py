"""Single-hop SaaS redirects from the shipped Next config."""

from __future__ import annotations

import re
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[2] / "frontend" / "next.config.js"

EXPECTED = {
    "/pricing": "/consultoria-b2g",
    "/planos": "/consultoria-b2g",
    "/signup": "/consultoria-b2g",
    "/fundadores": "/sobre",
    "/founding": "/sobre",
}


def _redirects() -> list[tuple[str, str]]:
    text = CONFIG.read_text(encoding="utf-8")
    pairs = re.findall(
        r"source:\s*'([^']+)'\s*,\s*destination:\s*'([^']+)'\s*,\s*permanent:\s*true",
        text,
    )
    return [(src, dest) for src, dest in pairs]


def test_saas_routes_are_single_hop():
    mapping = dict(_redirects())
    for source, dest in EXPECTED.items():
        assert mapping[source] == dest
        assert dest not in EXPECTED
        assert dest not in {"/planos", "/pricing", "/signup", "/fundadores", "/founding"}


def test_no_redirect_loop():
    mapping = dict(_redirects())
    for source, dest in mapping.items():
        hop = dest.split("?")[0]
        assert hop not in mapping or mapping[hop] != source
        # destination of a SaaS route must not itself be a redirect source
        if source in EXPECTED:
            assert hop not in mapping
