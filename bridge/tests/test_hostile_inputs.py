"""Hostile path/query/method/host matrix against the shipped evaluator and serve."""

from __future__ import annotations

import unittest
from urllib.parse import quote, urlencode, urlsplit

from bridge.generate import emit, load_and_compile
from bridge.generate import GENERATED_DIR
from bridge.pins import PII_QUERY_KEYS
from bridge.policy import resolve
from bridge.tests._evidence import write_evidence
from bridge.tests._harness import (
    assert_location_shape,
    assert_no_pii,
    http_get,
    launch_serve,
    parse_status_and_location,
    raw_http,
    stop_serve,
    wait_ready,
)

PII_QUERY = urlencode(
    {
        "email": "ada@example.com",
        "phone": "11999999999",
        "name": "Ada",
        "cnpj": "00000000000191",
        "cpf": "00000000000",
        "telefone": "11988887777",
        "nome": "Ada Lovelace",
        "password": "hunter2",
        "token": "secret-token",
        "secret": "super-secret",
        "utm_source": "gsc",
        "jornada": "defesa",
    }
)
CRLF_QUERY = "jornada=x%0d%0aLocation:%20https://evil.example/%0d%0aSet-Cookie:%20a=1"
FORBIDDEN_HOSTS = (
    "evil.example",
    "smartlic.tech.evil.example",
    "confenge.com.br",
    "www.confenge.com.br",
    "api.smartlic.tech",
    "smartlic.tech.attacker.invalid",
)
SERVE_PORT = 18880


class HostileEvaluatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compiled = load_and_compile()
        cls.ready = cls.compiled.redirects
        cls.hold = cls.compiled.holds
        cls.cases: list[dict[str, object]] = []

    def _record(self, name: str, path: str, query: str, host: str | None, decision) -> None:
        self.cases.append(
            {
                "host": host,
                "hops": decision.hops,
                "location": decision.location,
                "name": name,
                "path": path,
                "query": query,
                "rule_id": decision.rule_id,
                "status": decision.status,
                "surface": "evaluator",
            }
        )

    def _assert_fail_closed(self, decision, *, label: str) -> None:
        self.assertEqual(decision.status, 410, label)
        self.assertIsNone(decision.location, label)
        self.assertEqual(decision.hops, 0, label)
        assert_location_shape(decision.location, decision.status)

    def test_trailing_slash_ready_holds_and_unmapped(self) -> None:
        for rule in self.ready:
            decision = resolve(self.compiled, rule.path + "/", "", "smartlic.tech")
            self._record("trailing-slash-ready", rule.path + "/", "", "smartlic.tech", decision)
            with self.subTest(path=rule.path):
                self.assertEqual(decision.status, 301)
                self.assertEqual(decision.location, rule.target_url)
                self.assertEqual(decision.hops, 1)
                assert_location_shape(decision.location, 301)
        for path in self.hold:
            decision = resolve(self.compiled, path + "/", "", "smartlic.tech")
            self._record("trailing-slash-hold", path + "/", "", "smartlic.tech", decision)
            with self.subTest(path=path):
                self._assert_fail_closed(decision, label=path + "/")
        unmapped = resolve(self.compiled, "/not-mapped/", "", "smartlic.tech")
        self._record("trailing-slash-unmapped", "/not-mapped/", "", "smartlic.tech", unmapped)
        self._assert_fail_closed(unmapped, label="/not-mapped/")

    def test_percent_encoding_does_not_open_a_ready_row_or_redirect(self) -> None:
        rule = self.ready[0]
        variants = (
            quote(rule.path, safe=""),
            quote(rule.path, safe="/").replace("/", "%2F", 1),
            rule.path.replace("/", "%2f"),
            "/%2F%2Fevil.example",
            "/%2f%2fevil.example",
            "/%252F%252Fevil.example",
            quote("//evil.example", safe=""),
        )
        for path in variants:
            decision = resolve(self.compiled, path, "", "smartlic.tech")
            self._record("encoding", path, "", "smartlic.tech", decision)
            with self.subTest(path=path):
                self._assert_fail_closed(decision, label=path)

    def test_case_fold_does_not_invent_a_redirect(self) -> None:
        for rule in self.ready:
            for path in (rule.path.upper(), rule.path.title(), rule.path.swapcase()):
                if path == rule.path:
                    continue
                decision = resolve(self.compiled, path, "", "smartlic.tech")
                self._record("case", path, "", "smartlic.tech", decision)
                with self.subTest(path=path):
                    self._assert_fail_closed(decision, label=path)

    def test_duplicate_slashes_do_not_open_redirect_or_ready_row(self) -> None:
        rule = self.ready[0]
        variants = (
            "/" + rule.path,
            "//" + rule.path.lstrip("/"),
            rule.path.replace("/", "//"),
            "//evil.example",
            "///evil.example",
            "/\\evil.example",
            "//confenge.com.br/consultoria-b2g",
            "https://evil.example/",
        )
        for path in variants:
            decision = resolve(self.compiled, path, "", "smartlic.tech")
            self._record("dup-slash", path, "", "smartlic.tech", decision)
            with self.subTest(path=path):
                self._assert_fail_closed(decision, label=path)

    def test_fragment_suffix_is_fail_closed_on_the_evaluator(self) -> None:
        rule = self.ready[0]
        decision = resolve(self.compiled, rule.path + "#evil", "", "smartlic.tech")
        self._record("fragment-in-path", rule.path + "#evil", "", "smartlic.tech", decision)
        self._assert_fail_closed(decision, label=rule.path + "#evil")

    def test_spoofed_hosts_are_410(self) -> None:
        rule = self.ready[0]
        for host in FORBIDDEN_HOSTS:
            decision = resolve(self.compiled, rule.path, "", host)
            self._record("host-spoof", rule.path, "", host, decision)
            with self.subTest(host=host):
                self._assert_fail_closed(decision, label=host)

    def test_crlf_in_host_does_not_open_redirect(self) -> None:
        rule = self.ready[0]
        hosts = (
            "smartlic.tech\r\nLocation: https://evil.example/",
            "smartlic.tech\nX-Injected: 1",
            "smartlic.tech\r\n\r\nGET / HTTP/1.1",
            "evil.example\r\nHost: smartlic.tech",
        )
        for host in hosts:
            decision = resolve(self.compiled, rule.path, "", host)
            self._record("host-crlf", rule.path, "", host.replace("\r", "\\r").replace("\n", "\\n"), decision)
            with self.subTest(host=repr(host)):
                self._assert_fail_closed(decision, label=repr(host))

    def test_pii_and_crlf_queries_never_land_in_location(self) -> None:
        rule = self.ready[0]
        decision = resolve(self.compiled, rule.path, PII_QUERY, "smartlic.tech")
        self._record("pii-query", rule.path, PII_QUERY, "smartlic.tech", decision)
        self.assertEqual(decision.status, 301)
        self.assertIsNotNone(decision.location)
        assert_location_shape(decision.location, 301)
        assert_no_pii(decision.location, label="ready-pii")
        qs = urlsplit(decision.location or "").query
        self.assertIn("utm_source=gsc", qs)
        self.assertIn("jornada=defesa", qs)
        for key in PII_QUERY_KEYS:
            self.assertNotIn(f"{key}=", (decision.location or "").lower())

        injected = resolve(self.compiled, rule.path, CRLF_QUERY, "smartlic.tech")
        self._record("crlf-query", rule.path, CRLF_QUERY, "smartlic.tech", injected)
        self.assertEqual(injected.status, 301)
        assert_location_shape(injected.location, 301)
        self.assertNotIn("\r", injected.location or "")
        self.assertNotIn("\n", injected.location or "")
        self.assertNotIn("evil.example", urlsplit(injected.location or "").netloc)
        # urlencode may keep the literal letters Set-Cookie inside a query
        # value; that is not a second response header. The host stays pinned.
        self.assertEqual(urlsplit(injected.location or "").hostname, "confenge.com.br")
        self.assertTrue(
            (injected.location or "").startswith(rule.target_url),
            injected.location,
        )

        hold = resolve(self.compiled, self.hold[0], PII_QUERY, "smartlic.tech")
        self._record("pii-hold", self.hold[0], PII_QUERY, "smartlic.tech", hold)
        self._assert_fail_closed(hold, label="hold-pii")
        assert_no_pii(hold.location, label="hold-pii")

    @classmethod
    def tearDownClass(cls) -> None:
        write_evidence(
            "hostile-evaluator.json",
            {
                "n_cases": len(cls.cases),
                "surface": "evaluator",
                "cases": cls.cases,
            },
        )


class HostileServeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compiled = load_and_compile()
        emit(cls.compiled, GENERATED_DIR)
        cls.rule = cls.compiled.redirects[0]
        cls.proc = launch_serve(SERVE_PORT)
        cls.banner = wait_ready(cls.proc)
        cls.stderr = ""
        cls.cases: list[dict[str, object]] = []

    @classmethod
    def tearDownClass(cls) -> None:
        _out, err = stop_serve(cls.proc)
        cls.stderr = err
        evaluator_cases = getattr(HostileEvaluatorTests, "cases", [])
        write_evidence(
            "hostile-matrix.json",
            {
                "banner": cls.banner.strip(),
                "cases": list(evaluator_cases) + list(cls.cases),
                "n_cases": len(evaluator_cases) + len(cls.cases),
                "n_evaluator": len(evaluator_cases),
                "n_serve": len(cls.cases),
                "stderr": err,
            },
        )

    def _record_http(self, name: str, status: int, location: str | None, **extra: object) -> None:
        self.cases.append(
            {
                "location": location,
                "name": name,
                "status": status,
                "surface": "serve",
                **extra,
            }
        )

    def test_banner_is_serve_ok(self) -> None:
        self.assertIn("SERVE_OK", self.banner)
        self.assertIn(self.compiled.manifesto_sha256, self.banner)
        self.assertIn(self.compiled.config_sha256, self.banner)

    def test_methods_other_than_get_head_do_not_redirect(self) -> None:
        for method in ("POST", "PUT", "DELETE", "OPTIONS", "PATCH", "TRACE"):
            status, location, _headers = http_get(
                SERVE_PORT, self.rule.path, method=method
            )
            self._record_http("method", status, location, method=method, path=self.rule.path)
            with self.subTest(method=method):
                self.assertNotEqual(status, 301, method)
                self.assertIsNone(location, method)
                self.assertIn(status, {400, 405, 501})

        head_status, head_loc, _headers = http_get(
            SERVE_PORT, self.rule.path, method="HEAD"
        )
        self._record_http("method", head_status, head_loc, method="HEAD", path=self.rule.path)
        self.assertEqual(head_status, 301)
        self.assertEqual(head_loc, self.rule.target_url)
        assert_location_shape(head_loc, 301)

        get_status, get_loc, _headers = http_get(SERVE_PORT, self.rule.path)
        self.assertEqual(get_status, 301)
        self.assertEqual(get_loc, self.rule.target_url)

    def test_host_spoof_over_http_is_410(self) -> None:
        for host in FORBIDDEN_HOSTS:
            status, location, _headers = http_get(
                SERVE_PORT, self.rule.path, host=host
            )
            self._record_http("host-spoof", status, location, host=host)
            with self.subTest(host=host):
                self.assertEqual(status, 410)
                self.assertIsNone(location)

    def test_raw_host_crlf_does_not_inject_response_headers(self) -> None:
        request = (
            f"GET {self.rule.path} HTTP/1.1\r\n"
            "Host: smartlic.tech\r\n"
            "X-Attack: 1\r\nLocation: https://evil.example/\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).encode("ascii")
        raw = raw_http(SERVE_PORT, request)
        status, location = parse_status_and_location(raw)
        self._record_http("raw-extra-location-header", status, location)
        self.assertEqual(status, 301)
        self.assertEqual(location, self.rule.target_url)
        self.assertNotIn(b"evil.example", raw.split(b"\r\n\r\n", 1)[0])
        assert_location_shape(location, 301)

        injected_host = (
            f"GET {self.rule.path} HTTP/1.1\r\n"
            "Host: smartlic.tech\r\nLocation: https://evil.example/\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).encode("ascii")
        raw2 = raw_http(SERVE_PORT, injected_host)
        status2, location2 = parse_status_and_location(raw2)
        self._record_http("raw-host-crlf-as-two-headers", status2, location2)
        self.assertEqual(status2, 301)
        self.assertEqual(location2, self.rule.target_url)
        self.assertNotIn(b"evil.example", raw2.split(b"\r\n\r\n", 1)[0])

        bad_host = (
            f"GET {self.rule.path} HTTP/1.1\r\n"
            "Host: evil.example\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).encode("ascii")
        raw3 = raw_http(SERVE_PORT, bad_host)
        status3, location3 = parse_status_and_location(raw3)
        self._record_http("raw-evil-host", status3, location3)
        self.assertEqual(status3, 410)
        self.assertIsNone(location3)

    def test_fragment_is_stripped_by_urlsplit_on_the_wire(self) -> None:
        status, location, _headers = http_get(
            SERVE_PORT, self.rule.path + "#ignored"
        )
        self._record_http("fragment", status, location, path=self.rule.path + "#ignored")
        self.assertEqual(status, 301)
        self.assertEqual(location, self.rule.target_url)

    def test_crlf_query_does_not_inject_response_headers(self) -> None:
        status, location, headers = http_get(
            SERVE_PORT, f"{self.rule.path}?{CRLF_QUERY}"
        )
        self._record_http("crlf-query", status, location)
        self.assertEqual(status, 301)
        assert_location_shape(location, 301)
        self.assertNotIn("\r", location or "")
        self.assertNotIn("\n", location or "")
        self.assertNotIn("set-cookie", headers)
        self.assertEqual(urlsplit(location or "").hostname, "confenge.com.br")

    def test_pii_query_absent_from_location_and_stderr(self) -> None:
        path = f"{self.rule.path}?{PII_QUERY}"
        status, location, _headers = http_get(SERVE_PORT, path)
        self._record_http("pii-query", status, location, path=self.rule.path)
        self.assertEqual(status, 301)
        assert_location_shape(location, 301)
        assert_no_pii(location, label="serve-location")
        self.assertNotIn("email=", location or "")
        self.assertNotIn("token=", location or "")

        hold_path = f"{self.compiled.holds[0]}?{PII_QUERY}"
        hold_status, hold_loc, _headers = http_get(SERVE_PORT, hold_path)
        self._record_http("pii-hold", hold_status, hold_loc)
        self.assertEqual(hold_status, 410)
        self.assertIsNone(hold_loc)

    def test_duplicate_slash_and_encoding_over_http_never_open_redirect(self) -> None:
        # HTTP parsers may collapse `//blog/ready` onto the ready row (301 to
        # the pinned target). That is still one hop to confenge. `//evil` and
        # percent-encoded lookalikes must stay 410.
        collapsed = "//" + self.rule.path.lstrip("/")
        status, location, _headers = http_get(SERVE_PORT, collapsed)
        self._record_http("leading-double-slash-ready", status, location, path=collapsed)
        self.assertIn(status, {301, 410})
        if status == 301:
            self.assertEqual(location, self.rule.target_url)
            assert_location_shape(location, 301)
        else:
            self.assertIsNone(location)

        closed = (
            self.rule.path.replace("/", "//"),
            quote(self.rule.path, safe=""),
            "//evil.example",
            "//confenge.com.br/",
            "//confenge.com.br/consultoria-b2g",
            "/not-mapped",
        )
        for path in closed:
            status, location, _headers = http_get(SERVE_PORT, path)
            self._record_http("slash-encoding", status, location, path=path)
            with self.subTest(path=path):
                self.assertEqual(status, 410)
                self.assertIsNone(location)


class HostileServeLogTests(unittest.TestCase):
    """Separate launch so stderr is only the PII request."""

    def test_serve_log_does_not_record_query_or_pii(self) -> None:
        compiled = load_and_compile()
        emit(compiled, GENERATED_DIR)
        rule = compiled.redirects[0]
        proc = launch_serve(18881)
        try:
            wait_ready(proc)
            http_get(18881, f"{rule.path}?{PII_QUERY}")
            http_get(18881, f"/login?email=ada@example.com&token=secret")
        finally:
            _out, err = stop_serve(proc)
        for key in PII_QUERY_KEYS:
            self.assertNotIn(f"{key}=", err.lower(), key)
        self.assertNotIn("ada@example.com", err)
        self.assertNotIn("secret-token", err)
        self.assertNotIn("00000000000191", err)
        self.assertNotIn("utm_source=", err)
        write_evidence(
            "hostile-logs.json",
            {"stderr": err, "pii_keys_checked": sorted(PII_QUERY_KEYS)},
        )


if __name__ == "__main__":
    unittest.main()
