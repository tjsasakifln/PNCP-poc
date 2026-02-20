"""CRIT-001 AC5: Validate migration file prefixes for duplicates.

Scans supabase/migrations/ for SQL files with numeric prefixes and reports
any prefix that appears more than once. Intended for CI integration.

Usage:
    python backend/scripts/validate_migrations.py

Exit codes:
    0: No conflicts found
    1: Duplicate prefixes detected
"""

import os
import re
import sys
from collections import defaultdict
from pathlib import Path


def validate_migrations(migrations_dir: str | Path) -> tuple[bool, dict[str, list[str]]]:
    """Check for duplicate numeric prefixes in migration files.

    Args:
        migrations_dir: Path to the migrations directory.

    Returns:
        Tuple of (is_valid, conflicts_dict).
        conflicts_dict maps prefix to list of filenames sharing that prefix.
    """
    migrations_dir = Path(migrations_dir)
    if not migrations_dir.is_dir():
        print(f"ERROR: Directory not found: {migrations_dir}")
        return False, {}

    # Match files like 001_xxx.sql, 027b_xxx.sql (letter suffixes are distinct)
    pattern = re.compile(r"^(\d{3}[a-z]?)_.*\.sql$")

    prefix_files: dict[str, list[str]] = defaultdict(list)

    for f in sorted(migrations_dir.iterdir()):
        if not f.is_file():
            continue
        match = pattern.match(f.name)
        if match:
            prefix = match.group(1)
            prefix_files[prefix].append(f.name)

    # Find conflicts (prefix with >1 file)
    conflicts = {p: files for p, files in prefix_files.items() if len(files) > 1}

    return len(conflicts) == 0, conflicts


def main() -> int:
    # Resolve migrations dir relative to this script's location
    script_dir = Path(__file__).resolve().parent
    # backend/scripts/ -> project root -> supabase/migrations/
    project_root = script_dir.parent.parent
    migrations_dir = project_root / "supabase" / "migrations"

    is_valid, conflicts = validate_migrations(migrations_dir)

    if is_valid:
        file_count = len(list(migrations_dir.glob("*.sql")))
        print(f"OK: {file_count} migration files, no duplicate prefixes found.")
        return 0

    print("ERROR: Duplicate migration prefixes detected!\n")
    for prefix, files in sorted(conflicts.items()):
        print(f"  Prefix {prefix}:")
        for f in files:
            print(f"    - {f}")
    print(f"\nTotal conflicts: {len(conflicts)}")
    print("Fix: Rename migrations so each numeric prefix is unique.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
