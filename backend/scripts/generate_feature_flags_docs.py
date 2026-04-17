#!/usr/bin/env python3
"""TD-SYS-021: Auto-generate feature flags documentation from config/features.py.

Usage:
    cd D:/pncp-poc/backend
    python scripts/generate_feature_flags_docs.py

Output:
    ../docs/features/feature-flags-reference.md
"""

import re
import pathlib
import sys
from datetime import datetime, timezone
from itertools import groupby

# Paths (run from backend/)
FEATURES_FILE = pathlib.Path("config/features.py")
OUTPUT_DIR = pathlib.Path("../docs/features")
OUTPUT_FILE = OUTPUT_DIR / "feature-flags-reference.md"


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Section header — two forms:
#   Form A (inline):  # === Title === or # === Title
#   Form B (3-line):  # ====
#                     # Title Text
#                     # ====
# We detect Form B by checking if a comment line is surrounded by === lines.
_RE_SECTION_INLINE = re.compile(r"^#\s*={3,}\s*(.+?)\s*=*\s*$")
_RE_SECTION_FENCE = re.compile(r"^#\s*={3,}\s*$")  # pure === fence line

# Comment line (single # comment)
_RE_COMMENT = re.compile(r"^#\s+(.*)")

# Standard flag with a wrapping cast and os.getenv:
#   FLAG: type = str_to_bool(os.getenv("VAR", "default"))
#   FLAG: type = int(os.getenv("VAR", "default"))
#   FLAG: type = float(os.getenv("VAR", "default"))
_RE_FLAG_CAST = re.compile(
    r'^([A-Z][A-Z0-9_]*)\s*:\s*(\w+)\s*='
    r'\s*\w+\(os\.getenv\("([A-Z0-9_]+)"(?:,\s*"([^"]*)")?\)'
)

# Bare os.getenv (no wrapping cast), possibly with .strip():
#   FLAG: str = os.getenv("VAR", "default")
#   FLAG: str = os.getenv("VAR", "default").strip()
_RE_FLAG_BARE = re.compile(
    r'^([A-Z][A-Z0-9_]*)\s*:\s*(\w+)\s*='
    r'\s*os\.getenv\("([A-Z0-9_]+)"(?:,\s*"([^"]*)")?\)'
)

# Nested-default form:
#   FLAG: type = float(os.getenv("OUTER_VAR", os.getenv("INNER_VAR", "5")))
_RE_FLAG_NESTED = re.compile(
    r'^([A-Z][A-Z0-9_]*)\s*:\s*(\w+)\s*='
    r'\s*\w+\(os\.getenv\("([A-Z0-9_]+)",\s*os\.getenv\("[^"]*",\s*"([^"]*)"\)\)'
)

# Private helper var that feeds a public flag via max()/min():
#   _MAX_FOO = int(os.getenv("ENV_VAR", "20"))
_RE_PRIVATE_HELPER = re.compile(
    r'^_([A-Z][A-Z0-9_]*)\s*=\s*\w+\(os\.getenv\("([A-Z0-9_]+)"(?:,\s*"([^"]*)")?\)\)'
)

# The public alias that uses the private helper:
#   FLAG: type = max(N, _PRIVATE_VAR)
_RE_FLAG_VIA_HELPER = re.compile(
    r'^([A-Z][A-Z0-9_]*)\s*:\s*(\w+)\s*=\s*(?:max|min)\(\d+,\s*_([A-Z0-9_]+)\)'
)


