"""Reject new executable paths that revive the retired SmartLic runtime."""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST_PATH = ROOT / ".github" / "runtime-authority-allowlist.json"

EXECUTABLE_ROOTS = (
    ROOT / ".github" / "workflows",
    ROOT / ".aios-core" / "development" / "workflows",
    ROOT / ".aios-core" / "development" / "agent-teams",
    ROOT / "scripts",
    ROOT / "deploy",
    ROOT / "frontend" / "scripts",
    ROOT / "backend" / "scripts",
)
EXECUTABLE_FILES = (
    ROOT / ".env.example",
    ROOT / "package.json",
    ROOT / "railway.toml",
    ROOT / "docker-compose.yml",
    ROOT / "backend" / "Dockerfile",
    ROOT / "frontend" / "railway.toml",
    ROOT / "frontend" / "Dockerfile",
    ROOT / "frontend" / ".env.example",
    ROOT / "backend" / "railway.toml",
    ROOT / "backend" / "railway-worker.toml",
    ROOT / "infra" / "config" / "production.env.example",
    ROOT / "infra" / "config" / "staging.env.example",
)
TEXT_SUFFIXES = {".yml", ".yaml", ".sh", ".py", ".js", ".mjs", ".cjs", ".ts", ".toml", ".json"}
IGNORED_PARTS = {".git", "node_modules", "tests", "test", "fixtures", "docs"}

PROHIBITED = {
    "railway_cli": re.compile(r"\brailway\s+(?:up|redeploy|variables|whoami|link|run)\b", re.I),
    "railway_token": re.compile(r"\bRAILWAY_TOKEN(?:_STAGING)?\b"),
    "railway_runtime_contract": re.compile(
        r"Railway\s+(?:environment|service variable|deployment|injects|handles|redeploy)|"
        r"Set (?:in|the following) Railway",
        re.I,
    ),
    "legacy_services": re.compile(r"\bbidiq-(?:backend|frontend)\b", re.I),
    "supabase_deploy": re.compile(
        r"\bsupabase\s+(?:link|start|stop|migration\s+up|db\s+(?:push|reset))\b", re.I
    ),
    "supabase_runtime_authority": re.compile(
        r"secrets\.(?:NEXT_PUBLIC_)?SUPABASE_|"
        r"https?://(?!(?:test|placeholder)\.supabase\.co\b)[^\s/]+\.supabase\.co\b",
        re.I,
    ),
    "smartlic_product_deploy": re.compile(
        r"(?:deploy|publish|release).{0,80}(?:smartlic\.tech|SmartLic production)|"
        r"(?:smartlic\.tech|SmartLic production).{0,80}(?:deploy|publish|release)",
        re.I | re.S,
    ),
    "smartlic_runtime_topology": re.compile(
        r"/opt/smartlic\b|/etc/smartlic\b|"
        r"\bsmartlic-(?:web|adapter)\.service\b|"
        r"\bSMARTLIC_DOMAIN\b|"
        r"\bNEXT_PUBLIC_SITE_URL=https?://(?:www\.)?smartlic\.tech\b",
        re.I,
    ),
    "smartlic_public_runtime": re.compile(
        r"(?:TARGET|URL|SITE_URL|DEFAULT_URL|BASE_URL|CANONICAL_URL|BACKEND_URL|"
        r"CORS_ORIGINS|--(?:url|target|sitemap)).{0,120}"
        r"https?://(?:www\.)?(?:api\.)?(?:staging\.)?smartlic\.tech\b",
        re.I | re.S,
    ),
}


def candidate_files() -> set[Path]:
    result = {path for path in EXECUTABLE_FILES if path.is_file()}
    for base in EXECUTABLE_ROOTS:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            relative_parts = set(path.relative_to(ROOT).parts)
            if relative_parts & IGNORED_PARTS:
                continue
            if path.resolve() == Path(__file__).resolve():
                continue
            result.add(path)
    return result


def load_allowlist() -> dict[str, dict[str, str]]:
    payload = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    today = dt.date.today()
    allowed: dict[str, dict[str, str]] = {}
    for entry in payload.get("entries", []):
        required = {"path", "owner", "reason", "expires_on"}
        if required - entry.keys():
            raise ValueError(f"allowlist entry missing metadata: {entry}")
        expiry = dt.date.fromisoformat(entry["expires_on"])
        if expiry < today:
            raise ValueError(f"expired runtime-authority allowlist entry: {entry['path']}")
        allowed[entry["path"].replace("\\", "/")] = entry
    return allowed


def main() -> int:
    allowlist = load_allowlist()
    violations: list[str] = []
    for path in sorted(candidate_files()):
        relative = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        matches = [name for name, pattern in PROHIBITED.items() if pattern.search(text)]
        if relative.startswith(".aios-core/development/") and re.search(
            r"smartlic\.tech|\bRailway\b|\bSupabase\b|\bbidiq\b", text, re.I
        ):
            matches.append("legacy_agent_runtime_playbook")
        if matches and relative not in allowlist:
            violations.append(f"{relative}: {', '.join(matches)}")

    if violations:
        print("Runtime authority violation. SmartLic has no product deployment path:")
        for violation in violations:
            print(f"- {violation}")
        print("Historical text belongs under docs/archive. A temporary bridge requires owner/reason/expiry.")
        return 1

    print("Runtime authority guard: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
