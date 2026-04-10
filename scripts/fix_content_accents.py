"""Normalize Portuguese accents in TypeScript/TSX static content files.

This tool operates ONLY inside string literals (single-quoted, double-quoted,
template literals). Code, comments, and identifiers are never touched.
Slug-like literals (pure lowercase + hyphens/digits) are skipped to protect
URL identifiers in arrays like ``relatedTerms: ['dispensa-de-licitacao']``.

Usage:
    python scripts/fix_content_accents.py FILE...           # apply
    python scripts/fix_content_accents.py --dry-run FILE    # preview diff
    python scripts/fix_content_accents.py --check FILE...   # exit 1 on any hit
    python scripts/fix_content_accents.py --all             # every frontend/lib/*.ts
    python scripts/fix_content_accents.py --report-markdown FILE...  # flag markdown leaks

The rules come from scripts/_pt_accents.py. Ambiguous cases (e.g., ``e`` vs
``é``, ``pais`` vs ``país``, ``por`` vs ``pôr``) are deliberately NOT in the
dictionary — they require human review.

Exit codes:
    0 — no changes needed / changes applied
    1 — --check detected pending changes
    2 — usage error / IO failure
"""

from __future__ import annotations

import argparse
import difflib
import glob
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Local import; script MUST run from project root to find _pt_accents.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pt_accents import (  # noqa: E402
    PHRASE_RULES,
    build_rules,
    detect_markdown,
    is_slug_like,
)

RULES = build_rules()

# URLs, domains, and email addresses — these must NEVER be modified even
# when embedded inside prose strings (e.g., "Portal da Transparência
# (transparencia.gov.br)"). The applier replaces matches with placeholders
# before running accent rules, then restores them.
URL_PATTERN = re.compile(
    r"(?:https?://[^\s'\"`)]+)"                    # absolute URL
    r"|(?:www\.[a-zA-Z0-9][a-zA-Z0-9\-._/]*)"      # www.domain
    r"|(?:[a-zA-Z0-9][a-zA-Z0-9\-._]*\.(?:gov|com|org|net|br|io|dev|app|tech|info)"
    r"(?:\.[a-zA-Z]{2,3})?(?:/[^\s'\"`)]*)?)"      # bare domain like foo.gov.br/path
    r"|(?:[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})"  # email
)


# ---------------------------------------------------------------------------
# String-literal extractor (state machine)
# ---------------------------------------------------------------------------


@dataclass
class LiteralSpan:
    """A contiguous region of the source file that is inside a string literal."""

    start: int          # index (exclusive of opening quote)
    end: int            # index (exclusive of closing quote)
    quote: str          # "'" | '"' | '`'
    content: str        # raw string content (with escapes still intact)

    @property
    def is_slug(self) -> bool:
        # Resolve simple escapes for slug detection (so '\n' doesn't fool it).
        return is_slug_like(self.content)


