"""Objective canary gate for a single public_read_v1 family.

Global PUBLIC_READ_V1_MODE=on is never implied by this module.
Promotion of `tenders` requires every check below.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

CANARY_FAMILY = "tenders"

# Residual reconciliation allowed before serving public tenders.
MAX_NON_BLOCKING_DIVERGENCES = 2


@dataclass
class CanaryCheck:
    name: str
    passed: bool
    detail: str


@dataclass
class CanaryDecision:
    family: str
    promote: bool
    checks: list[CanaryCheck] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "family": self.family,
            "promote": self.promote,
            "checks": [
                {"name": item.name, "passed": item.passed, "detail": item.detail}
                for item in self.checks
            ],
        }


def canary_family_allowed(family: str) -> bool:
    return family == CANARY_FAMILY


def evaluate_canary_gate(
    *,
    family: str,
    contract_ok: bool,
    blocking_divergences: int,
    classified_divergences: int,
    credential_leak_count: int,
    isolation_ok: bool,
    last_known_good_ok: bool,
    seo_regression: bool,
    rollback_ok: bool,
    query_budget_ok: bool,
    no_write_ok: bool,
) -> CanaryDecision:
    checks = [
        CanaryCheck("family_is_tenders", family == CANARY_FAMILY, family),
        CanaryCheck("contract_tests", contract_ok, "producer/consumer contract"),
        CanaryCheck(
            "no_blocking_divergence",
            blocking_divergences == 0,
            f"blocking={blocking_divergences}",
        ),
        CanaryCheck(
            "reconciliation_threshold",
            classified_divergences <= MAX_NON_BLOCKING_DIVERGENCES,
            f"classified={classified_divergences} max={MAX_NON_BLOCKING_DIVERGENCES}",
        ),
        CanaryCheck(
            "zero_credential",
            credential_leak_count == 0,
            f"leaks={credential_leak_count}",
        ),
        CanaryCheck("isolation_budgets", isolation_ok, "backpressure fail-closed"),
        CanaryCheck("query_budgets", query_budget_ok, "statement/lock/pool"),
        CanaryCheck("no_write", no_write_ok, "SELECT-only role"),
        CanaryCheck("last_known_good", last_known_good_ok, "LKG path proven"),
        CanaryCheck("seo_clean", not seo_regression, "no unexpected 404/500"),
        CanaryCheck("rollback_proven", rollback_ok, "mode=off restores legacy"),
        CanaryCheck(
            "global_mode_not_on",
            os.getenv("PUBLIC_READ_V1_MODE", "off").strip().lower() != "on",
            os.getenv("PUBLIC_READ_V1_MODE", "off"),
        ),
    ]
    return CanaryDecision(
        family=family,
        promote=all(item.passed for item in checks),
        checks=checks,
    )
