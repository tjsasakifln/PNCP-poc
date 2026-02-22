"""CRIT-004: Schema contract for critical tables.

Defines the minimum required schema for the application to operate.
Critical tables block startup if schema diverges.
Optional RPCs degrade gracefully with recurring warnings.
"""
import logging
import time

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