def extract_string_literals(src: str) -> list[LiteralSpan]:
    """Scan TS/JS source and return all string literal spans.

    Handles:
    - Single-quoted strings with \\ escapes
    - Double-quoted strings with \\ escapes
    - Template literals (backticks) — content NOT parsed recursively; ${...}
      expressions ARE part of the literal content but replacements are still
      applied inside them. This is fine for our static content which doesn't
      use expression interpolation.
    - Line comments (// ...) and block comments (/* ... */) — SKIPPED entirely
      (never enter literal state while inside a comment).
    - Regex literals — heuristically skipped to avoid treating /foo/ as a
      division-then-path. The heuristic: a / is a regex start only if the
      previous non-whitespace char is one of ``([=,:;!&|?{}``<newline> or the
      start of file. Otherwise treat as division.

    Returns literals in document order.
    """
    literals: list[LiteralSpan] = []
    n = len(src)
    i = 0

    # Track the previous meaningful (non-whitespace, non-comment) char to
    # disambiguate regex vs division.
    def _prev_meaningful(idx: int) -> str:
        j = idx - 1
        while j >= 0 and src[j] in " \t":
            j -= 1
        return src[j] if j >= 0 else "\n"

    while i < n:
        c = src[i]

        # Line comment
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            end = src.find("\n", i)
            i = n if end == -1 else end + 1
            continue
        # Block comment
        if c == "/" and i + 1 < n and src[i + 1] == "*":
            end = src.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue
        # Regex literal (heuristic)
        if c == "/":
            prev = _prev_meaningful(i)
            if prev in "([=,:;!&|?{}\n" or prev == "":
                # Consume until unescaped /
                j = i + 1
                in_class = False
                while j < n:
                    cj = src[j]
                    if cj == "\\":
                        j += 2
                        continue
                    if cj == "[":
                        in_class = True
                    elif cj == "]":
                        in_class = False
                    elif cj == "/" and not in_class:
                        j += 1
                        break
                    elif cj == "\n":
                        # Invalid regex; treat as division.
                        break
                    j += 1
                # Skip flags (gimsuy)
                while j < n and src[j] in "gimsuy":
                    j += 1
                i = j
                continue

        # String literal start
        if c in ("'", '"', "`"):
            quote = c
            start = i + 1
            j = start
            while j < n:
                cj = src[j]
                if cj == "\\":
                    j += 2
                    continue
                if cj == quote:
                    break
                # For single/double quoted, \n ends the literal (JS parse error),
                # but we tolerate it for safety and bail.
                if quote != "`" and cj == "\n":
                    break
                j += 1
            literals.append(
                LiteralSpan(
                    start=start,
                    end=j,
                    quote=quote,
                    content=src[start:j],
                )
            )
            i = j + 1
            continue

        i += 1

    return literals


# ---------------------------------------------------------------------------
# Replacement engine
# ---------------------------------------------------------------------------


@dataclass
class FileResult:
    path: Path
    original: str
    updated: str
    replacements: int = 0
    markdown_leaks: list[tuple[int, str, list[str]]] = field(default_factory=list)
    # (line_number, snippet, pattern_names)

    @property
    def changed(self) -> bool:
        return self.original != self.updated


def apply_rules_to_content(content: str) -> tuple[str, int]:
    """Apply all dictionary rules to a single string-literal content.

    URLs and email addresses are protected with placeholders to prevent
    accidental modification of domain names (e.g.,
    "transparencia.gov.br" must NOT become "transparência.gov.br").

    Returns (new_content, number_of_replacements).
    """
    original = content

    # Step 1: replace URLs/emails with unique placeholders
    preserved: list[str] = []

    def _stash(match: re.Match[str]) -> str:
        preserved.append(match.group(0))
        return f"\x00URL{len(preserved) - 1}\x00"

    protected = URL_PATTERN.sub(_stash, content)

    # Step 2: apply accent rules on the protected text
    for pat, dst in RULES:
        protected = pat.sub(dst, protected)

    # Step 2b: apply phrase-level verb-é rules (post-word rules)
    for pat, dst in PHRASE_RULES:
        protected = pat.sub(dst, protected)

    # Step 3: restore the preserved URLs
    def _restore(match: re.Match[str]) -> str:
        idx = int(match.group(1))
        return preserved[idx]

    content = re.sub(r"\x00URL(\d+)\x00", _restore, protected)

    count = 0 if content == original else sum(
        1 for _ in _diff_tokens(original, content)
    )
    return content, count


