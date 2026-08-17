"""Table-drive every pinned inventory v2 row through the shipped evaluator."""

from __future__ import annotations

import json
import unittest
from collections import Counter
from urllib.parse import urlsplit

from bridge.generate import assert_pinned_hash, load_and_compile, load_manifest_bytes
from bridge.pins import (
    PINNED_CONFIG_SHA256,
    PINNED_HOLD_COUNT,
    PINNED_REDIRECT_COUNT,
    PINNED_RETIRE_COUNT,
    PINNED_SHA256,
    REDIRECT_DECISIONS,
)
from bridge.policy import normalize_path, resolve
from bridge.tests._evidence import write_evidence
from bridge.tests._harness import assert_decision_matches, expected_action


class InventoryOracleTests(unittest.TestCase):
    """Manifesto bytes are the oracle. resolve() is the only unit under test."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = load_manifest_bytes()
        cls.digest = assert_pinned_hash(cls.raw)
        cls.data = json.loads(cls.raw)
        cls.compiled = load_and_compile()
        cls.entries = cls.data["entries"]

    def test_pin_and_counts_match_inventory_v2(self) -> None:
        self.assertEqual(self.digest, PINNED_SHA256)
        self.assertEqual(self.compiled.manifesto_sha256, PINNED_SHA256)
        self.assertEqual(self.compiled.config_sha256, PINNED_CONFIG_SHA256)
        self.assertEqual(len(self.entries), 1255)
        counts = Counter(entry["decision"] for entry in self.entries)
        self.assertEqual(counts["REDIRECT_301"], PINNED_REDIRECT_COUNT)
        self.assertEqual(counts["HOLD_TARGET_NOT_READY"], PINNED_HOLD_COUNT)
        self.assertEqual(counts["RETIRE_410"], PINNED_RETIRE_COUNT)
        self.assertEqual(sum(counts.values()), 1255)
        self.assertEqual(len(self.compiled.redirects), PINNED_REDIRECT_COUNT)
        self.assertEqual(len(self.compiled.holds), PINNED_HOLD_COUNT)

    def test_every_inventory_row_produces_the_pinned_action(self) -> None:
        rows: list[dict[str, object]] = []
        mismatches: list[str] = []
        action_counts: Counter[str] = Counter()
        for entry in self.entries:
            path = normalize_path(urlsplit(entry["legacy_url"]).path)
            expected_status, expected_location = expected_action(entry)
            decision = resolve(self.compiled, path, "", "smartlic.tech")
            label = f"{entry['decision']} {path}"
            try:
                assert_decision_matches(
                    decision, expected_status, expected_location, label=label
                )
            except AssertionError as exc:
                mismatches.append(str(exc))
            action_counts[str(entry["decision"])] += 1
            rows.append(
                {
                    "decision": entry["decision"],
                    "expected_http": expected_status,
                    "family": entry.get("family"),
                    "legacy_path": path,
                    "location": decision.location,
                    "rule_id": decision.rule_id,
                    "status": decision.status,
                }
            )
            with self.subTest(path=path, decision=entry["decision"]):
                assert_decision_matches(
                    decision, expected_status, expected_location, label=label
                )
                if entry["decision"] in REDIRECT_DECISIONS:
                    self.assertEqual(decision.location, entry["target_url"])
                    self.assertEqual(decision.location, entry["expected_canonical"])
                else:
                    self.assertIsNone(decision.location)
                    self.assertEqual(decision.status, 410)

        default = resolve(self.compiled, "/not-mapped", "", "smartlic.tech")
        assert_decision_matches(default, 410, None, label="default /not-mapped")
        rows.append(
            {
                "decision": "DEFAULT_UNMAPPED",
                "expected_http": 410,
                "family": "retire",
                "legacy_path": "/not-mapped",
                "location": default.location,
                "rule_id": default.rule_id,
                "status": default.status,
            }
        )
        write_evidence(
            "inventory-actions.json",
            {
                "action_counts": dict(action_counts),
                "config_sha256": self.compiled.config_sha256,
                "default": {"location": default.location, "status": default.status},
                "manifesto_sha256": self.compiled.manifesto_sha256,
                "mismatches": mismatches,
                "n_rows": len(self.entries),
                "rows": rows,
            },
        )
        self.assertEqual(mismatches, [])
        self.assertEqual(action_counts["REDIRECT_301"], 11)
        self.assertEqual(action_counts["HOLD_TARGET_NOT_READY"], 54)
        self.assertEqual(action_counts["RETIRE_410"], 1190)


if __name__ == "__main__":
    unittest.main()
