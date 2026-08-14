"""Zero credential in browser artifacts; SELECT-only is covered live."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DSN_RE = re.compile(r"postgres(?:ql)?://[^\s\"']+", re.I)
SKIP_DIRS = {".next", "node_modules", "coverage", ".turbo", "dist", "out"}
SCAN_ROOTS = (
    ROOT / "frontend" / "app",
    ROOT / "frontend" / "lib",
    ROOT / "frontend" / "components",
    ROOT / "frontend" / "next.config.js",
    ROOT / ".env.example",
    ROOT / "deploy" / "netcup",
)


def _iter_source_files():
    for root in SCAN_ROOTS:
        if root.is_file():
            yield root
            continue
        if not root.is_dir():
            continue
        for dirpath, dirnames, filenames in os_walk(root):
            dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
            for name in filenames:
                path = Path(dirpath) / name
                if path.suffix in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".env"}:
                    yield path


def os_walk(root: Path):
    import os

    yield from os.walk(root)


def test_no_public_read_dsn_in_frontend_or_next_public():
    leaks: list[str] = []
    for path in _iter_source_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "NEXT_PUBLIC_PUBLIC_READ" in text or "NEXT_PUBLIC_PUBLIC_READ_V1_DSN" in text:
            leaks.append(f"{path}: NEXT_PUBLIC public_read DSN")
        if path.suffix == ".env" and DSN_RE.search(text) and "example" not in path.name:
            leaks.append(f"{path}: committed DSN")
    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "PUBLIC_READ_V1_DSN=" in env_example
    assert "NEXT_PUBLIC_PUBLIC_READ" not in env_example
    assert leaks == []


def test_netcup_env_keeps_dsn_server_side():
    example = (ROOT / "deploy" / "netcup" / "smartlic.env.example").read_text(encoding="utf-8")
    assert "PUBLIC_READ_V1_DSN=" in example
    assert "NEXT_PUBLIC_PUBLIC_READ_V1_DSN" not in example
