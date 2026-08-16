"""Drive the shipped window recorder, serve emit path, and export CLI."""

from __future__ import annotations

import http.client
import json
import re
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

from bridge.generate import GENERATED_DIR, load_and_compile, render_caddyfile
from bridge.observe import (
    EXPORT_SCHEMA,
    RETENTION_DAYS,
    WindowRecorder,
    assert_no_pii,
    classify_path,
    evaluate_signals,
    main as observe_main,
    make_record,
    redact_query,
    serialize_record,
    target_health_from_results,
)
from bridge.pins import PINNED_SHA256
from bridge.policy import Decision, resolve

ROOT = Path(__file__).resolve().parents[2]
FIXED = datetime(2026, 8, 16, 20, 0, 0, tzinfo=timezone.utc)
PII_QUERY = "email=ada@example.com&cnpj=00000000000191&token=secret"
PII_VALUES = ("ada@example.com", "00000000000191", "secret", "email=", "cnpj=", "token=")
RAW_IP = "203.0.113.50"
RAW_IPV6 = "2001:db8::50"
FULL_UA = "Mozilla/5.0 (X11; Linux x86_64) Hostile/1.0"


def _forbidden_in(blob: str) -> list[str]:
    hits = [item for item in (*PII_VALUES, RAW_IP, RAW_IPV6, FULL_UA) if item in blob]
    if re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", blob):
        hits.append("ipv4-pattern")
    if "Mozilla/" in blob or "User-Agent" in blob:
        hits.append("user-agent")
    return hits


class RecordAndRedactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compiled = load_and_compile()
        cls.ready = cls.compiled.redirects[0]
        cls.hold = cls.compiled.holds[0]

    def _recorder(self) -> WindowRecorder:
        return WindowRecorder(
            self.compiled.manifesto_sha256,
            self.compiled.config_sha256,
            clock=lambda: FIXED,
        )

    def test_query_values_are_dropped(self) -> None:
        self.assertEqual(redact_query(PII_QUERY), "")
        self.assertEqual(redact_query("utm_source=gsc"), "")

    def test_ready_hold_login_unmapped_and_pii_query_do_not_change_resolve(self) -> None:
        rec = self._recorder()
        cases = [
            (self.ready.path, "", "smartlic.tech"),
            (self.hold, "", "smartlic.tech"),
            ("/login", "", "smartlic.tech"),
            ("/not-mapped-2115", "", "smartlic.tech"),
            (self.ready.path, PII_QUERY, "smartlic.tech"),
        ]
        records = []
        for path, query, host in cases:
            decision = resolve(self.compiled, path, query, host)
            before = (decision.status, decision.location, decision.family, decision.hops)
            record = rec.record(
                decision,
                path=path,
                latency_ms=1.25,
                query=query,
                remote_ip=RAW_IP,
                user_agent=FULL_UA,
            )
            after = resolve(self.compiled, path, query, host)
            self.assertEqual((after.status, after.location, after.family, after.hops), before)
            self.assertEqual(record["status"], decision.status)
            self.assertEqual(record["action"], decision.family)
            records.append((decision, record, path, query))

        ready_decision, ready_record, _path, _q = records[0]
        self.assertEqual(ready_decision.status, 301)
        self.assertEqual(ready_decision.location, self.ready.target_url)
        self.assertEqual(ready_record["path_class"], "ready")
        self.assertEqual(ready_record["critical_url"], self.ready.path)

        hold_decision, hold_record, _path, _q = records[1]
        self.assertEqual(hold_decision.status, 410)
        self.assertIsNone(hold_decision.location)
        self.assertEqual(hold_record["path_class"], "hold")

        login_decision, login_record, _path, _q = records[2]
        self.assertEqual(login_decision.status, 410)
        self.assertIsNone(login_decision.location)
        self.assertEqual(login_record["path_class"], "login")

        unmapped_decision, unmapped_record, unmapped_path, _q = records[3]
        self.assertEqual(unmapped_decision.status, 410)
        self.assertIsNone(unmapped_decision.location)
        self.assertEqual(unmapped_record["path_class"], "unmapped")
        self.assertNotIn("critical_url", unmapped_record)
        self.assertNotIn(unmapped_path, serialize_record(unmapped_record))

        pii_decision, pii_record, _path, _q = records[4]
        self.assertEqual(pii_decision.status, 301)
        self.assertIsNotNone(pii_decision.location)
        self.assertNotIn("email=", pii_decision.location)
        self.assertNotIn("cnpj=", pii_decision.location)
        self.assertNotIn("token=", pii_decision.location)

        for _decision, record, _path, _query in records:
            for key in (
                "ts",
                "manifesto_sha256",
                "config_sha256",
                "action",
                "path_class",
                "status",
                "latency_ms",
            ):
                self.assertIn(key, record)
            self.assertEqual(record["manifesto_sha256"], self.compiled.manifesto_sha256)
            self.assertEqual(record["config_sha256"], self.compiled.config_sha256)
            self.assertEqual(record["ts"], "2026-08-16T20:00:00.000Z")
            self.assertEqual(record["latency_ms"], 1.25)
            blob = serialize_record(record)
            self.assertEqual(_forbidden_in(blob), [])
            assert_no_pii(blob)

    def test_assert_no_pii_rejects_identity_blobs(self) -> None:
        with self.assertRaises(ValueError):
            assert_no_pii("email=ada@example.com")
        with self.assertRaises(ValueError):
            assert_no_pii(f"peer={RAW_IP}")
        with self.assertRaises(ValueError):
            assert_no_pii(f"peer={RAW_IPV6}")
        with self.assertRaises(ValueError):
            assert_no_pii(FULL_UA)

    def test_make_record_discards_identity_kwargs(self) -> None:
        decision = resolve(self.compiled, self.ready.path, PII_QUERY, "smartlic.tech")
        record = make_record(
            manifesto_sha256=self.compiled.manifesto_sha256,
            config_sha256=self.compiled.config_sha256,
            decision=decision,
            path=self.ready.path,
            latency_ms=0.4,
            ts=FIXED,
            query=PII_QUERY,
            remote_ip=RAW_IP,
            user_agent=FULL_UA,
        )
        self.assertEqual(set(record) & {"query", "remote_ip", "user_agent", "ip", "ua"}, set())
        self.assertEqual(_forbidden_in(serialize_record(record)), [])


class SummarySignalExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compiled = load_and_compile()
        cls.ready = cls.compiled.redirects[0]

    def test_first_301_is_bound_to_config_hash_and_404_stays_visible(self) -> None:
        rec = WindowRecorder(
            self.compiled.manifesto_sha256,
            self.compiled.config_sha256,
            clock=lambda: FIXED,
        )
        empty = rec.summary()
        self.assertIsNone(empty["first_301"]["at"])
        self.assertEqual(empty["counts"]["301"], 0)
        self.assertEqual(empty["counts"]["404"], 0)
        self.assertEqual(empty["retention_days"], RETENTION_DAYS)

        ready = resolve(self.compiled, self.ready.path, "", "smartlic.tech")
        rec.record(ready, path=self.ready.path, latency_ms=0.8)
        gone = resolve(self.compiled, "/login", "", "smartlic.tech")
        rec.record(gone, path="/login", latency_ms=0.2)
        unexpected = Decision(status=404, location=None, rule_id="unexpected", family="retire", hops=0)
        rec.record(unexpected, path="/nope", latency_ms=0.1)

        summary = rec.summary()
        self.assertEqual(summary["first_301"]["at"], "2026-08-16T20:00:00.000Z")
        self.assertEqual(summary["first_301"]["config_sha256"], self.compiled.config_sha256)
        self.assertEqual(summary["first_301"]["manifesto_sha256"], self.compiled.manifesto_sha256)
        self.assertEqual(summary["first_301"]["scope"], "process-local")
        self.assertEqual(summary["counts"]["301"], 1)
        self.assertEqual(summary["counts"]["410"], 1)
        self.assertEqual(summary["counts"]["404"], 1)
        self.assertEqual(summary["by_path_class"]["ready"], 1)
        self.assertEqual(summary["by_path_class"]["login"], 1)
        self.assertEqual(summary["by_path_class"]["unmapped"], 1)
        self.assertIsNone(unexpected.location)

        local = evaluate_signals(summary)
        self.assertFalse(local["window_started"])
        self.assertEqual(local["first_301_scope"], "process-local")
        self.assertEqual(local["removal"], "HOLD_WINDOW_NOT_STARTED")
        self.assertTrue(local["residual_priority"])
        self.assertTrue(local["rollback"])
        self.assertEqual(local["unexpected_404"], 1)

        export = rec.export()
        self.assertEqual(export["schema"], EXPORT_SCHEMA)
        self.assertEqual(export["config_sha256"], self.compiled.config_sha256)
        self.assertEqual(export["first_301_at"], "2026-08-16T20:00:00.000Z")
        self.assertEqual(export["first_301_config_sha256"], self.compiled.config_sha256)
        self.assertEqual(export["first_production_301"], "UNOBSERVED")
        self.assertEqual(export["counts"]["301"], 1)
        self.assertEqual(export["counts"]["410"], 1)
        self.assertEqual(export["counts"]["404"], 1)
        self.assertIn("errors", export["counts"])
        self.assertIn("target_health", export)
        self.assertEqual(export["target_health"]["status"], "UNOBSERVED")
        self.assertIn("signals", export)
        self.assertEqual(export["retention_days"], RETENTION_DAYS)
        self.assertEqual(_forbidden_in(json.dumps(export, sort_keys=True)), [])

    def test_loopback_is_not_production_first_301(self) -> None:
        rec = WindowRecorder(self.compiled.manifesto_sha256, self.compiled.config_sha256)
        rec.record(
            resolve(self.compiled, self.ready.path, "", "127.0.0.1"),
            path=self.ready.path,
            latency_ms=0.3,
        )
        summary = rec.summary()
        self.assertEqual(summary["counts"]["301"], 1)
        self.assertEqual(summary["first_301"]["scope"], "process-local")
        signals = evaluate_signals(summary)
        self.assertFalse(signals["window_started"])
        self.assertEqual(signals["removal"], "HOLD_WINDOW_NOT_STARTED")
        refused = evaluate_signals(
            summary,
            production_first_301={
                "status": "BLOCKED",
                "detail": "refused source=loopback",
                "config_sha256": self.compiled.config_sha256,
            },
        )
        self.assertFalse(refused["window_started"])
        self.assertEqual(refused["first_301_scope"], "process-local")

    def test_production_probe_can_start_window_only_with_matching_hash(self) -> None:
        rec = WindowRecorder(self.compiled.manifesto_sha256, self.compiled.config_sha256)
        rec.record(
            resolve(self.compiled, self.ready.path, "", "smartlic.tech"),
            path=self.ready.path,
            latency_ms=0.3,
        )
        summary = rec.summary()
        wrong = evaluate_signals(
            summary,
            production_first_301={
                "status": "OBSERVED",
                "config_sha256": "0" * 64,
                "captured_at": "2026-07-01T00:00:00Z",
            },
        )
        self.assertFalse(wrong["window_started"])
        live = evaluate_signals(
            summary,
            production_first_301={
                "status": "OBSERVED",
                "config_sha256": self.compiled.config_sha256,
                "captured_at": "2026-07-01T00:00:00Z",
            },
            now=FIXED,
        )
        self.assertTrue(live["window_started"])
        self.assertTrue(live["window_elapsed"])
        self.assertEqual(live["removal"], "READY_FOR_REVIEW")
        self.assertEqual(live["first_301_scope"], "production")

    def test_target_health_fail_is_a_rollback_signal(self) -> None:
        self.assertEqual(target_health_from_results(None)["status"], "UNOBSERVED")
        self.assertEqual(target_health_from_results([{"status": 200}])["status"], "OK")
        failed = target_health_from_results([{"status": 404, "path": "/x"}])
        self.assertEqual(failed["status"], "FAIL")
        summary = {
            "config_sha256": self.compiled.config_sha256,
            "counts": {"404": 0, "errors": 0, "5xx": 0, "chain_gt1": 0},
            "target_health": failed,
        }
        signals = evaluate_signals(summary)
        self.assertTrue(signals["target_health_fail"])
        self.assertTrue(signals["rollback"])

    def test_observe_cli_writes_export_from_jsonl(self) -> None:
        rec = WindowRecorder(
            self.compiled.manifesto_sha256,
            self.compiled.config_sha256,
            clock=lambda: FIXED,
        )
        record = rec.record(
            resolve(self.compiled, self.ready.path, "", "smartlic.tech"),
            path=self.ready.path,
            latency_ms=1.0,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = root / "records.jsonl"
            dest = root / "export.json"
            records.write_text(serialize_record(record) + "\n", encoding="utf-8")
            rc = observe_main(["--records", str(records), "--export", str(dest)])
            self.assertEqual(rc, 0)
            export = json.loads(dest.read_text(encoding="utf-8"))
            self.assertEqual(export["schema"], EXPORT_SCHEMA)
            self.assertEqual(export["counts"]["301"], 1)
            self.assertEqual(export["first_301_scope"], "process-local")
            self.assertEqual(export["first_production_301"], "UNOBSERVED")
            self.assertIn("retention_days", dest.read_text(encoding="utf-8"))


class ServeWindowLaunchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compiled = load_and_compile()
        cls.ready = cls.compiled.redirects[0]

    def _launch(self, port: int, records: Path, export: Path) -> subprocess.Popen[str]:
        return subprocess.Popen(
            [
                sys.executable,
                "-m",
                "bridge.serve",
                "--map",
                str(GENERATED_DIR / "bridge-map.json"),
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--records-file",
                str(records),
                "--export-file",
                str(export),
            ],
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def _wait_ready(self, proc: subprocess.Popen[str], timeout: float = 5.0) -> str:
        deadline = time.time() + timeout
        assert proc.stdout is not None
        buf = ""
        while time.time() < deadline:
            if proc.poll() is not None:
                err = proc.stderr.read() if proc.stderr else ""
                raise AssertionError(f"serve.py exited {proc.returncode}: {err}")
            line = proc.stdout.readline()
            buf += line
            if "SERVE_OK" in buf:
                return buf
            time.sleep(0.05)
        raise AssertionError(f"serve.py did not become ready: {buf!r}")

    def _hit(self, port: int, path: str, extra_headers: dict[str, str] | None = None) -> tuple[int, str | None, str, dict]:
        headers = {"Host": "smartlic.tech"}
        if extra_headers:
            headers.update(extra_headers)
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            conn.request("GET", path, headers=headers)
            resp = conn.getresponse()
            raw = resp.read()
            health: dict = {}
            if path.startswith("/__bridge/"):
                health = json.loads(raw.decode("utf-8"))
            return resp.status, resp.getheader("Location"), resp.getheader("X-Bridge-Config-Hash") or "", health
        finally:
            conn.close()

    def _one_run(self, port: int, tmp: Path) -> dict:
        records = tmp / f"records-{port}.jsonl"
        export = tmp / f"export-{port}.json"
        proc = self._launch(port, records, export)
        try:
            banner = self._wait_ready(proc)
            ready_status, ready_loc, cfg, _h = self._hit(
                port,
                self.ready.path + "?" + PII_QUERY,
                extra_headers={"User-Agent": FULL_UA, "X-Forwarded-For": RAW_IP},
            )
            gone_status, gone_loc, cfg2, _h2 = self._hit(port, "/login")
            health_status, health_loc, cfg3, health = self._hit(port, "/__bridge/health")
            self.assertEqual(cfg, cfg2)
            self.assertEqual(cfg, cfg3)
            return {
                "banner": banner,
                "ready_status": ready_status,
                "ready_location": ready_loc,
                "gone_status": gone_status,
                "gone_location": gone_loc,
                "health_status": health_status,
                "health_location": health_loc,
                "config_hash": cfg,
                "health": health,
                "records": records,
                "export": export,
                "proc": proc,
            }
        except Exception:
            proc.kill()
            proc.communicate(timeout=3)
            raise

    def _stop(self, proc: subprocess.Popen[str]) -> str:
        proc.terminate()
        try:
            _out, err = proc.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            _out, err = proc.communicate(timeout=3)
        return err or ""

    def test_two_real_serve_launches_emit_window_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self._one_run(18871, root)
            first_err = self._stop(first["proc"])
            second = self._one_run(18872, root)
            second_err = self._stop(second["proc"])

            for run, err in ((first, first_err), (second, second_err)):
                self.assertIn("SERVE_OK", run["banner"])
                self.assertIn(PINNED_SHA256, run["banner"])
                self.assertIn(self.compiled.config_sha256, run["banner"])
                self.assertEqual(run["ready_status"], 301)
                self.assertEqual(run["ready_location"], self.ready.target_url)
                self.assertNotIn("email=", run["ready_location"] or "")
                self.assertEqual(run["gone_status"], 410)
                self.assertIsNone(run["gone_location"])
                self.assertEqual(run["health_status"], 200)
                self.assertIsNone(run["health_location"])
                self.assertEqual(run["config_hash"], self.compiled.config_sha256)
                window = run["health"]["window"]
                self.assertEqual(window["config_sha256"], self.compiled.config_sha256)
                self.assertIsNotNone(window["first_301"]["at"])
                self.assertEqual(window["first_301"]["config_sha256"], self.compiled.config_sha256)
                self.assertEqual(window["counts"]["301"], 1)
                self.assertEqual(window["counts"]["410"], 1)
                self.assertEqual(window["counts"]["404"], 0)
                self.assertEqual(window["first_301"]["scope"], "process-local")
                blob = run["records"].read_text(encoding="utf-8") + err + json.dumps(run["health"])
                self.assertEqual(_forbidden_in(blob), [])
                lines = [json.loads(line) for line in run["records"].read_text(encoding="utf-8").splitlines() if line]
                self.assertEqual(len(lines), 2)
                self.assertEqual({row["status"] for row in lines}, {301, 410})
                for row in lines:
                    for key in ("ts", "manifesto_sha256", "config_sha256", "action", "path_class", "status", "latency_ms"):
                        self.assertIn(key, row)
                export = json.loads(run["export"].read_text(encoding="utf-8"))
                self.assertEqual(export["schema"], EXPORT_SCHEMA)
                self.assertEqual(export["first_production_301"], "UNOBSERVED")
                self.assertEqual(export["signals"]["removal"], "HOLD_WINDOW_NOT_STARTED")

            self.assertEqual(first["config_hash"], second["config_hash"])
            self.assertEqual(first["health"]["window"]["config_sha256"], second["health"]["window"]["config_sha256"])


class ShippedSurfacePrivacyTests(unittest.TestCase):
    def test_caddy_deletes_ua_and_client_ip(self) -> None:
        compiled = load_and_compile()
        rendered = render_caddyfile(compiled)
        self.assertIn("request>headers>User-Agent delete", rendered)
        self.assertIn("request>remote_ip delete", rendered)
        self.assertIn("request>client_ip delete", rendered)
        committed = (GENERATED_DIR / "Caddyfile").read_text(encoding="utf-8")
        self.assertIn("request>headers>User-Agent delete", committed)
        self.assertIn("request>remote_ip delete", committed)
        self.assertIn("request>client_ip delete", committed)
        self.assertNotRegex(committed, r"request>headers>User-Agent\s*$")

    def test_shipped_sources_have_no_analytics_stack_or_production_first_301_write(self) -> None:
        root = Path(__file__).resolve().parents[1]
        shipped = [
            root / "observe.py",
            root / "serve.py",
            root / "generate.py",
            root / "generated" / "Caddyfile",
        ]
        banned = (
            "mixpanel",
            "prometheus",
            "opentelemetry",
            "import stripe",
            "import fastapi",
            "from fastapi",
            "register_first_production_301",
        )
        hits: list[str] = []
        for path in shipped:
            text = path.read_text(encoding="utf-8").lower()
            for token in banned:
                if token in text:
                    hits.append(f"{path.name}: {token}")
        self.assertEqual(hits, [])

    def test_classify_path_does_not_echo_unknown_visitor_paths(self) -> None:
        compiled = load_and_compile()
        decision = resolve(compiled, "/visitor-token-abc123", "", "smartlic.tech")
        self.assertEqual(classify_path("/visitor-token-abc123", decision), "unmapped")
        record = make_record(
            manifesto_sha256=compiled.manifesto_sha256,
            config_sha256=compiled.config_sha256,
            decision=decision,
            path="/visitor-token-abc123",
            latency_ms=0.1,
            ts=FIXED,
        )
        self.assertNotIn("visitor-token-abc123", serialize_record(record))


if __name__ == "__main__":
    unittest.main()
