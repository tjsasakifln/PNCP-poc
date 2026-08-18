"""Drive shipped apply / resolve / serve / start_observation_window fail-closed."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bridge.apply import (
    FORBIDDEN_DNS_NAMES,
    SINGLE_HUMAN_ACTION,
    apply_dns,
    assert_plan_safe,
    assert_runtime_commands_safe,
    credential_presence,
    dns_plan,
    load_authorized_env,
    main as apply_main,
    missing_credentials,
    rollback_dns_plan,
    run_apply,
    runtime_install_commands,
)
from bridge.errors import ManifestError
from bridge.generate import load_and_compile
from bridge.observe import evaluate_signals
from bridge.pins import PINNED_CONFIG_SHA256, PINNED_SHA256
from bridge.policy import resolve
from bridge.preflight import ProductionProbe, start_observation_window

ROOT = Path(__file__).resolve().parents[2]


class AuthorizedEnvTests(unittest.TestCase):
    def test_empty_env_and_missing_file_are_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            values = load_authorized_env({}, Path(tmp) / "missing")
        self.assertEqual(values, {})
        self.assertEqual(
            missing_credentials(values),
            (
                "BRIDGE_PUBLIC_IPV4",
                "SMARTLIC_ACME_EMAIL",
                "CF_API_TOKEN",
                "CF_ZONE_ID",
            ),
        )
        self.assertFalse(any(credential_presence(values).values()))

    def test_env_file_and_process_env_load_without_leaking_other_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "env"
            path.write_text(
                "BRIDGE_PUBLIC_IPV4=1.1.1.1\n"
                "SMARTLIC_ACME_EMAIL=ops@example.com\n"
                "STRIPE_SECRET=sk_live_should_be_ignored\n",
                encoding="utf-8",
            )
            values = load_authorized_env(
                {"CF_API_TOKEN": "cf-dummy", "CF_ZONE_ID": "zone-dummy"},
                path,
            )
        self.assertEqual(set(values), set(credential_presence(values)))
        self.assertTrue(all(credential_presence(values).values()))
        self.assertNotIn("STRIPE_SECRET", values)
        self.assertEqual(values["BRIDGE_PUBLIC_IPV4"], "1.1.1.1")


class DnsPlanSafetyTests(unittest.TestCase):
    def test_plan_is_only_apex_and_www(self) -> None:
        plan = dns_plan("1.1.1.1")
        assert_plan_safe(plan)
        names = {item.name for item in plan}
        self.assertEqual(names, {"smartlic.tech", "www.smartlic.tech"})
        self.assertTrue(FORBIDDEN_DNS_NAMES.isdisjoint(names))
        self.assertTrue(all(item.type in {"A", "CNAME"} for item in plan))
        self.assertTrue(all(item.proxied is False for item in plan))

    def test_private_ip_is_refused(self) -> None:
        with self.assertRaises(ManifestError):
            dns_plan("127.0.0.1")

    def test_api_name_cannot_be_forced_into_plan(self) -> None:
        plan = list(dns_plan("1.1.1.1"))
        from bridge.apply import DnsMutation

        plan.append(DnsMutation(op="upsert", type="A", name="api.smartlic.tech", content="1.1.1.1", ttl=60))
        with self.assertRaises(ManifestError) as ctx:
            assert_plan_safe(plan)
        self.assertIn("api.smartlic.tech", str(ctx.exception))

    def test_rollback_plan_does_not_touch_api(self) -> None:
        plan = rollback_dns_plan()
        assert_plan_safe(plan)
        self.assertTrue(all(item.name in {"smartlic.tech", "www.smartlic.tech"} for item in plan))


class ApplyDnsFailClosedTests(unittest.TestCase):
    def test_missing_secrets_do_not_call_transport(self) -> None:
        calls: list[tuple[str, str]] = []

        def transport(method: str, url: str, headers, body):
            calls.append((method, url))
            raise AssertionError("transport must not run without secrets")

        result = apply_dns(
            dns_plan("1.1.1.1"),
            token=None,
            zone_id=None,
            transport=transport,
        )
        self.assertEqual(result["status"], "BLOCKED_SINGLE_EXTERNAL_ACTION")
        self.assertFalse(result["applied"])
        self.assertEqual(result["mutations"], 0)
        self.assertEqual(calls, [])
        self.assertEqual(result["action"], SINGLE_HUMAN_ACTION)

    def test_dummy_secrets_never_write_api_hostname(self) -> None:
        calls: list[tuple[str, str]] = []

        def transport(method: str, url: str, headers, body):
            calls.append((method, url))
            self.assertNotIn("api.smartlic.tech", url)
            if body:
                self.assertNotIn(b"api.smartlic.tech", body)
            if method == "GET":
                return {"success": True, "result": []}
            return {"success": True, "result": {"id": "rec"}}

        result = apply_dns(
            dns_plan("1.1.1.1"),
            token="dummy-token",
            zone_id="dummy-zone",
            transport=transport,
        )
        self.assertTrue(result["applied"])
        self.assertGreater(len(calls), 0)
        joined = " ".join(url for _method, url in calls)
        self.assertNotIn("api.smartlic.tech", joined)
        self.assertNotIn("app.smartlic.tech", joined)

    def test_default_transport_is_not_attached_implicitly(self) -> None:
        with self.assertRaises(ManifestError):
            apply_dns(
                dns_plan("1.1.1.1"),
                token="dummy-token",
                zone_id="dummy-zone",
            )


class RuntimePlanTests(unittest.TestCase):
    def test_runtime_commands_are_bridge_only(self) -> None:
        commands = runtime_install_commands()
        blob = "\n".join(commands).lower()
        self.assertIn("python3 -m bridge.serve --host 127.0.0.1 --port 8765", blob)
        self.assertIn("caddy-bridge", blob)
        for token in ("fastapi", "uvicorn", "next.js", "redis", "railway", "supabase"):
            self.assertNotIn(token, blob)

    def test_product_token_is_rejected(self) -> None:
        with self.assertRaises(ManifestError):
            assert_runtime_commands_safe(["uvicorn backend.main:app"])


class ObservationWindowStartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compiled = load_and_compile()
        cls.ready = cls.compiled.redirects[0]

    def test_loopback_and_fixture_cannot_start_window(self) -> None:
        decision = resolve(self.compiled, self.ready.path, "", "smartlic.tech")
        self.assertEqual(decision.status, 301)
        self.assertEqual(decision.location, self.ready.target_url)
        for source, host in (("loopback", "127.0.0.1"), ("fixture", "smartlic.tech"), ("mock", "www.smartlic.tech")):
            probe = ProductionProbe(
                host=host,
                path=self.ready.path,
                status=301,
                location=self.ready.target_url,
                config_hash=PINNED_CONFIG_SHA256,
                source=source,
                captured_at="2026-08-18T12:00:00Z",
            )
            with tempfile.TemporaryDirectory() as tmp:
                dest = Path(tmp) / "observation.json"
                payload = start_observation_window(probe, self.compiled, write_path=dest)
            self.assertIsNone(payload["observation_started_at"], source)
            self.assertIsNone(payload["observation_end"], source)
            self.assertNotEqual(payload["first_production_301"], "OBSERVED")
            self.assertFalse(payload["written"])
            self.assertFalse(dest.exists())
            signals = evaluate_signals(
                {"config_sha256": PINNED_CONFIG_SHA256, "counts": {}},
                production_first_301=payload,
            )
            self.assertFalse(signals["window_started"])

    def test_production_shaped_probe_is_only_start(self) -> None:
        probe = ProductionProbe(
            host="smartlic.tech",
            path=self.ready.path,
            status=301,
            location=self.ready.target_url,
            config_hash=PINNED_CONFIG_SHA256,
            source="live",
            captured_at="2026-08-18T14:00:00Z",
        )
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "observation.json"
            payload = start_observation_window(probe, self.compiled, write_path=dest)
            written = json.loads(dest.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "OBSERVED")
        self.assertEqual(payload["first_production_301"], "OBSERVED")
        self.assertEqual(payload["observation_started_at"], "2026-08-18T14:00:00Z")
        self.assertEqual(payload["observation_end"], "2026-09-15T14:00:00Z")
        self.assertEqual(payload["config_sha256"], PINNED_CONFIG_SHA256)
        self.assertEqual(payload["manifesto_sha256"], PINNED_SHA256)
        self.assertEqual(payload["location"], self.ready.target_url)
        self.assertTrue(payload["written"])
        self.assertEqual(written["observation_started_at"], "2026-08-18T14:00:00Z")
        signals = evaluate_signals(
            {"config_sha256": PINNED_CONFIG_SHA256, "counts": {}, "target_health": {"status": "OK"}},
            production_first_301=payload,
        )
        self.assertTrue(signals["window_started"])
        self.assertEqual(signals["first_301_scope"], "production")

    def test_wrong_hash_or_home_location_cannot_start_window(self) -> None:
        bad_hash = ProductionProbe(
            host="smartlic.tech",
            path=self.ready.path,
            status=301,
            location=self.ready.target_url,
            config_hash="0" * 64,
            source="live",
            captured_at="2026-08-18T14:00:00Z",
        )
        home = ProductionProbe(
            host="smartlic.tech",
            path=self.ready.path,
            status=301,
            location="https://confenge.com.br/",
            config_hash=PINNED_CONFIG_SHA256,
            source="live",
            captured_at="2026-08-18T14:00:00Z",
        )
        for probe in (bad_hash, home):
            payload = start_observation_window(probe, self.compiled)
            self.assertIsNone(payload["observation_started_at"])
            self.assertNotEqual(payload["first_production_301"], "OBSERVED")


class RunApplyCliTests(unittest.TestCase):
    def test_run_apply_without_secrets_is_blocked_and_secretless(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = run_apply(environ={}, env_file=Path(tmp) / "missing")
        self.assertEqual(payload["status"], "BLOCKED_SINGLE_EXTERNAL_ACTION")
        self.assertFalse(payload["applied"])
        self.assertFalse(any(payload["credential_presence"].values()))
        self.assertEqual(payload["action"], SINGLE_HUMAN_ACTION)
        self.assertEqual(payload["manifesto_sha256"], PINNED_SHA256)
        self.assertEqual(payload["config_sha256"], PINNED_CONFIG_SHA256)
        blob = json.dumps(payload)
        self.assertNotIn("Bearer ", blob)
        self.assertNotRegex(blob, r"CF_API_TOKEN=[A-Za-z0-9_\-]{8,}")
        for token in ("fastapi", "uvicorn", "railway", "redis"):
            self.assertNotIn(token, blob.lower())

    def test_apply_main_does_not_open_network_without_secrets(self) -> None:
        def boom(*_args, **_kwargs):
            raise AssertionError("urlopen must not run")

        with patch("urllib.request.urlopen", side_effect=boom):
            rc = apply_main(["--env-file", "/no/such/smartlic-bridge.env", "--json-only"])
        self.assertEqual(rc, 2)

    def test_loopback_probe_via_run_apply_does_not_start_window(self) -> None:
        compiled = load_and_compile()
        ready = compiled.redirects[0]
        probe = ProductionProbe(
            host="127.0.0.1",
            path=ready.path,
            status=301,
            location=ready.target_url,
            config_hash=PINNED_CONFIG_SHA256,
            source="loopback",
            captured_at="2026-08-18T14:00:00Z",
        )
        with tempfile.TemporaryDirectory() as tmp:
            payload = run_apply(
                environ={},
                env_file=Path(tmp) / "missing",
                first_production_probe=probe,
                observation_path=Path(tmp) / "obs.json",
            )
        self.assertIsNone(payload["observation"]["observation_started_at"])
        self.assertNotEqual(payload["observation"]["first_production_301"], "OBSERVED")


class MonitorDoesNotStartWindowTests(unittest.TestCase):
    def test_monitor_source_cannot_register_first_301(self) -> None:
        text = (Path(__file__).resolve().parents[1] / "monitor.py").read_text(encoding="utf-8")
        self.assertNotIn("start_observation_window", text)
        self.assertNotIn("register_first_production_301", text)
        self.assertIn("Does not start observation_started_at", text)


class ServeStillResolvesPinnedMapTests(unittest.TestCase):
    def test_shipped_serve_plus_resolve_match_pin(self) -> None:
        compiled = load_and_compile()
        ready = compiled.redirects[0]
        decision = resolve(compiled, ready.path, "email=a@b.c&utm_source=x", "smartlic.tech")
        self.assertEqual(decision.status, 301)
        self.assertEqual(decision.location, ready.target_url + "?utm_source=x")
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "bridge.apply",
                "--env-file",
                "/no/such/smartlic-bridge.env",
                "--json-only",
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
            env={k: v for k, v in os.environ.items() if k not in {
                "BRIDGE_PUBLIC_IPV4",
                "SMARTLIC_ACME_EMAIL",
                "CF_API_TOKEN",
                "CF_ZONE_ID",
            }},
        )
        self.assertEqual(proc.returncode, 2)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "BLOCKED_SINGLE_EXTERNAL_ACTION")
        self.assertIn("CF_API_TOKEN", payload["missing"])
