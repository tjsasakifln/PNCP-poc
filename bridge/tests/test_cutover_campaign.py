"""Drive shipped generate/policy/serve and bind campaign artifacts to pins."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bridge.cutover_campaign import (
    CAMPAIGN_NAME,
    DEFAULT_CAMPAIGN_DIR,
    EXPECTED_PERSIST,
    FAIL_CLOSED_PATHS,
    HOLD_SAMPLE,
    READY_CANARY_PATH,
    READY_CANARY_TARGET,
    assert_pins,
    canary_serve_twice,
    probe_ready_targets_full,
    run_generate_check,
    try_caddy_canary,
    write_campaign,
)
from bridge.generate import load_and_compile, main as generate_main, probe_targets
from bridge.pins import (
    PINNED_COMMIT,
    PINNED_CONFIG_SHA256,
    PINNED_HOLD_COUNT,
    PINNED_REDIRECT_COUNT,
    PINNED_RETIRE_COUNT,
    PINNED_SCHEMA,
    PINNED_SHA256,
)
from bridge.policy import filter_query, resolve


class CutoverCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compiled = load_and_compile()

    def test_generate_check_and_pins_match_constants(self) -> None:
        rc = generate_main(["--check"])
        self.assertEqual(rc, 0)
        result = run_generate_check()
        self.assertEqual(result["status"], "GENERATE_OK")
        pins = assert_pins(self.compiled)
        self.assertEqual(pins["manifesto_sha256"]["got"], PINNED_SHA256)
        self.assertEqual(pins["config_sha256"]["got"], PINNED_CONFIG_SHA256)
        self.assertEqual(pins["pinned_commit"]["got"], PINNED_COMMIT)
        self.assertEqual(pins["schema"]["got"], PINNED_SCHEMA)
        self.assertEqual(len(self.compiled.redirects), PINNED_REDIRECT_COUNT)
        self.assertEqual(len(self.compiled.holds), PINNED_HOLD_COUNT)
        self.assertEqual(PINNED_RETIRE_COUNT, 1190)
        self.assertEqual(tuple(self.compiled.persist), EXPECTED_PERSIST)

    def test_policy_resolve_is_the_request_evaluator(self) -> None:
        for rule in self.compiled.redirects:
            decision = resolve(self.compiled, rule.path, "", "smartlic.tech")
            self.assertEqual(decision.status, 301, rule.path)
            self.assertEqual(decision.location, rule.target_url, rule.path)
            self.assertEqual(decision.hops, 1, rule.path)
        payment = resolve(
            self.compiled,
            "/blog/orgaos-risco-atraso-pagamento-licitacao",
            "",
            "smartlic.tech",
        )
        self.assertEqual(
            payment.location,
            "https://confenge.com.br/conteudos/atraso-pagamento-contrato-publico-suspender/",
        )
        self.assertNotIn("/atrasos-prorrogacao-obras-publicas/", payment.location or "")
        home = resolve(self.compiled, "/", "", "smartlic.tech")
        self.assertEqual(home.status, 410)
        self.assertIsNone(home.location)
        hold = resolve(self.compiled, HOLD_SAMPLE, "", "smartlic.tech")
        self.assertEqual(hold.status, 410)
        self.assertIsNone(hold.location)
        query = "utm_source=gsc&jornada=obra&email=ada@example.com&token=secret"
        ready = resolve(self.compiled, READY_CANARY_PATH, query, "www.smartlic.tech")
        self.assertEqual(ready.status, 301)
        self.assertTrue((ready.location or "").startswith(READY_CANARY_TARGET))
        self.assertIn("utm_source=gsc", ready.location or "")
        self.assertIn("jornada=obra", ready.location or "")
        self.assertNotIn("email=", ready.location or "")
        self.assertNotIn("token=", ready.location or "")
        self.assertNotIn("email=", filter_query(query, self.compiled.persist))

    def test_serve_canary_twice_and_caddy_fallback(self) -> None:
        canary = canary_serve_twice(self.compiled)
        self.assertEqual(canary["status"], "PASS")
        self.assertEqual(len(canary["launches"]), 2)
        for launch in canary["launches"]:
            self.assertIn("SERVE_OK", launch["banner"])
            self.assertIn(PINNED_SHA256, launch["banner"])
            self.assertIn(PINNED_CONFIG_SHA256, launch["banner"])
            self.assertEqual(launch["errors"], [])
        caddy = try_caddy_canary()
        self.assertIn(caddy["status"], {"CADDY_ABSENT", "VALIDATED", "CADDY_VALIDATE_FAILED"})

    def test_probe_targets_get_head_all_ready_rows(self) -> None:
        probe_targets(self.compiled)
        report = probe_ready_targets_full(self.compiled)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["count"], PINNED_REDIRECT_COUNT)
        self.assertEqual(len(report["rows"]), PINNED_REDIRECT_COUNT)
        for row in report["rows"]:
            self.assertTrue(row["useful_final_status"], row["path"])
            self.assertTrue(row["host_ok"], row["path"])
            self.assertFalse(row["chain"], row["path"])
            self.assertFalse(row["soft_404"], row["path"])
            self.assertTrue(row["canonical_ok"], row["path"])
            self.assertTrue(row["robots_ok"], row["path"])
            self.assertEqual(row["get"]["host"], "confenge.com.br")

    def test_committed_campaign_artifacts_bind_to_pins(self) -> None:
        self.assertTrue(DEFAULT_CAMPAIGN_DIR.is_dir(), DEFAULT_CAMPAIGN_DIR)
        required = (
            "PRE_FLIGHT.json",
            "TARGET_VERIFICATION.json",
            "CANARY_LOCAL.txt",
            "CUTOVER_MANIFEST.json",
            "ROLLBACK.md",
            "REMOVAL_CRITERIA.md",
            "EVIDENCE.md",
            "FOUNDER_ACTION_REQUIRED_CUTOVER.txt",
        )
        for name in required:
            path = DEFAULT_CAMPAIGN_DIR / name
            self.assertTrue(path.is_file(), name)
            text = path.read_text(encoding="utf-8")
            self.assertTrue(
                PINNED_SHA256 in text or PINNED_CONFIG_SHA256 in text,
                f"{name} must bind to a pinned hash",
            )
        for name in (
            "PRE_FLIGHT.json",
            "TARGET_VERIFICATION.json",
            "CUTOVER_MANIFEST.json",
            "EVIDENCE.md",
            "FOUNDER_ACTION_REQUIRED_CUTOVER.txt",
            "ROLLBACK.md",
            "REMOVAL_CRITERIA.md",
        ):
            text = (DEFAULT_CAMPAIGN_DIR / name).read_text(encoding="utf-8")
            self.assertIn(PINNED_SHA256, text, name)
            self.assertIn(PINNED_CONFIG_SHA256, text, name)
        canary_text = (DEFAULT_CAMPAIGN_DIR / "CANARY_LOCAL.txt").read_text(encoding="utf-8")
        self.assertIn(PINNED_SHA256, canary_text)
        self.assertIn(PINNED_CONFIG_SHA256, canary_text)
        manifest = json.loads((DEFAULT_CAMPAIGN_DIR / "CUTOVER_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["campaign"], CAMPAIGN_NAME)
        self.assertEqual(manifest["verdict"], "CUTOVER READY")
        self.assertEqual(manifest["manifesto_sha256"], PINNED_SHA256)
        self.assertEqual(manifest["config_sha256"], PINNED_CONFIG_SHA256)
        self.assertEqual(manifest["redirects"], PINNED_REDIRECT_COUNT)
        self.assertFalse(manifest["live_apply"])
        founder = (DEFAULT_CAMPAIGN_DIR / "FOUNDER_ACTION_REQUIRED_CUTOVER.txt").read_text(encoding="utf-8")
        self.assertIn("type=A  name=smartlic.tech      value=$BRIDGE_PUBLIC_IPV4  ttl=60", founder)
        self.assertIn("type=A  name=www.smartlic.tech  value=$BRIDGE_PUBLIC_IPV4  ttl=300", founder)
        self.assertIn("value=69.46.46.88", founder)
        self.assertIn("value=app.smartlic.tech.", founder)
        self.assertIn(READY_CANARY_TARGET, founder)
        self.assertIn("curl -sI https://smartlic.tech/login", founder)
        self.assertNotIn("configure DNS", founder.lower().replace("dns apply", "apply"))
        self.assertIn("python3 -m bridge.generate --check", founder)
        self.assertIn("systemctl enable --now smartlic-bridge caddy-bridge", founder)
        targets = json.loads((DEFAULT_CAMPAIGN_DIR / "TARGET_VERIFICATION.json").read_text(encoding="utf-8"))
        self.assertEqual(targets["status"], "PASS")
        self.assertEqual(targets["count"], PINNED_REDIRECT_COUNT)
        canary = (DEFAULT_CAMPAIGN_DIR / "CANARY_LOCAL.txt").read_text(encoding="utf-8")
        self.assertIn("SERVE_OK", canary)
        self.assertIn(READY_CANARY_PATH, canary)
        for path in FAIL_CLOSED_PATHS:
            self.assertIn(path, canary)

    def test_write_campaign_tmp_hashes_equal_pins(self) -> None:
        pins = assert_pins(self.compiled)
        with tempfile.TemporaryDirectory() as tmp:
            written = write_campaign(
                Path(tmp),
                self.compiled,
                generate={"status": "GENERATE_OK"},
                pins=pins,
                targets={"status": "PASS", "count": PINNED_REDIRECT_COUNT, "rows": []},
                canary={"status": "PASS", "entry": "python3 -m bridge.serve", "launches": []},
                caddy={"status": "CADDY_ABSENT", "detail": "test"},
                dns={"credentials_present": {}},
                preflight={
                    "manifesto_sha256": PINNED_SHA256,
                    "config_sha256": PINNED_CONFIG_SHA256,
                },
            )
            manifest = json.loads((Path(tmp) / "CUTOVER_MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["manifesto_sha256"], PINNED_SHA256)
            self.assertEqual(manifest["config_sha256"], PINNED_CONFIG_SHA256)
            self.assertEqual(manifest["verdict"], "CUTOVER READY")
            self.assertIn("CUTOVER_MANIFEST.json", written)


if __name__ == "__main__":
    unittest.main()
