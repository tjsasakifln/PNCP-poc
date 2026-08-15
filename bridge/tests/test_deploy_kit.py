"""Drive shipped deploy-kit validators. No ACME, no DNS writes."""

from __future__ import annotations

import unittest

from bridge.deploy_kit import (
    assert_bridge_unit_safe,
    assert_caddy_unit_safe,
    assert_cutover_writeup,
    assert_firewall_safe,
    validate_deploy_kit,
)
from bridge.errors import ManifestError
from bridge.generate import (
    GENERATED_DIR,
    URI_QUERY_STRIP,
    assert_terminator_safe,
    load_and_compile,
    render_caddyfile,
)


class DeployKitTests(unittest.TestCase):
    def test_shipped_kit_is_safe(self) -> None:
        validate_deploy_kit()

    def test_generated_caddyfile_is_apex_www_acme_to_local_bridge(self) -> None:
        compiled = load_and_compile()
        text = (GENERATED_DIR / "Caddyfile").read_text(encoding="utf-8")
        assert_terminator_safe(text)
        self.assertIn(compiled.manifesto_sha256, text)
        self.assertIn(compiled.config_sha256, text)
        self.assertIn("reverse_proxy 127.0.0.1:8765", text)
        self.assertNotIn("127.0.0.1:8000", text)
        self.assertNotIn("127.0.0.1:3000", text)
        self.assertIn(URI_QUERY_STRIP, text)
        self.assertNotIn("request>uri query", text)

    def test_render_caddyfile_strips_query_with_regexp_not_noop_query_filter(self) -> None:
        import re

        compiled = load_and_compile()
        rendered = render_caddyfile(compiled)
        self.assertIn(URI_QUERY_STRIP, rendered)
        parsed = re.search(r'regexp "([^"]+)" "([^"]*)"', URI_QUERY_STRIP)
        self.assertIsNotNone(parsed)
        pattern, replacement = parsed.group(1), parsed.group(2)
        sample = (
            "/glossario/reajuste?email=ada@example.com&cnpj=00000000000191"
            "&token=secret&utm_source=gsc"
        )
        stripped = re.sub(pattern, replacement, sample)
        self.assertEqual(stripped, "/glossario/reajuste")
        for leaked in ("email", "cnpj", "token", "ada@", "utm_source", "?"):
            self.assertNotIn(leaked, stripped)

    def test_bare_query_filter_is_rejected(self) -> None:
        compiled = load_and_compile()
        broken = render_caddyfile(compiled).replace(
            URI_QUERY_STRIP,
            "request>uri query",
        )
        with self.assertRaises(ManifestError) as ctx:
            assert_terminator_safe(broken)
        self.assertRegex(str(ctx.exception), r"query|PII|regexp")

    def test_cutover_writeup_has_required_observations(self) -> None:
        from pathlib import Path

        text = (Path(__file__).resolve().parents[1] / "docs" / "CUTOVER.md").read_text(encoding="utf-8")
        assert_cutover_writeup(text)
        self.assertIn("CUTOVER_READY", text)
        self.assertIn("69.46.46.88", text)
        self.assertIn("69.46.46.117", text)

    def test_unsafe_unit_fails_closed(self) -> None:
        with self.assertRaises(ManifestError):
            assert_bridge_unit_safe("[Service]\nUser=root\nExecStart=/usr/bin/python3 -m fastapi\n")

    def test_firewall_opening_8765_fails(self) -> None:
        with self.assertRaises(ManifestError):
            assert_firewall_safe("policy drop\ntcp dport { 22, 80, 443, 8765 } accept\n")

    def test_caddy_unit_as_root_fails(self) -> None:
        with self.assertRaises(ManifestError):
            assert_caddy_unit_safe("[Service]\nUser=root\nAmbientCapabilities=CAP_NET_BIND_SERVICE\n")


if __name__ == "__main__":
    unittest.main()
