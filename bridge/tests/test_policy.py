"""Policy tests call the shipped resolver on the compiled pinned map."""

from __future__ import annotations

import unittest
from urllib.parse import parse_qs, urlsplit

from bridge.generate import load_and_compile
from bridge.pins import DEFAULT_STATUS, REDIRECT_STATUS, TARGET_HOSTNAME
from bridge.policy import filter_query, resolve


class PolicyReadyRedirectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compiled = load_and_compile()

    def test_every_ready_rule_is_one_hop_301_to_manifest_target(self) -> None:
        self.assertEqual(len(self.compiled.redirects), 11)
        self.assertEqual(len(self.compiled.holds), 54)
        for rule in self.compiled.redirects:
            decision = resolve(self.compiled, rule.path, "", "smartlic.tech")
            self.assertEqual(decision.status, REDIRECT_STATUS, rule.path)
            self.assertEqual(decision.location, rule.target_url, rule.path)
            self.assertEqual(decision.hops, 1, rule.path)
            host = urlsplit(decision.location).hostname
            self.assertEqual(host, TARGET_HOSTNAME, rule.path)
            self.assertNotEqual(decision.location, "https://confenge.com.br/")
            self.assertNotIn("/consultoria-b2g", decision.location)

    def test_payment_delay_resolver_uses_remapped_target(self) -> None:
        decision = resolve(
            self.compiled,
            "/blog/orgaos-risco-atraso-pagamento-licitacao",
            "",
            "smartlic.tech",
        )
        self.assertEqual(decision.status, REDIRECT_STATUS)
        self.assertEqual(
            decision.location,
            "https://confenge.com.br/conteudos/atraso-pagamento-contrato-publico-suspender/",
        )
        self.assertNotIn("/atrasos-prorrogacao-obras-publicas/", decision.location or "")
        self.assertEqual(decision.hops, 1)

    def test_www_alias_is_same_one_hop(self) -> None:
        for rule in self.compiled.redirects:
            apex = resolve(self.compiled, rule.path, "", "smartlic.tech")
            www = resolve(self.compiled, rule.path, "", "www.smartlic.tech")
            self.assertEqual(www.status, 301)
            self.assertEqual(www.location, apex.location)
            self.assertEqual(www.hops, 1)

    def test_trailing_slash_normalizes_to_same_rule(self) -> None:
        rule = self.compiled.redirects[0]
        slashed = resolve(self.compiled, rule.path + "/", "", "smartlic.tech")
        self.assertEqual(slashed.status, 301)
        self.assertEqual(slashed.location, rule.target_url)


class PolicyRetireAndNegativesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compiled = load_and_compile()

    def test_unmapped_is_410(self) -> None:
        decision = resolve(self.compiled, "/this-path-is-not-in-the-manifesto", "", "smartlic.tech")
        self.assertEqual(decision.status, DEFAULT_STATUS)
        self.assertIsNone(decision.location)
        self.assertEqual(decision.hops, 0)

    def test_api_auth_checkout_webhooks_are_410(self) -> None:
        paths = (
            "/v1/search",
            "/v1/health",
            "/login",
            "/signup",
            "/planos",
            "/pricing",
            "/webhooks/stripe",
            "/buscar",
            "/conta",
        )
        for path in paths:
            decision = resolve(self.compiled, path, "", "smartlic.tech")
            self.assertEqual(decision.status, DEFAULT_STATUS, path)
            self.assertIsNone(decision.location, path)

    def test_api_host_is_not_inventoried(self) -> None:
        rule = self.compiled.redirects[0]
        decision = resolve(self.compiled, rule.path, "", "api.smartlic.tech")
        self.assertEqual(decision.status, DEFAULT_STATUS)
        self.assertIsNone(decision.location)

    def test_root_is_410_not_home_redirect(self) -> None:
        decision = resolve(self.compiled, "/", "", "smartlic.tech")
        self.assertEqual(decision.status, DEFAULT_STATUS)
        self.assertIsNone(decision.location)

    def test_hold_paths_are_fail_closed_410(self) -> None:
        self.assertGreaterEqual(len(self.compiled.holds), 1)
        for path in self.compiled.holds:
            decision = resolve(self.compiled, path, "", "smartlic.tech")
            self.assertEqual(decision.status, DEFAULT_STATUS, path)
            self.assertIsNone(decision.location, path)
            self.assertEqual(decision.rule_id, "hold-fail-closed", path)
            self.assertEqual(decision.hops, 0, path)

    def test_pncp_hold_is_not_a_home_redirect(self) -> None:
        decision = resolve(
            self.compiled,
            "/blog/como-consultar-contratos-publicos-pncp",
            "",
            "smartlic.tech",
        )
        self.assertEqual(decision.status, 410)
        self.assertIsNone(decision.location)
        self.assertEqual(decision.rule_id, "hold-fail-closed")


class QueryAllowlistTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compiled = load_and_compile()
        cls.rule = cls.compiled.redirects[0]

    def test_allowlist_survives_and_pii_is_dropped(self) -> None:
        query = (
            "utm_source=gsc&utm_medium=organic&jornada=defesa"
            "&email=ada@example.com&phone=11999999999&name=Ada"
            "&cnpj=00000000000191&cpf=00000000000&token=secret&foo=bar"
        )
        decision = resolve(self.compiled, self.rule.path, query, "smartlic.tech")
        self.assertEqual(decision.status, 301)
        assert decision.location is not None
        self.assertTrue(decision.location.startswith(self.rule.target_url))
        qs = parse_qs(urlsplit(decision.location).query)
        self.assertEqual(qs.get("utm_source"), ["gsc"])
        self.assertEqual(qs.get("utm_medium"), ["organic"])
        self.assertEqual(qs.get("jornada"), ["defesa"])
        for forbidden in ("email", "phone", "name", "cnpj", "cpf", "token", "foo"):
            self.assertNotIn(forbidden, qs)
            self.assertNotIn(f"{forbidden}=", decision.location)

    def test_filter_query_uses_compiled_persist_list(self) -> None:
        kept = filter_query("origem=site&route_family=x&evil=1", self.compiled.persist)
        parsed = parse_qs(kept)
        self.assertEqual(parsed.get("origem"), ["site"])
        self.assertEqual(parsed.get("route_family"), ["x"])
        self.assertNotIn("evil", parsed)


if __name__ == "__main__":
    unittest.main()
