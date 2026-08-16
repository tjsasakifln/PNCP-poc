"""Static checks for the #2115 deploy kit.

Tests call these functions on the shipped files. They do not talk to
Let's Encrypt, DNS, or any public host.
"""

from __future__ import annotations

from pathlib import Path

from bridge.errors import ManifestError
from bridge.generate import assert_terminator_safe

DEPLOY_DIR = Path(__file__).resolve().parent / "deploy"
GENERATED_CADDY = Path(__file__).resolve().parent / "generated" / "Caddyfile"


def _require(cond: bool, message: str) -> None:
    if not cond:
        raise ManifestError(message)


def assert_unit_safe(text: str, *, kind: str) -> None:
    lowered = text.lower()
    _require("user=root" not in lowered, f"{kind}: não pode correr como root")
    _require("dynamicuser=yes" in lowered or "user=caddy" in lowered or "user=smartlic-bridge" in lowered,
             f"{kind}: precisa de utilizador não-root")
    _require("fastapi" not in lowered, f"{kind}: FastAPI proibido")
    _require("next.js" not in lowered, f"{kind}: Next.js proibido")
    _require("redis" not in lowered, f"{kind}: Redis proibido")
    _require("uvicorn" not in lowered, f"{kind}: uvicorn/product runtime proibido")
    _require(":8000" not in text and ":3000" not in text, f"{kind}: upstream de produto proibido")


def assert_bridge_unit_safe(text: str) -> None:
    assert_unit_safe(text, kind="smartlic-bridge.service")
    _require("--host 127.0.0.1" in text, "bridge unit deve bindar 127.0.0.1")
    _require("--port 8765" in text, "bridge unit deve escutar :8765")
    _require("python3 -m bridge.serve" in text, "bridge unit deve lançar o entry real")
    _require("nonewprivileges=true" in text.lower(), "bridge unit: NoNewPrivileges")


def assert_caddy_unit_safe(text: str) -> None:
    assert_unit_safe(text, kind="caddy-bridge.service")
    _require("cap_net_bind_service" in text.lower(), "caddy unit precisa de CAP_NET_BIND_SERVICE")
    _require("user=caddy" in text.lower(), "caddy unit: User=caddy")


def assert_firewall_safe(text: str) -> None:
    _require("tcp dport { 22, 80, 443 }" in text or "tcp dport {22, 80, 443}" in text,
             "firewall deve permitir só 22/80/443")
    _require("policy drop" in text.lower(), "firewall input policy drop")
    _require("8765" not in text, "8765 não pode estar aberto no host")
    _require(":8000" not in text and ":3000" not in text, "firewall não abre portas de produto")


def validate_deploy_kit(root: Path | None = None) -> None:
    """Fail closed if the shipped kit is incomplete or unsafe."""
    base = Path(__file__).resolve().parent if root is None else root
    caddy = (base / "generated" / "Caddyfile").read_text(encoding="utf-8")
    assert_terminator_safe(caddy)
    assert_bridge_unit_safe((base / "deploy" / "smartlic-bridge.service").read_text(encoding="utf-8"))
    assert_caddy_unit_safe((base / "deploy" / "caddy-bridge.service").read_text(encoding="utf-8"))
    assert_firewall_safe((base / "deploy" / "nftables.conf").read_text(encoding="utf-8"))
    env = (base / "deploy" / "env.example").read_text(encoding="utf-8")
    _require("SMARTLIC_ACME_EMAIL=" in env, "env.example sem SMARTLIC_ACME_EMAIL")
    _require("BRIDGE_PUBLIC_IPV4=" in env, "env.example sem BRIDGE_PUBLIC_IPV4")
    _require("BEGIN " not in env, "env.example não pode conter material de chave")
    for path in (base / "deploy").rglob("*"):
        if path.is_file():
            blob = path.read_bytes()
            if b"BEGIN PRIVATE" in blob or b"BEGIN RSA PRIVATE" in blob:
                raise ManifestError(f"chave privada no kit: {path}")
    writeup = (base / "docs" / "CUTOVER.md").read_text(encoding="utf-8")
    assert_cutover_writeup(writeup)
    readiness = (base / "docs" / "CUTOVER_READINESS.md").read_text(encoding="utf-8")
    assert_cutover_readiness_writeup(readiness)


def assert_cutover_writeup(text: str) -> None:
    _require("CUTOVER_READY" in text, "CUTOVER.md deve conter o token CUTOVER_READY")
    _require(text.count("BLOCKED:<") == 0, "CUTOVER.md não deve misturar BLOCKED:<token> com CUTOVER_READY")
    _require("69.46.46.88" in text, "CUTOVER.md sem baseline apex A")
    _require("69.46.46.117" in text, "CUTOVER.md sem baseline www A")
    _require("127.0.0.1:8765" in text, "CUTOVER.md sem upstream do bridge")
    _require("smartlic.tech" in text and "www.smartlic.tech" in text, "CUTOVER.md sem apex+www")
    _require("Let's Encrypt" in text or "ACME" in text, "CUTOVER.md sem caminho ACME")
    _require("BEGIN PRIVATE" not in text, "CUTOVER.md não pode conter chave privada")
    _require("CUTOVER_READINESS.md" in text, "CUTOVER.md deve apontar para CUTOVER_READINESS.md")
    _require("python3 -m bridge.preflight" in text, "CUTOVER.md deve exigir o preflight como hard gate")
    _require("hard gate" in text.lower(), "CUTOVER.md deve nomear o preflight como hard gate")


def assert_cutover_readiness_writeup(text: str) -> None:
    """Engineering READY vs live BLOCKED must stay separate. Cutover is not applied."""
    _require("## READY" in text, "CUTOVER_READINESS.md sem secção READY")
    _require("## BLOCKED" in text, "CUTOVER_READINESS.md sem secção BLOCKED")
    _require("BRIDGE_PUBLIC_IPV4" in text, "CUTOVER_READINESS.md sem BRIDGE_PUBLIC_IPV4")
    _require("SMARTLIC_ACME_EMAIL" in text or "ACME email" in text, "CUTOVER_READINESS.md sem ACME email")
    _require("python3 -m bridge.generate --rollback" in text, "CUTOVER_READINESS.md sem rollback 410-only")
    _require("python3 -m bridge.preflight" in text, "CUTOVER_READINESS.md deve citar o preflight")
    _require("69.46.46.88" in text, "CUTOVER_READINESS.md sem rollback apex A")
    _require("app.smartlic.tech." in text, "CUTOVER_READINESS.md sem rollback www CNAME")
    lowered = text.lower()
    for banned in (
        "dns applied",
        "tls issued in production",
        "first production 301 observed",
    ):
        _require(banned not in lowered, f"CUTOVER_READINESS.md não pode afirmar {banned!r}")
    _require("does not claim live cutover completed" in lowered, "CUTOVER_READINESS.md deve negar cutover live")
    _require("cutover completed." not in lowered.replace("does not claim live cutover completed.", ""),
             "CUTOVER_READINESS.md não pode afirmar cutover completed")
