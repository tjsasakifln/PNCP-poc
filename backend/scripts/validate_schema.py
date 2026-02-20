"""CRIT-001 AC13: Validate search_results_cache schema against Pydantic model.

Compares the actual database schema with the expected schema defined in
SearchResultsCacheRow. Can run against any environment.

Usage:
    python backend/scripts/validate_schema.py
    python backend/scripts/validate_schema.py --database-url postgresql://...

Exit codes:
    0: Schema aligned
    1: Divergence found
    2: Connection error
"""

import argparse
import os
import sys
from pathlib import Path

# Add backend to path for imports
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))


def get_db_columns(database_url: str | None = None) -> list[dict] | None:
    """Fetch column metadata from information_schema.

    Returns list of dicts with: column_name, data_type, is_nullable, column_default
    """
    try:
        if database_url:
            import psycopg2
            conn = psycopg2.connect(database_url)
        else:
            # Use Supabase REST API via supabase-py
            from dotenv import load_dotenv
            load_dotenv(backend_dir / ".env")

            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

            if not supabase_url or not supabase_key:
                print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required (set in .env or as env vars)")
                return None

            # Use REST RPC for schema introspection
            import httpx
            response = httpx.post(
                f"{supabase_url}/rest/v1/rpc/get_table_columns",
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}",
                    "Content-Type": "application/json",
                },
                json={"table_name_param": "search_results_cache"},
                timeout=10,
            )

            if response.status_code == 404:
                # RPC function doesn't exist — fall back to direct query note
                print("NOTE: RPC function 'get_table_columns' not found.")
                print("Create it or use --database-url for direct connection.")
                return None

            if response.status_code != 200:
                print(f"ERROR: Supabase API returned {response.status_code}: {response.text[:200]}")
                return None

            return response.json()

        # Direct PostgreSQL connection path
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'search_results_cache'
            ORDER BY ordinal_position
        """)
        columns = []
        for row in cursor.fetchall():
            columns.append({
                "column_name": row[0],
                "data_type": row[1],
                "is_nullable": row[2],
                "column_default": row[3],
            })
        cursor.close()
        conn.close()
        return columns

    except ImportError as e:
        print(f"ERROR: Missing dependency: {e}")
        print("Install: pip install psycopg2-binary (for --database-url)")
        return None
    except Exception as e:
        print(f"ERROR: Database connection failed: {e}")
        return None


def validate_schema(db_columns: list[dict]) -> tuple[bool, list[str]]:
    """Compare DB columns against SearchResultsCacheRow model.

    Returns (is_valid, list_of_issues).
    """
    from models.cache import SearchResultsCacheRow

    expected = SearchResultsCacheRow.expected_columns()
    actual = {col["column_name"] for col in db_columns}

    issues = []

    # Missing columns (in model but not in DB)
    missing = expected - actual
    for col in sorted(missing):
        issues.append(f"MISSING: Column '{col}' expected by model but not in database")

    # Extra columns (in DB but not in model)
    extra = actual - expected
    for col in sorted(extra):
        issues.append(f"EXTRA: Column '{col}' in database but not in model (may need model update)")

    return len(missing) == 0, issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate search_results_cache schema")
    parser.add_argument(
        "--database-url",
        help="PostgreSQL connection URL (default: uses SUPABASE_URL from .env)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Schema Validation: search_results_cache")
    print("=" * 60)

    # Load expected columns from model
    from models.cache import SearchResultsCacheRow
    expected = SearchResultsCacheRow.expected_columns()
    print(f"\nExpected columns ({len(expected)}): {sorted(expected)}")

    # Fetch actual columns from DB
    db_columns = get_db_columns(args.database_url)
    if db_columns is None:
        print("\nCould not connect to database. Validating model only.")
        print(f"Model has {len(expected)} columns — looks correct.")
        return 2

    actual = {col["column_name"] for col in db_columns}
    print(f"Actual columns  ({len(actual)}): {sorted(actual)}")

    # Validate
    is_valid, issues = validate_schema(db_columns)

    if issues:
        print(f"\nIssues found ({len(issues)}):")
        for issue in issues:
            print(f"  - {issue}")

    if is_valid:
        print(f"\n{'='*60}")
        print("RESULT: Schema aligned (all expected columns present)")
        print(f"{'='*60}")
        return 0
    else:
        print(f"\n{'='*60}")
        print("RESULT: DIVERGENCE DETECTED — schema does not match model")
        print(f"{'='*60}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
