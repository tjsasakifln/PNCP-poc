#!/usr/bin/env python3
"""STORY-2.8 (TD-DB-011) EPIC-TD-2026Q2: deduplicate profiles with the same email.

Groups public.profiles by LOWER(email), identifies clusters with count > 1,
picks a winner via a deterministic heuristic, re-points all FK rows from
losers to winner, soft-deletes the losers, and writes an entry to
public.audit_events for each merge.

Safety rails:
  * DRY-RUN by default — no writes unless both ``--execute`` AND env var
    ``CONFIRM_DEDUP=YES`` are set.
  * Even in execute mode, all writes for a single cluster are wrapped in
    a try/except so one bad cluster doesn't abort the whole run.
  * Every run produces a CSV under docs/audit/ for human review — written
    BEFORE any mutation so operators have the plan on disk even if execution
    fails halfway.
  * Soft-delete only: losers are tagged with deleted_at, deleted_reason,
    migrated_to so auth.users FKs stay intact.

Winner heuristic (most-recent-and-most-valuable wins):
  1. Highest last_sign_in_at (most recently active user).
  2. Tiebreak: has a stripe_customer_id via user_subscriptions (paying).
  3. Tiebreak: oldest created_at (original account).
  4. Tiebreak: smallest UUID (deterministic).

Usage:
    # Dry run (default) — inspects DB, writes CSV, NO writes
    python scripts/dedup_profiles_email.py

    # Real run — requires BOTH flags to execute
    CONFIRM_DEDUP=YES python scripts/dedup_profiles_email.py --execute

    # Custom output dir
    python scripts/dedup_profiles_email.py --output-dir /tmp/audit
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add backend/ to sys.path so local imports work when running from project root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("dedup_profiles_email")


# ---------------------------------------------------------------------------
# Config / constants
# ---------------------------------------------------------------------------

# Tables whose user_id column references profiles.id and must be re-pointed
# to the winner before the loser is soft-deleted.
FK_TABLES_USER_ID: tuple[str, ...] = (
    "user_subscriptions",
    "search_sessions",
    "pipeline_items",
    "classification_feedback",
)

CONFIRM_ENV = "CONFIRM_DEDUP"
CONFIRM_VALUE = "YES"

# ---------------------------------------------------------------------------
# Supabase helpers
# ---------------------------------------------------------------------------


def _get_client() -> Any:
    """Return an admin Supabase client (service_role)."""
    from supabase_client import get_supabase  # local import so tests can patch

    return get_supabase()


def _hash_id(user_id: str) -> str | None:
    """SHA-256 hash truncated to 16 hex chars — matches audit_events schema."""
    if not user_id:
        return None
    return hashlib.sha256(str(user_id).encode("utf-8")).hexdigest()[:16]


def _fetch_all_profiles(sb: Any) -> list[dict]:
    """Page through profiles, collecting id/email/metadata.

    We intentionally avoid SQL-level grouping (no RPC for this) so the script
    works with plain PostgREST access.
    """
    rows: list[dict] = []
    page_size = 1000
    offset = 0
    select_cols = (
        "id,email,created_at,plan_type,deleted_at,"
        "last_sign_in_at,stripe_customer_id"
    )
    while True:
        try:
            resp = (
                sb.table("profiles")
                .select(select_cols)
                .range(offset, offset + page_size - 1)
                .execute()
            )
        except Exception as exc:
            # Some environments may not have last_sign_in_at / stripe_customer_id
            # columns on profiles directly; fall back to a narrower select.
            logger.warning(
                "fetch: narrow select (missing cols?) — %s: %s",
                type(exc).__name__,
                exc,
            )
            resp = (
                sb.table("profiles")
                .select("id,email,created_at,plan_type,deleted_at")
                .range(offset, offset + page_size - 1)
                .execute()
            )
        data = resp.data or []
        if not data:
            break
        rows.extend(data)
        if len(data) < page_size:
            break
        offset += page_size
    logger.info("fetch: %d total profiles scanned", len(rows))
    return rows


def _enrich_with_stripe(sb: Any, profile_ids: list[str]) -> set[str]:
    """Return the set of profile_ids that have an active stripe_customer_id
    via user_subscriptions."""
    if not profile_ids:
        return set()
    paying: set[str] = set()
    # supabase-py .in_() has a payload cap — chunk defensively.
    for i in range(0, len(profile_ids), 200):
        chunk = profile_ids[i : i + 200]
        try:
            resp = (
                sb.table("user_subscriptions")
                .select("user_id,stripe_customer_id")
                .in_("user_id", chunk)
                .execute()
            )
            for row in resp.data or []:
                if row.get("stripe_customer_id"):
                    paying.add(row["user_id"])
        except Exception as exc:
            logger.warning(
                "enrich: user_subscriptions lookup failed for chunk %d — %s",
                i,
                exc,
            )
    return paying


# ---------------------------------------------------------------------------
# Cluster building + winner selection
# ---------------------------------------------------------------------------


def build_clusters(profiles: list[dict]) -> dict[str, list[dict]]:
    """Group profiles by lowercased email. Skip NULL / blank / soft-deleted."""
    clusters: dict[str, list[dict]] = defaultdict(list)
    for p in profiles:
        email = (p.get("email") or "").strip().lower()
        if not email:
            continue
        if p.get("deleted_at"):
            continue  # already archived — ignore
        clusters[email].append(p)
    # Keep only real duplicates
    return {e: ps for e, ps in clusters.items() if len(ps) > 1}


def pick_winner(candidates: list[dict], paying_ids: set[str]) -> dict:
    """Deterministic winner selection.

    Lower score == better. Sort ascending.
    """

    def sort_key(p: dict) -> tuple:
        # 1. Most recent last_sign_in_at wins (None pushed to the back)
        last = p.get("last_sign_in_at")
        last_rank = 0 if last else 1
        last_val = last or ""  # strings compare lexicographically for ISO ts
        # 2. Paying wins (lower is better)
        pays = 0 if p["id"] in paying_ids else 1
        # 3. Oldest created_at wins
        created = p.get("created_at") or "9999-12-31"
        # 4. Tiebreak by id for determinism
        return (last_rank, -_ts_to_float(last_val), pays, created, str(p["id"]))

    return sorted(candidates, key=sort_key)[0]


def _ts_to_float(ts: str) -> float:
    """Convert ISO timestamp string to a float for sorting. Missing => 0."""
    if not ts:
        return 0.0
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# CSV + audit
# ---------------------------------------------------------------------------


def write_plan_csv(
    clusters: dict[str, list[dict]],
    paying_ids: set[str],
    output_path: Path,
) -> list[dict]:
    """Write a CSV describing the merge plan. Returns the plan rows."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plan_rows: list[dict] = []
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "email",
                "cluster_size",
                "winner_id",
                "loser_ids",
                "winner_last_sign_in",
                "winner_is_paying",
                "recommendation",
            ]
        )
        for email, members in sorted(clusters.items()):
            winner = pick_winner(members, paying_ids)
            losers = [m for m in members if m["id"] != winner["id"]]
            row = {
                "email": email,
                "cluster_size": len(members),
                "winner_id": winner["id"],
                "loser_ids": ";".join(m["id"] for m in losers),
                "winner_last_sign_in": winner.get("last_sign_in_at") or "",
                "winner_is_paying": "yes" if winner["id"] in paying_ids else "no",
                "recommendation": "merge_losers_into_winner",
            }
            writer.writerow(
                [
                    row["email"],
                    row["cluster_size"],
                    row["winner_id"],
                    row["loser_ids"],
                    row["winner_last_sign_in"],
                    row["winner_is_paying"],
                    row["recommendation"],
                ]
            )
            plan_rows.append(row | {"winner": winner, "losers": losers})
    logger.info("plan: wrote %d cluster rows → %s", len(plan_rows), output_path)
    return plan_rows


