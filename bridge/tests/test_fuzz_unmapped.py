"""Property/fuzz unmapped and malformed paths against the shipped evaluator."""

from __future__ import annotations

import random
import string
import unittest
from urllib.parse import quote

from bridge.generate import load_and_compile
from bridge.policy import resolve
from bridge.tests._evidence import write_evidence
from bridge.tests._harness import assert_location_shape

SEED = 2115
N_RANDOM = 400


def _alphabet() -> str:
    return string.ascii_letters + string.digits + "-._~%/"


def generate_paths(rng: random.Random, n: int) -> list[str]:
    canned = [
        "",
        "/",
        "//",
        "///",
        "/.",
        "/..",
        "/../",
        "/../etc/passwd",
        "/.",
        "/././login",
        "/not-mapped",
        "/not-mapped-2115",
        "/index.php",
        "/wp-admin",
        "/.env",
        "/.git/config",
        "/%00",
        "/\x00",
        "/\r\nLocation: https://evil.example/",
        "/\\",
        "/\\evil.example",
        "//evil.example",
        "//evil.example/%2e%2e",
        "/%2e%2e/%2e%2e/etc/passwd",
        "/%2F%2Fevil.example",
        "https://evil.example/",
        "http://smartlic.tech/login",
        "//confenge.com.br/",
        "//confenge.com.br/consultoria-b2g",
        "/consultoria-b2g",
        "/CONSULTORIA-B2G",
        "/login%00",
        "/login/" + ("a" * 4096),
        "/" + "åção",
        "/blog/" + "\u202e" + "evil",
        "/intel-reports/not-a-session",
        "/intel-reports/{sessionId}/extra",
        quote("//evil.example", safe=""),
        "/%0d%0aLocation:%20https://evil.example/",
        "/foo?bar#baz",
        "/foo#bar",
        "/////",
        "/./blog/aditivos-contratuais-o-que-sao-como-monitorar",
        "/blog/../blog/aditivos-contratuais-o-que-sao-como-monitorar",
        "/blog/aditivos-contratuais-o-que-sao-como-monitorar/../login",
        "/blog%2faditivos-contratuais-o-que-sao-como-monitorar",
        "/%2fblog%2faditivos-contratuais-o-que-sao-como-monitorar",
        "/blog/aditivos-contratuais-o-que-sao-como-monitorar%2f",
        "/v1/search?q=x",
        "/webhooks/stripe",
        "/__bridge/../login",
    ]
    paths = list(canned)
    alphabet = _alphabet()
    while len(paths) < n:
        length = rng.choice((1, 2, 3, 8, 16, 32, 64, 128))
        body = "".join(rng.choice(alphabet) for _ in range(length))
        prefix = rng.choice(("/", "//", "///", "/.", "/../", "/%2e/", "/foo/"))
        paths.append(prefix + body)
    return paths[:n]


class FuzzUnmappedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compiled = load_and_compile()
        cls.ready_paths = {rule.path for rule in cls.compiled.redirects}

    def test_unmapped_and_malformed_paths_fail_closed(self) -> None:
        rng = random.Random(SEED)
        paths = generate_paths(rng, N_RANDOM)
        failures: list[dict[str, object]] = []
        ready_hits = 0
        samples: list[dict[str, object]] = []
        for path in paths:
            decision = resolve(self.compiled, path, "email=ada@example.com&token=secret", "smartlic.tech")
            is_ready = path.rstrip("/") == path and path in self.ready_paths
            # generate_paths never emits an exact ready path; trailing-slash of a
            # ready row would 301, so treat only exact ready rows as allowed 301.
            if is_ready:
                ready_hits += 1
                if decision.status != 301 or decision.location is None:
                    failures.append(
                        {
                            "path": path,
                            "reason": "ready-row-miss",
                            "status": decision.status,
                            "location": decision.location,
                        }
                    )
                continue
            try:
                self.assertEqual(decision.status, 410, path)
                self.assertIsNone(decision.location, path)
                self.assertEqual(decision.hops, 0, path)
                assert_location_shape(decision.location, decision.status)
            except AssertionError as exc:
                failures.append(
                    {
                        "path": path,
                        "reason": str(exc),
                        "status": decision.status,
                        "location": decision.location,
                        "hops": decision.hops,
                    }
                )
            if len(samples) < 40:
                samples.append(
                    {
                        "location": decision.location,
                        "path": path,
                        "status": decision.status,
                    }
                )
        write_evidence(
            "fuzz-unmapped.json",
            {
                "failures": failures,
                "n": len(paths),
                "ready_hits": ready_hits,
                "samples": samples,
                "seed": SEED,
            },
        )
        self.assertEqual(failures, [])
        self.assertEqual(ready_hits, 0)

    def test_host_fuzz_never_opens_foreign_location(self) -> None:
        rng = random.Random(SEED + 1)
        rule = self.compiled.redirects[0]
        known_legacy = (
            "",
            None,
            "localhost",
            "127.0.0.1",
            "smartlic.tech",
            "www.smartlic.tech",
            "SMARTLIC.TECH",
            "smartlic.tech:8765",
            "smartlic.tech:443",
        )
        spoofed = (
            "evil.example",
            "evil.example:443",
            "confenge.com.br",
            "smartlic.tech.evil.example",
            "smartlic.tech\r\nLocation: https://evil.example/",
            "127.0.0.1:9\r\nLocation: https://evil.example/",
            "api.smartlic.tech",
        )
        hosts: list[str | None] = list(known_legacy) + list(spoofed)
        while len(hosts) < 80:
            hosts.append("".join(rng.choice(string.ascii_lowercase + ".-") for _ in range(12)))
        failures: list[dict[str, object]] = []
        for host in hosts:
            decision = resolve(self.compiled, rule.path, "", host)
            try:
                # Property: every host is either the pinned one-hop 301 or fail-closed
                # 410. No foreign Location, no home, no CRLF, no extra hop.
                if decision.status == 301:
                    self.assertEqual(decision.location, rule.target_url, host)
                    self.assertEqual(decision.hops, 1, host)
                    assert_location_shape(decision.location, 301)
                else:
                    self.assertEqual(decision.status, 410, host)
                    self.assertIsNone(decision.location, host)
                    self.assertEqual(decision.hops, 0, host)
            except AssertionError as exc:
                failures.append({"host": host, "reason": str(exc), "status": decision.status})
        for host in spoofed:
            decision = resolve(self.compiled, rule.path, "", host)
            self.assertEqual(decision.status, 410, host)
            self.assertIsNone(decision.location, host)
        for host in known_legacy:
            decision = resolve(self.compiled, rule.path, "", host)
            self.assertEqual(decision.status, 301, host)
            self.assertEqual(decision.location, rule.target_url, host)
        write_evidence(
            "fuzz-hosts.json",
            {"failures": failures, "n": len(hosts), "seed": SEED + 1},
        )
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
