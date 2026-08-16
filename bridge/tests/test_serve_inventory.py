"""Launch python3 -m bridge.serve twice and HTTP-exercise every inventory path."""

from __future__ import annotations

import hashlib
import json
import unittest
from urllib.parse import urlsplit

from bridge.generate import GENERATED_DIR, emit, load_and_compile, load_manifest_bytes
from bridge.pins import PINNED_SHA256
from bridge.policy import normalize_path
from bridge.tests._evidence import write_evidence
from bridge.tests._harness import (
    assert_location_shape,
    expected_action,
    http_get,
    launch_serve,
    stop_serve,
    wait_ready,
)

PORTS = (18891, 18892)


class ServeInventoryBlackboxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compiled = load_and_compile()
        emit(cls.compiled, GENERATED_DIR)
        cls.entries = json.loads(load_manifest_bytes())["entries"]
        cls.paths: list[tuple[str, int, str | None]] = []
        for entry in cls.entries:
            path = normalize_path(urlsplit(entry["legacy_url"]).path)
            status, location = expected_action(entry)
            cls.paths.append((path, status, location))
        cls.paths.append(("/not-mapped", 410, None))

    def _run_launch(self, port: int) -> dict[str, object]:
        proc = launch_serve(port)
        try:
            banner = wait_ready(proc)
            self.assertIn("SERVE_OK", banner)
            self.assertIn(PINNED_SHA256, banner)
            self.assertIn(self.compiled.config_sha256, banner)
            rows: list[str] = []
            n_301 = 0
            n_410 = 0
            mismatches: list[dict[str, object]] = []
            config_hashes: set[str] = set()
            for path, expected_status, expected_location in self.paths:
                status, location, headers = http_get(port, path)
                cfg = headers.get("x-bridge-config-hash", "")
                config_hashes.add(cfg)
                try:
                    self.assertEqual(status, expected_status, path)
                    self.assertEqual(location, expected_location, path)
                    assert_location_shape(location, status)
                    self.assertEqual(cfg, self.compiled.config_sha256, path)
                except AssertionError as exc:
                    mismatches.append(
                        {
                            "path": path,
                            "expected_location": expected_location,
                            "expected_status": expected_status,
                            "location": location,
                            "status": status,
                            "reason": str(exc),
                        }
                    )
                if status == 301:
                    n_301 += 1
                elif status == 410:
                    n_410 += 1
                rows.append(f"{path}|{status}|{location or ''}")
            fingerprint = hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()
            return {
                "banner": banner.strip(),
                "config_hashes": sorted(config_hashes),
                "fingerprint": fingerprint,
                "mismatches": mismatches,
                "n_301": n_301,
                "n_410": n_410,
                "n_paths": len(self.paths),
                "port": port,
            }
        finally:
            stop_serve(proc)

    def test_two_launches_identical_status_and_location_for_every_row(self) -> None:
        first = self._run_launch(PORTS[0])
        second = self._run_launch(PORTS[1])
        write_evidence(
            "serve-blackbox.json",
            {
                "config_sha256": self.compiled.config_sha256,
                "identical": first["fingerprint"] == second["fingerprint"],
                "launch_1": first,
                "launch_2": second,
                "manifesto_sha256": self.compiled.manifesto_sha256,
                "n_inventory": 1255,
                "n_plus_default": len(self.paths),
            },
        )
        self.assertEqual(first["mismatches"], [])
        self.assertEqual(second["mismatches"], [])
        self.assertEqual(first["fingerprint"], second["fingerprint"])
        self.assertEqual(first["n_301"], 11)
        self.assertEqual(second["n_301"], 11)
        # 1190 RETIRE + 54 HOLD + default /not-mapped
        self.assertEqual(first["n_410"], 1245)
        self.assertEqual(second["n_410"], 1245)
        self.assertEqual(first["config_hashes"], [self.compiled.config_sha256])
        self.assertEqual(second["config_hashes"], [self.compiled.config_sha256])
        self.assertIn("SERVE_OK", first["banner"])
        self.assertIn("SERVE_OK", second["banner"])


if __name__ == "__main__":
    unittest.main()