# ---------------------------------------------------------------------------
# Mutation (only in --execute mode)
# ---------------------------------------------------------------------------


def apply_merge(sb: Any, winner: dict, losers: list[dict], email: str) -> None:
    """Re-point FK rows + soft-delete losers + audit, for a single cluster.

    Any failure inside this function is expected to be caught by the caller;
    each cluster is independent so we don't abort the whole run on one bad one.
    """
    winner_id = winner["id"]
    loser_ids = [l["id"] for l in losers]

    # 1. Re-point FK rows on each dependent table.
    for table in FK_TABLES_USER_ID:
        for loser_id in loser_ids:
            try:
                sb.table(table).update({"user_id": winner_id}).eq(
                    "user_id", loser_id
                ).execute()
            except Exception as exc:
                logger.warning(
                    "merge(%s): FK repoint failed for %s.user_id %s → %s — %s",
                    email,
                    table,
                    loser_id,
                    winner_id,
                    exc,
                )

    # 2. Soft-delete each loser profile.
    now_iso = datetime.now(timezone.utc).isoformat()
    for loser_id in loser_ids:
        try:
            sb.table("profiles").update(
                {
                    "deleted_at": now_iso,
                    "deleted_reason": f"dedup_merged_to_{winner_id}",
                    "migrated_to": winner_id,
                }
            ).eq("id", loser_id).execute()
        except Exception as exc:
            logger.error(
                "merge(%s): soft-delete of loser %s failed — %s",
                email,
                loser_id,
                exc,
            )

    # 3. Audit event (one per merged cluster).
    try:
        sb.table("audit_events").insert(
            {
                "event_type": "profile_dedup_merged",
                "actor_id_hash": None,  # system / script run
                "target_id_hash": _hash_id(winner_id),
                "details": {
                    "email": email,
                    "winner_id": winner_id,
                    "loser_ids": loser_ids,
                    "fk_tables": list(FK_TABLES_USER_ID),
                    "story": "TD-DB-011 / STORY-2.8",
                },
            }
        ).execute()
    except Exception as exc:
        logger.error("merge(%s): audit insert failed — %s", email, exc)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Perform writes (also requires env CONFIRM_DEDUP=YES). Default: dry-run.",
    )
    parser.add_argument(
        "--output-dir",
        default="docs/audit",
        help="Directory for the plan CSV. Default: docs/audit",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    dry_run = not args.execute
    if not dry_run and os.getenv(CONFIRM_ENV, "").upper() != CONFIRM_VALUE:
        logger.error(
            "--execute supplied but env %s != %s — refusing to run. "
            "Set CONFIRM_DEDUP=YES to proceed.",
            CONFIRM_ENV,
            CONFIRM_VALUE,
        )
        return 2

    sb = _get_client()
    profiles = _fetch_all_profiles(sb)
    clusters = build_clusters(profiles)

    if not clusters:
        logger.info("dedup: no duplicate emails found — nothing to do")
        return 0

    logger.info(
        "dedup: found %d duplicate-email clusters (%d total loser rows)",
        len(clusters),
        sum(len(ps) - 1 for ps in clusters.values()),
    )

    paying_ids = _enrich_with_stripe(sb, [p["id"] for ps in clusters.values() for p in ps])
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = Path(args.output_dir) / f"dedup_profiles_email_{ts}.csv"
    plan = write_plan_csv(clusters, paying_ids, output_path)

    if dry_run:
        logger.info("dedup: DRY-RUN — no writes executed. Review %s then re-run with --execute", output_path)
        # Echo a short summary to stdout for CI logs
        print(json.dumps({"mode": "dry_run", "clusters": len(plan), "csv": str(output_path)}))
        return 0

    logger.warning("dedup: EXECUTE mode confirmed — applying merges")
    applied = 0
    failed = 0
    for entry in plan:
        try:
            apply_merge(sb, entry["winner"], entry["losers"], entry["email"])
            applied += 1
        except Exception as exc:  # defensive — apply_merge itself catches, but be safe
            failed += 1
            logger.exception(
                "dedup: cluster %s FAILED hard — %s", entry["email"], exc
            )

    logger.info("dedup: applied=%d failed=%d", applied, failed)
    print(
        json.dumps(
            {"mode": "execute", "applied": applied, "failed": failed, "csv": str(output_path)}
        )
    )
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
