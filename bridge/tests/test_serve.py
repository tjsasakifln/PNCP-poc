"""Launch the shipped serve.py against the generated map — twice."""

from __future__ import annotations

import http.client
import subprocess
import sys
import time
import unittest
from pathlib import Path

from bridge.generate import GENERATED_DIR, emit, load_and_compile
from bridge.pins import PINNED_SHA256

ROOT = Path(__file__).resolve().parents[2]


class ServeLaunchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compiled = load_and_compile()
        emit(cls.compiled, GENERATED_DIR)

    def _launch(self, port: int) -> subprocess.Popen[str]:
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

    def _hit(self, port: int, path: str) -> tuple[int, str | None, str]:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            conn.request("GET", path, headers={"Host": "smartlic.tech"})
            resp = conn.getresponse()
            resp.read()
            return resp.status, resp.getheader("Location"), resp.getheader("X-Bridge-Config-Hash") or ""
        finally:
            conn.close()

    def test_two_launches_same_status_and_location(self) -> None:
        rule = self.compiled.redirects[0]
        first = self._one_run(18765, rule)
        second = self._one_run(18766, rule)
        comparable = ("ready_status", "ready_location", "unmapped_status", "unmapped_location",
                      "login_status", "login_location", "config_hash", "manifest_ok")
        self.assertEqual({k: first[k] for k in comparable}, {k: second[k] for k in comparable})
        self.assertEqual(first["ready_status"], 301)
        self.assertEqual(first["ready_location"], rule.target_url)
        self.assertEqual(first["unmapped_status"], 410)
        self.assertIsNone(first["unmapped_location"])
        self.assertEqual(first["login_status"], 410)
        self.assertIsNone(first["login_location"])
        self.assertEqual(first["config_hash"], self.compiled.config_sha256)
        self.assertEqual(first["manifest_ok"], PINNED_SHA256)
        self.assertIn(PINNED_SHA256, first["banner"])
        self.assertIn(self.compiled.config_sha256, first["banner"])
        self.assertIn("SERVE_OK", first["banner"])
        self.assertIn("SERVE_OK", second["banner"])

    def test_all_ready_paths_and_410_negatives_over_http(self) -> None:
        proc = self._launch(18767)
        try:
            banner = self._wait_ready(proc)
            self.assertIn("SERVE_OK", banner)
            self.assertIn(PINNED_SHA256, banner)
            for rule in self.compiled.redirects:
                status, location, cfg = self._hit(18767, rule.path)
                self.assertEqual(status, 301, rule.path)
                self.assertEqual(location, rule.target_url, rule.path)
                self.assertEqual(cfg, self.compiled.config_sha256)
            for path in ("/login", "/signup", "/pricing", "/webhooks", "/v1", "/webhooks/stripe", "/v1/search"):
                status, location, _cfg = self._hit(18767, path)
                self.assertEqual(status, 410, path)
                self.assertIsNone(location, path)
            health = self._hit_body(18767, "/__bridge/health")
            self.assertEqual(health["status"], "ok")
            self.assertEqual(health["manifesto_sha256"], PINNED_SHA256)
            self.assertEqual(health["config_sha256"], self.compiled.config_sha256)
            self.assertEqual(health["redirects"], 11)
        finally:
            proc.terminate()
            try:
                proc.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate(timeout=3)

    def _one_run(self, port: int, rule) -> dict:
        proc = self._launch(port)
        try:
            banner = self._wait_ready(proc)
            self.assertIn(PINNED_SHA256, banner)
            ready_status, ready_loc, cfg = self._hit(port, rule.path)
            unmapped_status, unmapped_loc, cfg2 = self._hit(port, "/not-mapped-2115")
            login_status, login_loc, cfg3 = self._hit(port, "/login")
            self.assertEqual(cfg, cfg2)
            self.assertEqual(cfg, cfg3)
            return {
                "ready_status": ready_status,
                "ready_location": ready_loc,
                "unmapped_status": unmapped_status,
                "unmapped_location": unmapped_loc,
                "login_status": login_status,
                "login_location": login_loc,
                "config_hash": cfg,
                "manifest_ok": PINNED_SHA256 if PINNED_SHA256 in banner else "",
                "banner": banner,
            }
        finally:
            proc.terminate()
            try:
                proc.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate(timeout=3)

    def _hit_body(self, port: int, path: str) -> dict:
        import json

        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            conn.request("GET", path, headers={"Host": "smartlic.tech"})
            resp = conn.getresponse()
            raw = resp.read()
            self.assertEqual(resp.status, 200, path)
            self.assertIsNone(resp.getheader("Location"))
            return json.loads(raw.decode("utf-8"))
        finally:
            conn.close()


class NoProductRuntimeTests(unittest.TestCase):
    def test_shipped_runtime_has_no_product_upstreams_or_imports(self) -> None:
        root = Path(__file__).resolve().parents[1]
        shipped = [
            root / "generate.py",
            root / "serve.py",
            root / "policy.py",
            root / "pins.py",
            root / "generated" / "Caddyfile",
            root / "deploy" / "smartlic-bridge.service",
            root / "deploy" / "caddy-bridge.service",
            root / "deploy" / "nftables.conf",
        ]
        banned = (
            "import fastapi",
            "from fastapi",
            "import uvicorn",
            "from arq",
            "import redis",
            "import stripe",
            "reverse_proxy 127.0.0.1:8000",
            "reverse_proxy 127.0.0.1:3000",
        )
        hits: list[str] = []
        for path in shipped:
            text = path.read_text(encoding="utf-8")
            lowered = text.lower()
            for token in banned:
                if token in lowered:
                    hits.append(f"{path.name}: {token}")
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
