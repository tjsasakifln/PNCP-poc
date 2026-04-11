"""CRIT-004 + STORY-414: Schema contract for critical tables.

Defines the minimum required schema for the application to operate.
Critical tables block startup if schema diverges **when
``SCHEMA_CONTRACT_STRICT=true``**; otherwise the gate is passive and
only logs CRITICAL warnings (the pre-STORY-414 behaviour).

Rollout plan (STORY-414, decided 2026-04-10):
    * P1 (Dia 0):   STRICT=false in production, STRICT=true in staging.
    * P2 (Dia 1-7): observe staging — zero false positives PGRST002.
    * P3 (Dia 7-14): add PGRST002 retries if needed, monitor.
    * P4 (Dia 14):  flip production in a quiet window.

Moved from backend/schema_contract.py as part of DEBT-208 schema consolidation.
"""
import logging
import time
from typing import Tuple

logger = logging.getLogger(__name__)

CRITICAL_SCHEMA: dict[str, list[str]] = {
    "search_sessions": [
        "id", "user_id", "search_id", "status", "started_at",
        "completed_at", "created_at",
    ],
    "search_results_cache": [
        "id", "params_hash", "results", "created_at",
    ],
    "profiles": [
        "id", "plan_type", "email",
    ],
}

OPTIONAL_RPCS: list[str] = [
    "get_table_columns_simple",
]

_last_warning_time: dict[str, float] = {}
WARNING_INTERVAL_SECONDS = 300  # 5 minutes

# STORY-414: Cached last-known validation result used by the admin endpoint
# /admin/schema-contract-status so it can return quickly without hammering
# Supabase on every poll. Refreshed by enforce_schema_contract() at startup
# and by the admin endpoint when older than STATUS_CACHE_TTL seconds.
_last_status: dict[str, object] = {
    "passed": None,
    "missing": [],
    "checked_at": 0.0,
    "strict_mode": False,
}
STATUS_CACHE_TTL = 300  # 5 minutes


def validate_schema_contract(db) -> tuple[bool, list[str]]:
    """Validate critical schema contract against the database.

    Returns:
        (passed, missing_items): True if all critical columns exist.
        missing_items format: ["table.column", ...]
    """
    missing_items: list[str] = []

    for table_name, required_columns in CRITICAL_SCHEMA.items():
        try:
            # Try RPC first
            try:
                result = db.rpc(
                    "get_table_columns_simple",
                    {"p_table_name": table_name},
                ).execute()
                actual_columns = {row["column_name"] for row in result.data} if result.data else set()
            except Exception:
                # RPC not available — try direct query fallback
                result = db.table(table_name).select("*").limit(0).execute()
                # If the table exists, we can't easily get columns without RPC
                # but at least we know the table exists
                logger.warning(
                    f"CRIT-004: RPC unavailable, cannot validate columns for {table_name} "
                    f"(table exists but column check skipped)"
                )
                continue

            for col in required_columns:
                if col not in actual_columns:
                    missing_items.append(f"{table_name}.{col}")

        except Exception as e:
            # Table doesn't exist at all
            for col in required_columns:
                missing_items.append(f"{table_name}.{col}")
            logger.error(f"CRIT-004: Table {table_name} check failed: {e}")

    passed = len(missing_items) == 0
    return passed, missing_items


def emit_degradation_warning(component: str, message: str) -> None:
    """Emit a recurring degradation warning (max once per 5 minutes per component)."""
    now = time.time()
    last = _last_warning_time.get(component, 0)
    if now - last >= WARNING_INTERVAL_SECONDS:
        logger.warning(f"CRIT-004: {component} — {message}")
        _last_warning_time[component] = now


class SchemaContractViolation(RuntimeError):
    """STORY-414: Raised when the schema contract is violated and the gate
    is running in strict mode. Carries the list of missing items so the
    admin endpoint and Sentry can surface the exact delta.
    """

    def __init__(self, missing: list[str]) -> None:
        self.missing = missing
        super().__init__(
            f"Schema contract violated — missing items: {missing}. "
            "Set SCHEMA_CONTRACT_STRICT=false to unblock startup while "
            "migrations catch up."
        )


