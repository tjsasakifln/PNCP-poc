"""Structural check of the shipped #2111 decommission plan.

Does not delete anything. Drives the real file in docs/strategy/.
"""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "docs" / "strategy" / "decommission-plan-2111.md"
ALLOWED = {"MIGRATE", "RETIRE", "KEEP_UNTIL_REDIRECT_WINDOW", "UNKNOWN"}
FAMILIES = (
    "## 1. Jobs",
    "## 2. Secrets / credentials (names only)",
    "## 3. Stores",
    "## 4. Domains / DNS / TLS",
    "## 5. Webhooks",
    "## 6. Billing",
    "## 7. Auth",
    "## 8. PII retention",
    "## Zero-use evidence plan",
)


class DecommissionPlan2111Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = PLAN.read_text(encoding="utf-8")

    def test_plan_file_is_shipped(self) -> None:
        self.assertTrue(PLAN.is_file(), PLAN)

    def test_every_family_heading_is_present(self) -> None:
        missing = [h for h in FAMILIES if h not in self.text]
        self.assertEqual(missing, [])

    def test_class_vocabulary_is_only_the_allowed_set(self) -> None:
        for token in ALLOWED:
            self.assertIn(f"`{token}`", self.text)
        self.assertNotIn("SUNSET NOW", self.text)
        self.assertNotIn("KEEP + ADAPT", self.text)

    def test_campaign_class_mapping_is_explicit(self) -> None:
        for token in ("KEEP_TEMP_BRIDGE", "MIGRATED", "LEGAL_RETENTION"):
            self.assertIn(f"`{token}`", self.text)
        self.assertIn("Campaign class mapping", self.text)
        self.assertIn("## Execution 2026-08-15", self.text)

    def test_zero_use_plan_covers_every_family(self) -> None:
        table = self.text.split("## Zero-use evidence plan", 1)[1]
        for family in ("Jobs", "Secrets", "Stores", "Domains", "Webhooks", "Billing", "Auth", "PII"):
            self.assertIn(family, table, family)

    def test_plan_forbids_destructive_action(self) -> None:
        self.assertIn("Nothing listed here is removed", self.text)
        self.assertIn("Does not delete jobs, secrets, stores, domains, webhooks, or hosting.", self.text)
