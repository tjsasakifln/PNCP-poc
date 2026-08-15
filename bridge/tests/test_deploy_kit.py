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
from bridge.generate import GENERATED_DIR, assert_terminator_safe, load_and_compile


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
