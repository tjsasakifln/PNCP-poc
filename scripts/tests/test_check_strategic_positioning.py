"""Regression tests for the shipped strategic-positioning checker.

Drives scripts/check_strategic_positioning.py and its public functions.
Does not re-implement matching logic inside the test.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import check_strategic_positioning as checker  # noqa: E402

_CANONICAL_FOR_TREE = [
    "README.md",
    "PRD.md",
    "ROADMAP.md",
    "CLAUDE.md",
    "docs/DEPLOYMENT.md",
    "docs/architecture/system-architecture.md",
    "frontend/public/llms.txt",
    "docs/adr/ADR-STRAT-001-smartlic-confenge-inbound.md",
    "docs/strategy/critical-path.md",
    "docs/strategy/runtime-destination.md",
    "docs/strategy/capability-disposition-1262.md",
    "docs/strategy/strategic-positioning-policy.json",
]


class FindAffirmativeHitsTests(unittest.TestCase):
    def test_negated_stripe_live_billing_is_not_a_hit(self):
        text = "SmartLic não usa Stripe live billing e não vende assinatura."
        self.assertEqual(checker.find_affirmative_hits(r"Stripe live billing", text), [])

    def test_english_negation_stripe_is_not_a_hit(self):
        text = "SmartLic does not use Stripe live billing."
        self.assertEqual(checker.find_affirmative_hits(r"Stripe live billing", text), [])

    def test_negated_saas_is_not_a_hit(self):
        text = "O SmartLic não é um SaaS independente."
        self.assertEqual(checker.find_affirmative_hits(r"SaaS independente", text), [])

    def test_historical_plataforma_saas_is_not_a_hit(self):
        text = "Histórico: a empresa descrevia o produto como plataforma SaaS."
        self.assertEqual(checker.find_affirmative_hits(r"plataforma SaaS", text), [])

    def test_affirmative_stripe_live_billing_is_a_hit(self):
        text = "Production uses Stripe live billing for all plans."
        self.assertEqual(
            checker.find_affirmative_hits(r"Stripe live billing", text),
            [r"Stripe live billing"],
        )

    def test_affirmative_plataforma_saas_is_a_hit(self):
        text = "SmartLic é a plataforma SaaS de licitações."
        self.assertEqual(
            checker.find_affirmative_hits(r"plataforma SaaS", text),
            [r"plataforma SaaS"],
        )


class EvaluateTreeTests(unittest.TestCase):
    def _copy_canonical(self, dest: Path) -> None:
        for rel in _CANONICAL_FOR_TREE:
            src = ROOT / rel
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, target)

    def test_real_tree_evaluate_is_clean(self):
        errors = checker.evaluate(ROOT)
        self.assertEqual(errors, [], msg=errors)

    def test_injected_affirmative_saas_fails_evaluate(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            self._copy_canonical(dest)
            readme = dest / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8") + "\n\nStripe live billing\n",
                encoding="utf-8",
            )
            errors = checker.evaluate(dest)
            self.assertTrue(
                any("Stripe live billing" in e for e in errors),
                msg=errors,
            )

    def test_injected_negation_does_not_fail_evaluate(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            self._copy_canonical(dest)
            readme = dest / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8")
                + "\n\nO produto não usa Stripe live billing.\n",
                encoding="utf-8",
            )
            errors = checker.evaluate(dest)
            self.assertEqual(errors, [], msg=errors)


class ShippedScriptTests(unittest.TestCase):
    def test_script_entry_point_on_real_tree_exits_0(self):
        script = ROOT / "scripts" / "check_strategic_positioning.py"
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout={result.stdout!r} stderr={result.stderr!r}",
        )
        self.assertIn("Strategic positioning check passed", result.stdout)


class WorkflowTriggerTests(unittest.TestCase):
    def test_workflow_pins_checkout_sha_and_canonical_paths(self):
        workflow = (
            ROOT / ".github" / "workflows" / "strategic-positioning-check.yml"
        ).read_text(encoding="utf-8")
        self.assertRegex(
            workflow,
            r"uses:\s+actions/checkout@[0-9a-f]{40}",
        )
        self.assertIn("persist-credentials: false", workflow)
        for path in (
            "CLAUDE.md",
            "docs/DEPLOYMENT.md",
            "docs/architecture/system-architecture.md",
        ):
            self.assertIn(path, workflow)

    def test_policy_workflow_paths_cover_canonical_docs(self):
        policy = json.loads(
            (ROOT / "docs" / "strategy" / "strategic-positioning-policy.json").read_text(
                encoding="utf-8"
            )
        )
        paths = policy["workflow_paths"]
        for required in (
            "CLAUDE.md",
            "docs/DEPLOYMENT.md",
            "docs/architecture/system-architecture.md",
        ):
            self.assertIn(required, paths)

    def test_policy_is_what_the_script_loads(self):
        loaded = checker.load_policy(ROOT)
        self.assertEqual(loaded["adr"], "ADR-STRAT-002")
        self.assertEqual(checker.policy_path(ROOT), ROOT / checker.POLICY_REL)


if __name__ == "__main__":
    unittest.main()
