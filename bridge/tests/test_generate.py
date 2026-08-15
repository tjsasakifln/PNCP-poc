"""Drive the shipped generator against the pinned manifesto bytes."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bridge.errors import ManifestError
from bridge.generate import (
    _map_payload,
    assert_pinned_hash,
    assert_terminator_safe,
    emit,
    empty_retire_map,
    load_and_compile,
    load_manifest_bytes,
    main as generate_main,
    probe_targets,
    rollback,
    sha256_bytes,
    validate_schema,
)
from bridge.policy import CompiledMap, RedirectRule
from bridge.pins import (
    CITED_MANIFESTO_COMMIT,
    PINNED_COMMIT,
    PINNED_CONFIG_SHA256,
    PINNED_REDIRECT_COUNT,
    PINNED_SHA256,
    REDIRECT_STATUS,
    DEFAULT_STATUS,
)


class GeneratePinnedManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = load_manifest_bytes()
        cls.compiled = load_and_compile()

    def test_pinned_hash_matches_consumed_bytes(self) -> None:
        digest = assert_pinned_hash(self.raw)
        self.assertEqual(digest, PINNED_SHA256)
        self.assertEqual(sha256_bytes(self.raw), PINNED_SHA256)
        self.assertEqual(self.compiled.manifesto_sha256, PINNED_SHA256)
        self.assertEqual(self.compiled.config_sha256, PINNED_CONFIG_SHA256)

    def test_cited_rebase_commit_is_not_baked_into_config_hash(self) -> None:
        payload = _map_payload(self.compiled)
        self.assertEqual(payload["pinned_commit"], PINNED_COMMIT)
        self.assertEqual(payload["pinned_commit"], "3f112bfbd9e6b042691e1c09812af00f42735adb")
        self.assertNotEqual(CITED_MANIFESTO_COMMIT, PINNED_COMMIT)
        self.assertNotIn(CITED_MANIFESTO_COMMIT, payload["pinned_commit"])
        self.assertEqual(self.compiled.config_sha256, PINNED_CONFIG_SHA256)

    def test_dirty_bytes_are_rejected(self) -> None:
        dirty = self.raw + b"\n"
        with self.assertRaises(ManifestError) as ctx:
            assert_pinned_hash(dirty)
        self.assertIn("diverge", str(ctx.exception))

    def test_execute_set_is_exactly_the_ready_redirects(self) -> None:
        data = json.loads(self.raw)
        ready = [
            entry
            for entry in data["entries"]
            if entry["decision"] == "REDIRECT" and entry["status"] == "ready"
        ]
        self.assertEqual(len(ready), PINNED_REDIRECT_COUNT)
        self.assertEqual(len(self.compiled.redirects), PINNED_REDIRECT_COUNT)
        compiled_paths = {rule.path for rule in self.compiled.redirects}
        for entry in ready:
            from urllib.parse import urlsplit

            from bridge.policy import normalize_path

            path = normalize_path(urlsplit(entry["legacy_url"]).path)
            self.assertIn(path, compiled_paths)
            rule = self.compiled.by_path[path]
            self.assertEqual(rule.target_url, entry["target_url"])
            self.assertEqual(rule.expected_http, REDIRECT_STATUS)
            self.assertEqual(rule.expected_canonical, entry["expected_canonical"])
            self.assertTrue(rule.target_url.startswith("https://confenge.com.br/"))
            self.assertNotEqual(rule.target_url, "https://confenge.com.br/")
            self.assertNotIn("/consultoria-b2g", rule.target_url)

    def test_no_wildcard_or_home_rule(self) -> None:
        for rule in self.compiled.redirects:
            self.assertNotIn("*", rule.path)
            self.assertNotEqual(rule.path, "/")
            self.assertNotIn("/*", rule.path)

    def test_emit_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            a = emit(self.compiled, Path(first))
            b = emit(self.compiled, Path(second))
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertEqual(
                (Path(first) / "config.sha256").read_text(encoding="utf-8"),
                (Path(second) / "config.sha256").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                (Path(first) / "config.sha256").read_text(encoding="utf-8").strip(),
                self.compiled.config_sha256,
            )
            caddy = (Path(first) / "Caddyfile").read_text(encoding="utf-8")
            assert_terminator_safe(caddy)
            self.assertIn("reverse_proxy 127.0.0.1:8765", caddy)
            self.assertIn("smartlic.tech", caddy)
            self.assertIn("www.smartlic.tech", caddy)
            self.assertIn("{$SMARTLIC_ACME_EMAIL}", caddy)
            self.assertIn("auto_https disable_redirects", caddy)
            from bridge.generate import URI_QUERY_STRIP

            self.assertIn(URI_QUERY_STRIP, caddy)
            self.assertNotIn("request>uri query", caddy)
            self.assertNotIn("reverse_proxy 127.0.0.1:8000", caddy)
            self.assertNotIn("reverse_proxy 127.0.0.1:3000", caddy)
            self.assertNotIn("BEGIN PRIVATE KEY", caddy)
            self.assertNotRegex(caddy, r"redir\s+/\*")

    def test_generated_map_contains_only_approved_redirects(self) -> None:
        payload = json.loads((emit(self.compiled, Path(tempfile.mkdtemp()))).read_text(encoding="utf-8"))
        self.assertEqual(payload["default_status"], DEFAULT_STATUS)
        self.assertEqual(len(payload["redirects"]), PINNED_REDIRECT_COUNT)
        self.assertEqual(payload["manifesto_sha256"], PINNED_SHA256)


class FailClosedSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(load_manifest_bytes())

    def _redirect(self) -> dict:
        return next(entry for entry in self.data["entries"] if entry["decision"] == "REDIRECT")

    def test_missing_version_fails(self) -> None:
        data = json.loads(json.dumps(self.data))
        data["meta"]["version"] = ""
        with self.assertRaises(ManifestError):
            validate_schema(data)

    def test_duplicate_legacy_fails(self) -> None:
        data = json.loads(json.dumps(self.data))
        clone = json.loads(json.dumps(self._redirect()))
        data["entries"].append(clone)
        with self.assertRaises(ManifestError) as ctx:
            validate_schema(data)
        self.assertRegex(str(ctx.exception), "duplicata|contagem")

    def test_generic_home_target_fails(self) -> None:
        data = json.loads(json.dumps(self.data))
        for entry in data["entries"]:
            if entry["decision"] == "REDIRECT":
                entry["target_url"] = "https://confenge.com.br/"
                entry["expected_canonical"] = "https://confenge.com.br/"
                break
        with self.assertRaises(ManifestError) as ctx:
            validate_schema(data)
        self.assertRegex(str(ctx.exception), "genérico|inseguro|home")

    def test_consultoria_fallback_target_fails(self) -> None:
        data = json.loads(json.dumps(self.data))
        for entry in data["entries"]:
            if entry["decision"] == "REDIRECT":
                entry["target_url"] = "https://confenge.com.br/consultoria-b2g/"
                entry["expected_canonical"] = "https://confenge.com.br/consultoria-b2g/"
                break
        with self.assertRaises(ManifestError) as ctx:
            validate_schema(data)
        self.assertRegex(str(ctx.exception), "genérico|inseguro")

    def test_wildcard_legacy_fails(self) -> None:
        data = json.loads(json.dumps(self.data))
        for entry in data["entries"]:
            if entry["decision"] == "REDIRECT":
                entry["legacy_url"] = "https://smartlic.tech/*"
                break
        with self.assertRaises(ManifestError) as ctx:
            validate_schema(data)
        self.assertIn("wildcard", str(ctx.exception))

    def test_lookalike_legacy_origins_fail(self) -> None:
        for unsafe in (
            "https://smartlic.tech.attacker.invalid/path",
            "https://smartlic.tech@attacker.invalid/path",
            "https://smartlic.tech:444/path",
            "https://smartlic.tech/path?token=secret",
        ):
            with self.subTest(unsafe=unsafe):
                data = json.loads(json.dumps(self.data))
                redirect = next(
                    entry for entry in data["entries"] if entry["decision"] == "REDIRECT"
                )
                redirect["legacy_url"] = unsafe
                with self.assertRaises(ManifestError):
                    validate_schema(data)

    def test_http_target_fails(self) -> None:
        data = json.loads(json.dumps(self.data))
        for entry in data["entries"]:
            if entry["decision"] == "REDIRECT":
                entry["target_url"] = entry["target_url"].replace("https://", "http://")
                break
        with self.assertRaises(ManifestError):
            validate_schema(data)

    def test_redirect_not_ready_fails(self) -> None:
        data = json.loads(json.dumps(self.data))
        for entry in data["entries"]:
            if entry["decision"] == "REDIRECT":
                entry["status"] = "blocked"
                break
        with self.assertRaises(ManifestError):
            validate_schema(data)


class RollbackTests(unittest.TestCase):
    def test_rollback_restores_previous_without_product_runtime(self) -> None:
        compiled = load_and_compile()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            emit(compiled, root)
            emit(empty_retire_map(), root / "previous")
            restored = rollback(root)
            payload = json.loads(restored.read_text(encoding="utf-8"))
            self.assertEqual(payload["redirects"], [])
            self.assertEqual(payload["default_status"], DEFAULT_STATUS)
            from bridge.generate import compiled_from_map_file
            from bridge.policy import resolve

            rolled = compiled_from_map_file(restored)
            ready_path = compiled.redirects[0].path
            decision = resolve(rolled, ready_path, "", "smartlic.tech")
            self.assertEqual(decision.status, 410)
            self.assertIsNone(decision.location)

    def test_rollback_cli_against_previous_is_410_only(self) -> None:
        compiled = load_and_compile()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            emit(compiled, root)
            emit(empty_retire_map(), root / "previous")
            rc = generate_main(["--out", str(root), "--rollback"])
            self.assertEqual(rc, 0)
            from bridge.generate import compiled_from_map_file
            from bridge.policy import resolve

            rolled = compiled_from_map_file(root / "bridge-map.json")
            self.assertEqual(rolled.redirects, ())
            for rule in compiled.redirects:
                decision = resolve(rolled, rule.path, "", "smartlic.tech")
                self.assertEqual(decision.status, 410, rule.path)
                self.assertIsNone(decision.location, rule.path)


class ProbeTargetsTests(unittest.TestCase):
    def test_ready_targets_are_https_200(self) -> None:
        compiled = load_and_compile()
        probe_targets(compiled)

    def test_unavailable_ready_target_fails_closed(self) -> None:
        compiled = load_and_compile()
        bad = RedirectRule(
            path="/glossario/reajuste",
            target_url="https://confenge.com.br/this-path-must-not-exist-2115-probe/",
            expected_canonical="https://confenge.com.br/this-path-must-not-exist-2115-probe/",
            family="probe",
            owner="test",
            persist=compiled.persist,
            expected_http=301,
        )
        mutated = CompiledMap(
            manifesto_sha256=compiled.manifesto_sha256,
            config_sha256=compiled.config_sha256,
            persist=compiled.persist,
            redirects=(bad,),
            by_path={bad.path: bad},
            default_status=compiled.default_status,
        )
        with self.assertRaises(ManifestError) as ctx:
            probe_targets(mutated)
        self.assertIn("indisponível", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