def parse_feature_flags(source: str) -> list[dict]:
    """Parse feature flag definitions from Python source.

    Returns a list of dicts with keys:
        section, var_name, type, env_var, default, description
    """
    lines = source.splitlines()
    flags: list[dict] = []
    current_section = "Geral"
    pending_comments: list[str] = []

    # Map private helper names → (env_var, default)
    private_helpers: dict[str, tuple[str, str]] = {}

    # State for 3-line section detection:  # ===\n # Title\n # ===
    _prev_was_fence = False
    _prev_comment_text: str = ""

    for line in lines:
        stripped = line.strip()

        # ---- Section fence line (# ====) -----------------------------------
        if _RE_SECTION_FENCE.match(stripped):
            if _prev_was_fence and _prev_comment_text:
                # Second fence → the comment in between is the section title
                current_section = _prev_comment_text
                pending_comments = []
                _prev_was_fence = False
                _prev_comment_text = ""
            else:
                # First fence — set state, will be confirmed on second fence
                _prev_was_fence = True
                _prev_comment_text = ""
            continue

        # ---- Inline section header:  # === Title ... ----------------------
        m = _RE_SECTION_INLINE.match(stripped)
        if m:
            current_section = m.group(1).strip()
            pending_comments = []
            _prev_was_fence = False
            _prev_comment_text = ""
            continue

        # ---- Comment accumulation ------------------------------------------
        cm = _RE_COMMENT.match(stripped)
        if cm:
            text = cm.group(1).strip()
            if _prev_was_fence:
                # Could be the title between two fences
                _prev_comment_text = text
            else:
                pending_comments.append(text)
            continue

        # ---- Blank line — flush comments if no flag followed ---------------
        if not stripped:
            pending_comments = []
            _prev_was_fence = False
            _prev_comment_text = ""
            continue

        # ---- Private helper (e.g. _MAX_ITEM_RAW) ---------------------------
        ph = _RE_PRIVATE_HELPER.match(stripped)
        if ph:
            _priv_name, env_var, default = ph.groups()
            private_helpers[_priv_name] = (env_var, default or "")
            _prev_was_fence = False
            # Don't reset comments — the public alias usually follows
            continue

        # ---- Public flag via private helper (e.g. MAX_ITEM_INSPECTIONS) ----
        vh = _RE_FLAG_VIA_HELPER.match(stripped)
        if vh:
            var_name, var_type, helper_name = vh.groups()
            if helper_name in private_helpers:
                env_var, default = private_helpers[helper_name]
                description = " ".join(pending_comments) if pending_comments else ""
                flags.append({
                    "section": current_section,
                    "var_name": var_name,
                    "type": var_type,
                    "env_var": env_var,
                    "default": default,
                    "description": description,
                })
            pending_comments = []
            continue

        # ---- Nested-default form (try before cast form) --------------------
        nd = _RE_FLAG_NESTED.match(stripped)
        if nd:
            var_name, var_type, env_var, default = nd.groups()
            description = " ".join(pending_comments) if pending_comments else ""
            flags.append({
                "section": current_section,
                "var_name": var_name,
                "type": var_type,
                "env_var": env_var,
                "default": default or "",
                "description": description,
            })
            pending_comments = []
            continue

        # ---- Standard cast form --------------------------------------------
        fc = _RE_FLAG_CAST.match(stripped)
        if fc:
            var_name, var_type, env_var, default = fc.groups()
            description = " ".join(pending_comments) if pending_comments else ""
            flags.append({
                "section": current_section,
                "var_name": var_name,
                "type": var_type,
                "env_var": env_var,
                "default": default or "",
                "description": description,
            })
            pending_comments = []
            continue

        # ---- Bare os.getenv (str, no cast) ---------------------------------
        bf = _RE_FLAG_BARE.match(stripped)
        if bf:
            var_name, var_type, env_var, default = bf.groups()
            description = " ".join(pending_comments) if pending_comments else ""
            flags.append({
                "section": current_section,
                "var_name": var_name,
                "type": var_type,
                "env_var": env_var,
                "default": default or "",
                "description": description,
            })
            pending_comments = []
            continue

        # ---- Any other non-blank, non-comment line resets comments ---------
        pending_comments = []
        _prev_was_fence = False
        _prev_comment_text = ""

    return flags


def _escape_pipe(s: str) -> str:
    """Escape pipe characters so Markdown table cells don't break."""
    return s.replace("|", "\\|")


def generate_markdown(flags: list[dict], source_path: str) -> str:
    """Generate Markdown reference table from parsed flags."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Feature Flags Reference",
        "",
        "> **Auto-generated** — não editar manualmente.",
        f"> Gerado em: {now}",
        f"> Fonte: `{source_path}`",
        "> Para regenerar: `cd backend && python scripts/generate_feature_flags_docs.py`",
        "",
        f"**Total:** {len(flags)} flags documentadas",
        "",
    ]

    for section, group_iter in groupby(flags, key=lambda f: f["section"]):
        section_flags = list(group_iter)
        lines += [
            f"## {section}",
            "",
            "| Env Var | Tipo | Default | Descrição |",
            "|---------|------|---------|-----------|",
        ]
        for f in section_flags:
            env_var = _escape_pipe(f["env_var"])
            typ = _escape_pipe(f["type"])
            default = _escape_pipe(f["default"]) if f["default"] else "—"
            desc = _escape_pipe(f["description"]) if f["description"] else "—"
            lines.append(f"| `{env_var}` | `{typ}` | `{default}` | {desc} |")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    if not FEATURES_FILE.exists():
        print(
            f"ERROR: {FEATURES_FILE} not found. Run from backend/ directory.",
            file=sys.stderr,
        )
        sys.exit(1)

    source = FEATURES_FILE.read_text(encoding="utf-8")
    flags = parse_feature_flags(source)

    if not flags:
        print(
            "WARNING: No feature flags found. Check the regex patterns.",
            file=sys.stderr,
        )
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = generate_markdown(flags, str(FEATURES_FILE))
    OUTPUT_FILE.write_text(doc, encoding="utf-8")

    print(f"Generated: {OUTPUT_FILE} ({len(flags)} flags across {_count_sections(flags)} sections)")

    # Quick verification — DATALAKE_ENABLED lives in ingestion/config.py, not
    # features.py, so we only check flags that ARE defined in features.py.
    required = {"LLM_ARBITER_ENABLED", "TRIAL_DURATION_DAYS"}
    found_env_vars = {f["env_var"] for f in flags}
    missing = required - found_env_vars
    if missing:
        print(f"WARNING: Expected flags not found: {missing}", file=sys.stderr)
    else:
        print(f"Verification OK: {required} all present.")


def _count_sections(flags: list[dict]) -> int:
    seen: set[str] = set()
    for f in flags:
        seen.add(f["section"])
    return len(seen)


if __name__ == "__main__":
    main()