def enforce_schema_contract(db, *, strict: bool | None = None) -> Tuple[bool, list[str]]:
    """STORY-414: Wrapper around ``validate_schema_contract`` that honours
    the ``SCHEMA_CONTRACT_STRICT`` feature flag and updates the status
    cache consumed by the admin endpoint.

    Args:
        db: Supabase client (admin — service_role).
        strict: Override the feature flag (useful for tests). When None,
            reads ``SCHEMA_CONTRACT_STRICT`` via ``get_feature_flag``.

    Returns:
        ``(passed, missing)``. When strict=True and passed=False, raises
        ``SchemaContractViolation`` after updating the cache and logs.
    """
    if strict is None:
        try:
            from config.features import get_feature_flag

            strict = get_feature_flag("SCHEMA_CONTRACT_STRICT", default=False)
        except Exception:
            # Import cycle / unit-test path — fall back to passive mode.
            strict = False

    passed, missing = validate_schema_contract(db)
    _last_status.update(
        {
            "passed": passed,
            "missing": missing,
            "checked_at": time.time(),
            "strict_mode": bool(strict),
        }
    )

    if passed:
        logger.info(
            "STORY-414: Schema contract validated — 0 missing columns "
            "(strict=%s)",
            strict,
        )
        return True, []

    logger.critical(
        "STORY-414: SCHEMA CONTRACT VIOLATED — missing %s (strict=%s). "
        "Run migrations immediately.",
        missing,
        strict,
    )
    if strict:
        raise SchemaContractViolation(missing)
    return False, missing


def get_last_status() -> dict:
    """STORY-414: Return a JSON-safe copy of the last validation result.

    Used by ``GET /admin/schema-contract-status`` so ops can poll without
    hammering Supabase (the cache is refreshed at startup and stays warm
    for ``STATUS_CACHE_TTL`` seconds). The dict is safe to json.dumps.
    """
    status = dict(_last_status)
    status["stale"] = (time.time() - float(status.get("checked_at") or 0)) > STATUS_CACHE_TTL
    return status


def _main() -> None:  # pragma: no cover
    """CLI entry-point: ``python -m backend.schemas.contract --validate``

    Validates the schema contract against Supabase and exits with:
      0 — contract passes (all critical columns present)
      1 — contract violated (missing columns printed to stderr)
      2 — configuration error (missing env vars or import failure)

    Required env vars:
      SUPABASE_URL (or NEXT_PUBLIC_SUPABASE_URL)
      SUPABASE_SERVICE_ROLE_KEY

    Intended for use in CI after ``supabase db push`` to catch schema
    drift before it reaches production (STORY-414 AC3).
    """
    import argparse
    import os
    import sys

    parser = argparse.ArgumentParser(
        prog="python -m backend.schemas.contract",
        description="Validate SmartLic schema contract against Supabase.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        required=True,
        help="Run validation and exit 0 (pass) / 1 (violated) / 2 (config error).",
    )
    parser.parse_args()

    supabase_url = os.environ.get("SUPABASE_URL") or os.environ.get(
        "NEXT_PUBLIC_SUPABASE_URL"
    )
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not service_role_key:
        print(
            "ERROR: SUPABASE_URL (or NEXT_PUBLIC_SUPABASE_URL) and "
            "SUPABASE_SERVICE_ROLE_KEY must be set.",
            file=sys.stderr,
        )
        sys.exit(2)

    try:
        from supabase import create_client  # type: ignore[import]
    except ImportError:
        print(
            "ERROR: supabase package not installed. Run: pip install supabase",
            file=sys.stderr,
        )
        sys.exit(2)

    try:
        db = create_client(supabase_url, service_role_key)
        passed, missing = validate_schema_contract(db)
    except Exception as exc:
        print(f"ERROR: Schema contract check raised an exception: {exc}", file=sys.stderr)
        sys.exit(2)

    if not passed:
        print("SCHEMA CONTRACT VIOLATED — missing columns:", file=sys.stderr)
        for item in missing:
            print(f"  - {item}", file=sys.stderr)
        print(
            "\nTo resolve: apply pending migrations and redeploy.\n"
            "  supabase db push --include-all",
            file=sys.stderr,
        )
        sys.exit(1)

    table_count = len(CRITICAL_SCHEMA)
    col_count = sum(len(v) for v in CRITICAL_SCHEMA.values())
    print(
        f"Schema contract OK — {table_count} tables / {col_count} columns checked, "
        "0 missing."
    )
    sys.exit(0)


if __name__ == "__main__":
    _main()