def _diff_tokens(a: str, b: str) -> list[str]:
    """Rough count of differences for the replacement tally."""
    if a == b:
        return []
    # Cheap approximation: count substring transitions via difflib ops.
    matcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    diffs: list[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            diffs.append(b[j1:j2] or a[i1:i2])
    return diffs


def process_file(path: Path, *, report_markdown: bool = False) -> FileResult:
    original = path.read_text(encoding="utf-8")
    literals = extract_string_literals(original)

    # Build the updated source by splicing replacements in reverse order
    # (so indices stay valid).
    pieces = list(original)
    total_repl = 0
    md_leaks: list[tuple[int, str, list[str]]] = []

    for lit in reversed(literals):
        if lit.is_slug:
            # Still check for markdown leaks even in slugs? No — slugs don't
            # have markdown. Skip entirely.
            continue
        new_content, _ = apply_rules_to_content(lit.content)
        if new_content != lit.content:
            # Replace in the pieces list.
            pieces[lit.start:lit.end] = list(new_content)
            total_repl += 1

        if report_markdown:
            hits = detect_markdown(lit.content)
            if hits:
                # Compute 1-based line number of the literal start.
                line_no = original.count("\n", 0, lit.start) + 1
                snippet = lit.content[:80].replace("\n", "\\n")
                md_leaks.append((line_no, snippet, hits))

    updated = "".join(pieces)
    return FileResult(
        path=path,
        original=original,
        updated=updated,
        replacements=total_repl,
        markdown_leaks=md_leaks,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


LIB_GLOB = "frontend/lib/*.ts"


def _expand_targets(paths: list[str], all_libs: bool) -> list[Path]:
    if all_libs:
        return sorted(Path(p) for p in glob.glob(LIB_GLOB) if Path(p).is_file())
    out: list[Path] = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            print(f"error: file not found: {p}", file=sys.stderr)
            sys.exit(2)
        out.append(path)
    return out


def _format_diff(result: FileResult) -> str:
    diff = difflib.unified_diff(
        result.original.splitlines(keepends=True),
        result.updated.splitlines(keepends=True),
        fromfile=str(result.path),
        tofile=str(result.path) + " (fixed)",
        n=1,
    )
    return "".join(diff)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Normalize Portuguese accents in TypeScript static content.",
    )
    parser.add_argument("paths", nargs="*", help="TS/TSX files to process")
    parser.add_argument(
        "--all",
        action="store_true",
        help=f"Process all files matching {LIB_GLOB}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print a diff of proposed changes without writing files",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if any file would be modified (for CI)",
    )
    parser.add_argument(
        "--report-markdown",
        action="store_true",
        help="Also report raw markdown (**, *, #, -, 1.) found in prose literals",
    )
    args = parser.parse_args(argv)

    if not args.paths and not args.all:
        parser.error("provide PATH(s) or --all")

    targets = _expand_targets(args.paths, args.all)
    if not targets:
        print("no target files found", file=sys.stderr)
        return 0

    any_changed = False
    total_repl = 0
    files_changed = 0

    for path in targets:
        try:
            result = process_file(path, report_markdown=args.report_markdown)
        except OSError as exc:
            print(f"error reading {path}: {exc}", file=sys.stderr)
            return 2

        if result.changed:
            any_changed = True
            files_changed += 1
            total_repl += result.replacements
            if args.dry_run:
                print(_format_diff(result))
                print(f"# {path}: {result.replacements} literal(s) would be updated")
            elif args.check:
                print(
                    f"FAIL {path}: {result.replacements} literal(s) need accent fixes"
                )
            else:
                path.write_text(result.updated, encoding="utf-8")
                print(f"OK   {path}: fixed {result.replacements} literal(s)")
        else:
            if not args.check:
                print(f"skip {path}: no changes")

        if args.report_markdown and result.markdown_leaks:
            print(f"\n# Raw markdown found in {path}:")
            for line_no, snippet, hits in result.markdown_leaks[:30]:
                print(f"  L{line_no:5d} [{', '.join(hits)}] {snippet}")
            if len(result.markdown_leaks) > 30:
                print(f"  ... and {len(result.markdown_leaks) - 30} more")

    if args.check:
        if any_changed:
            print(
                f"\n{files_changed} file(s) need accent fixes "
                f"({total_repl} literal(s) total).",
                file=sys.stderr,
            )
            print(
                "Run: python scripts/fix_content_accents.py --all",
                file=sys.stderr,
            )
            return 1
        print("OK — no accent issues detected.", file=sys.stderr)
        return 0

    if args.dry_run:
        print(
            f"\n# Summary: {files_changed} file(s), {total_repl} literal(s) "
            f"would be updated."
        )
        return 0

    print(
        f"\nDone — {files_changed} file(s) updated, {total_repl} literal(s) total."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
