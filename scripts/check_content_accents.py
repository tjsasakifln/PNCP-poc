"""CI wrapper: runs fix_content_accents.py in --check mode over all lib files.

Exit codes:
    0 — no accent issues
    1 — issues found (build should fail)
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from fix_content_accents import main  # noqa: E402

if __name__ == "__main__":
    extra = sys.argv[1:]
    sys.exit(main(["--check", "--all", *extra]))
