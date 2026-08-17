"""Drive the shipped preflight checks. No mock of the unit under test."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from bridge.generate import GENERATED_DIR, load_and_compile
from bridge.pins import (
    PINNED_COMMIT,
    PINNED_CONFIG_SHA256,
    PINNED_SHA256,
)
from bridge.policy import CompiledMap, RedirectRule
from bridge.preflight import (
    ACTIONS,
    DnsObservation,
    PreflightInputs,
    ProductionProbe,
    check_acme_email,
    check_bridge_public_ipv4,
    check_config_hash,
    check_destinations,
    check_webcfg_pin,
    redact_secrets,
    register_first_production_301,
    render_apply_commands,
    render_rollback_commands,
    run_local_blackbox,
    run_preflight,
)

ROOT = Path(__file__).resolve().parents[2]


def _compiled_with_target(target_url: str) -> CompiledMap:
    compiled = load_and_compile()
    first = compiled.redirects[0]
    mutated = RedirectRule(
        path=first.path,
        target_url=target_url,
        expected_canonical=target_url,
        family=first.family,
        owner=first.owner,
        persist=first.persist,
        expected_http=first.expected_http,
    )
    redirects = (mutated,) + compiled.redirects[1:]
    by_path = dict(compiled.by_path)
    by_path[mutated.path] = mutated
    return CompiledMap(
        manifesto_sha256=compiled.manifesto_sha256,
        config_sha256=compiled.config_sha256,
        persist=compiled.persist,
        redirects=redirects,
        by_path=by_path,
        holds=compiled.holds,
        default_status=compiled.default_status,
        observation_window_days=compiled.observation_window_days,
        owner=compiled.owner,
        removal_trigger=compiled.removal_trigger,
        expiry_review=compiled.expiry_review,
    )


class RequiredVarTests(unittest.TestCase):
    def test_missing_bridge_public_ipv4_is_blocked(self) -> None:
        result = check_bridge_public_ipv4(None)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.field, "BRIDGE_PUBLIC_IPV4")
        self.assertEqual(result.action, ACTIONS["BRIDGE_PUBLIC_IPV4"])
        self.assertIn("BRIDGE_PUBLIC_IPV4", result.action)

    def test_empty_and_private_ip_are_blocked(self) -> None:
        for value in ("", "   ", "127.0.0.1", "10.0.0.1", "192.168.0.5", "not-an-ip"):
            result = check_bridge_public_ipv4(value if value.strip() else None)
            self.assertEqual(result.status, "BLOCKED", value)
            self.assertEqual(result.field, "BRIDGE_PUBLIC_IPV4", value)

    def test_public_ipv4_passes(self) -> None:
        result = check_bridge_public_ipv4("1.1.1.1")
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.field, "BRIDGE_PUBLIC_IPV4")

    def test_missing_acme_email_is_blocked(self) -> None:
        result = check_acme_email(None)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.field, "SMARTLIC_ACME_EMAIL")
        self.assertEqual(result.action, ACTIONS["SMARTLIC_ACME_EMAIL"])

    def test_invalid_acme_email_is_blocked(self) -> None:
        for value in ("ops", "ops@", "@confenge.com.br", "ops @confenge.com.br"):
            result = check_acme_email(value)
            self.assertEqual(result.status, "BLOCKED", value)
            self.assertEqual(result.field, "SMARTLIC_ACME_EMAIL", value)


class PinAndHashTests(unittest.TestCase):
    def test_webcfg_pin_mismatch_is_blocked(self) -> None:
        result = check_webcfg_pin(
            manifesto_sha256="0" * 64,
            pinned_commit=PINNED_COMMIT,
        )
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.field, "WEB_CFG_PIN")
        self.assertIn(PINNED_SHA256, result.action)
        self.assertIn("0" * 64, result.detail)

    def test_webcfg_commit_mismatch_is_blocked(self) -> None:
        result = check_webcfg_pin(
            manifesto_sha256=PINNED_SHA256,
            pinned_commit="deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
        )
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.field, "WEB_CFG_COMMIT")
        self.assertIn(PINNED_COMMIT, result.action)

    def test_matching_pin_and_commit_pass(self) -> None:
        result = check_webcfg_pin(
            manifesto_sha256=PINNED_SHA256,
            pinned_commit=PINNED_COMMIT,
        )
        self.assertEqual(result.status, "PASS")

    def test_config_hash_mismatch_is_blocked(self) -> None:
        result = check_config_hash("ff" * 32)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.field, "BRIDGE_CONFIG_HASH")
        self.assertIn(PINNED_CONFIG_SHA256, result.action)
        self.assertIn("ff" * 32, result.detail)

    def test_pinned_config_hash_passes(self) -> None:
        compiled = load_and_compile()
        result = check_config_hash(compiled.config_sha256)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(compiled.config_sha256, PINNED_CONFIG_SHA256)


class DestinationTests(unittest.TestCase):
    def test_pinned_destinations_pass(self) -> None:
        compiled = load_and_compile()
        result = check_destinations(compiled)
        self.assertEqual(result.status, "PASS")

    def test_generic_home_destination_is_blocked(self) -> None:
        result = check_destinations(_compiled_with_target("https://confenge.com.br/"))
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.field, "WEB_CFG_DESTINATION")
        self.assertIn("confenge.com.br", result.action)

    def test_non_confenge_destination_is_blocked(self) -> None:
        result = check_destinations(_compiled_with_target("https://example.com/glossario"))
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.field, "WEB_CFG_DESTINATION")


class FirstProductionRefuseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compiled = load_and_compile()
        cls.ready = cls.compiled.redirects[0]

    def test_missing_probe_stays_unobserved_and_unwritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "first-production-301.json"
            record = register_first_production_301(None, self.compiled, write_path=dest)
            self.assertEqual(record.status, "UNOBSERVED")
            self.assertEqual(record.field, "first-production-301")
            self.assertFalse(record.written)
            self.assertFalse(dest.exists())

    def test_fixture_probe_is_blocked_and_unwritten(self) -> None:
        probe = ProductionProbe(
            host="smartlic.tech",
            path=self.ready.path,
            status=301,
            location=self.ready.target_url,
            config_hash=self.compiled.config_sha256,
            source="fixture",
        )
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "first-production-301.json"
            record = register_first_production_301(probe, self.compiled, write_path=dest)
            self.assertEqual(record.status, "BLOCKED")
            self.assertEqual(record.field, "first-production-301")
            self.assertIn("fixture", record.detail)
            self.assertFalse(record.written)
            self.assertFalse(dest.exists())

    def test_mock_and_loopback_probes_are_blocked(self) -> None:
        for source, host in (("mock", "smartlic.tech"), ("loopback", "127.0.0.1")):
            probe = ProductionProbe(
                host=host,
                path=self.ready.path,
                status=301,
                location=self.ready.target_url,
                config_hash=self.compiled.config_sha256,
                source=source,
            )
            record = register_first_production_301(probe, self.compiled)
            self.assertEqual(record.status, "BLOCKED", (source, host))
            self.assertFalse(record.written)

    def test_wrong_hash_or_location_is_blocked_even_if_labeled_live(self) -> None:
        probe = ProductionProbe(
            host="smartlic.tech",
            path=self.ready.path,
            status=301,
            location="https://confenge.com.br/",
            config_hash=self.compiled.config_sha256,
            source="live",
        )
        record = register_first_production_301(probe, self.compiled)
        self.assertEqual(record.status, "BLOCKED")
        self.assertEqual(record.field, "WEB_CFG_DESTINATION")
        probe2 = ProductionProbe(
            host="smartlic.tech",
            path=self.ready.path,
            status=301,
            location=self.ready.target_url,
            config_hash="00" * 32,
            source="live",
        )
        record2 = register_first_production_301(probe2, self.compiled)
        self.assertEqual(record2.status, "BLOCKED")
        self.assertEqual(record2.field, "BRIDGE_CONFIG_HASH")


class BlackboxRollbackTests(unittest.TestCase):
    def test_shipped_blackbox_and_rollback_share_manifesto_pin(self) -> None:
        compiled = load_and_compile()
        with tempfile.TemporaryDirectory() as tmp:
            result = run_local_blackbox(compiled, Path(tmp))
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["ready_status"], 301)
        self.assertEqual(result["ready_location"], compiled.redirects[0].target_url)
        self.assertEqual(result["slash_status"], 410)
        self.assertEqual(result["login_status"], 410)
        self.assertEqual(result["hold_status"], 410)
        self.assertEqual(result["config_sha256"], compiled.config_sha256)
        self.assertEqual(result["manifesto_sha256"], PINNED_SHA256)
        rollback = result["rollback"]
        self.assertEqual(rollback["status"], "PASS")
        self.assertEqual(rollback["from_config_sha256"], compiled.config_sha256)
        self.assertEqual(rollback["manifesto_sha256"], PINNED_SHA256)
        self.assertEqual(rollback["redirects"], 0)
        self.assertEqual(rollback["ready_path_status"], 410)
        self.assertIsNone(rollback["ready_path_location"])
        self.assertNotEqual(rollback["rollback_config_sha256"], compiled.config_sha256)


class RunPreflightMissingInputsTests(unittest.TestCase):
    def test_run_preflight_names_first_missing_field(self) -> None:
        compiled = load_and_compile()
        caddy = (GENERATED_DIR / "Caddyfile").read_text(encoding="utf-8")
        report = run_preflight(
            PreflightInputs(
                bridge_public_ipv4=None,
                smartlic_acme_email=None,
                cf_api_token=None,
                cf_zone_id=None,
                compiled=compiled,
                compile_error=None,
                caddy_text=caddy,
                dns_apex=DnsObservation("smartlic.tech", ("69.46.46.88",)),
                dns_www=DnsObservation("www.smartlic.tech", ("69.46.46.117",)),
                skip_blackbox=True,
                run_live_dest_probe=False,
            )
        )
        self.assertEqual(report.status, "BLOCKED")
        self.assertEqual(report.field, "BRIDGE_PUBLIC_IPV4")
        self.assertEqual(report.action, ACTIONS["BRIDGE_PUBLIC_IPV4"])
        self.assertFalse(report.dns_mutated)
        self.assertFalse(report.tls_mutated)
        self.assertEqual(report.first_production_301["status"], "UNOBSERVED")
        fields = [item.field for item in report.checks if item.status == "BLOCKED"]
        self.assertIn("BRIDGE_PUBLIC_IPV4", fields)
        self.assertIn("SMARTLIC_ACME_EMAIL", fields)
        self.assertIn("CF_API_TOKEN", fields)
        self.assertIn("CF_ZONE_ID", fields)


class CliMissingInputsTests(unittest.TestCase):
    def _run_cli(self, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        for key in ("BRIDGE_PUBLIC_IPV4", "SMARTLIC_ACME_EMAIL", "CF_API_TOKEN", "CF_ZONE_ID"):
            env.pop(key, None)
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "bridge.preflight",
                "--skip-live",
                "--skip-blackbox",
            ],
            cwd=str(ROOT),
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_cli_twice_is_blocked_on_missing_ipv4(self) -> None:
        first = self._run_cli()
        second = self._run_cli()
        self.assertNotEqual(first.returncode, 0)
        self.assertNotEqual(second.returncode, 0)
        for proc in (first, second):
            self.assertIn("PREFLIGHT_BLOCKED", proc.stdout)
            self.assertIn("field=BRIDGE_PUBLIC_IPV4", proc.stdout)
            self.assertIn(ACTIONS["BRIDGE_PUBLIC_IPV4"], proc.stdout)
            self.assertIn('"status": "BLOCKED"', proc.stdout)
            self.assertIn("python3 -m bridge.generate --rollback", proc.stdout)
            self.assertIn("api.cloudflare.com", proc.stdout)
            self.assertIn("Authorization: Bearer $CF_API_TOKEN", proc.stdout)
            self.assertNotIn("Authorization=<redacted>", proc.stdout)
            self.assertIn('"name": "cf_api_token"', proc.stdout)
            self.assertNotIn("<redacted-token>", proc.stdout)
            self.assertNotIn("BEGIN PRIVATE", proc.stdout + proc.stderr)
        self.assertEqual(
            [line for line in first.stdout.splitlines() if line.startswith("PREFLIGHT_")][0],
            [line for line in second.stdout.splitlines() if line.startswith("PREFLIGHT_")][0],
        )

    def test_cli_does_not_print_token_value(self) -> None:
        secret = "super-secret-cf-token-value-xyz"
        proc = self._run_cli({"CF_API_TOKEN": secret})
        blob = proc.stdout + proc.stderr
        self.assertNotIn(secret, blob)
        self.assertIn("PREFLIGHT_BLOCKED", proc.stdout)
        self.assertIn("Authorization: Bearer $CF_API_TOKEN", proc.stdout)
        self.assertNotIn("Authorization=<redacted>", proc.stdout)
        self.assertIn('"name": "cf_api_token"', proc.stdout)
        self.assertNotIn("BEGIN PRIVATE", blob)


class CommandRenderTests(unittest.TestCase):
    def test_apply_and_rollback_are_text_only_with_env_refs(self) -> None:
        apply_cmds = render_apply_commands(None)
        rollback_cmds = render_rollback_commands()
        blob = "\n".join(apply_cmds + rollback_cmds)
        self.assertIn("$CF_API_TOKEN", blob)
        self.assertIn("$BRIDGE_PUBLIC_IPV4", blob)
        self.assertIn("python3 -m bridge.generate --rollback", blob)
        self.assertIn("69.46.46.88", blob)
        self.assertIn("app.smartlic.tech.", blob)
        self.assertNotRegex(blob, r"CF_API_TOKEN=[A-Za-z0-9_\-]{8,}")

    def test_preflight_source_never_executes_cloudflare_write(self) -> None:
        text = (ROOT / "bridge" / "preflight.py").read_text(encoding="utf-8")
        self.assertNotIn("urlopen", text)
        self.assertNotIn("requests.", text)
        self.assertIn("api.cloudflare.com", text)
        self.assertNotIn('Request("https://api.cloudflare.com', text.replace(" ", ""))


class RedactTests(unittest.TestCase):
    def test_redact_secrets_strips_token_assignment_and_pem(self) -> None:
        raw = "CF_API_TOKEN=abcd1234\n-----BEGIN PRIVATE KEY-----\nMII\n"
        out = redact_secrets(raw)
        self.assertNotIn("abcd1234", out)
        self.assertNotIn("BEGIN PRIVATE KEY", out)
        self.assertIn("<redacted>", out)

    def test_redact_keeps_env_ref_apply_templates_and_check_names(self) -> None:
        raw = (
            'curl -H "Authorization: Bearer $CF_API_TOKEN"\n'
            "# export CF_API_TOKEN=... CF_ZONE_ID=...\n"
            '"name": "cf_api_token"\n'
            "Authorization: Bearer leaked-literal-token\n"
            "sk_live_abcdefghijklmnop\n"
        )
        out = redact_secrets(raw)
        self.assertIn("Authorization: Bearer $CF_API_TOKEN", out)
        self.assertIn("# export CF_API_TOKEN=... CF_ZONE_ID=...", out)
        self.assertIn('"name": "cf_api_token"', out)
        self.assertNotIn("leaked-literal-token", out)
        self.assertNotIn("sk_live_abcdefghijklmnop", out)
        self.assertIn("Authorization: Bearer <redacted>", out)


class DocsGateTests(unittest.TestCase):
    def test_cutover_docs_name_preflight_as_hard_gate(self) -> None:
        cutover = (ROOT / "bridge" / "docs" / "CUTOVER.md").read_text(encoding="utf-8")
        readiness = (ROOT / "bridge" / "docs" / "CUTOVER_READINESS.md").read_text(encoding="utf-8")
        readme = (ROOT / "bridge" / "README.md").read_text(encoding="utf-8")
        self.assertIn("python3 -m bridge.preflight", cutover)
        self.assertIn("python3 -m bridge.preflight", readiness)
        self.assertIn("python3 -m bridge.preflight", readme)
        self.assertIn("hard gate", cutover.lower())
        self.assertNotIn("first production 301 observed", readiness.lower())


if __name__ == "__main__":
    unittest.main()
