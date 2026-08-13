#!/usr/bin/env python3
"""Fail if canonical docs still define SmartLic as an independent SaaS.

Guards ADR-STRAT-001 / issue #1262. Stdlib only.

Policy lives in docs/strategy/strategic-positioning-policy.json.
This module only loads that policy and evaluates the tree.

Exit 0 — positioning is coherent.
Exit 1 — one or more contradictions found.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLICY_REL = Path("docs") / "strategy" / "strategic-positioning-policy.json"

# Sentence-level markers: a forbidden phrase in this window is historical
# or negated, not an affirmative current-state claim.
_NEGATION_OR_HISTORY = re.compile(
    r"(?ix)"
    r"("
    r"n[aã]o\s+(é|e|usa|vende|opera|tem|ser[aá]|foi|criar|tratar)"
    r"|n[aã]o\s+é\s+(um|uma|mais)"
    r"|does\s+not"
    r"|do\s+not"
    r"|is\s+not"
    r"|isn['’]t"
    r"|doesn['’]t"
    r"|deixou\s+de"
    r"|nunca\s+"
    r"|sem\s+(assinatura|billing|saas|stripe|trial|mrr)"
    r"|hist[oó]rico"
    r"|legado"
    r"|sunset"
    r"|supersed"
    r"|n[aã]o\s+é\s+mais"
    r"|n[aã]o\s+mais"
    r")"
)


def policy_path(root: Path) -> Path:
    return root / POLICY_REL


def load_policy(root: Path | None = None) -> dict:
    path = policy_path(root or ROOT)
    if not path.is_file():
        raise FileNotFoundError(f"missing required policy file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _read(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"missing required file: {path}")
    return path.read_text(encoding="utf-8")


def _header(text: str, n_lines: int) -> str:
    return "\n".join(text.splitlines()[:n_lines])


def sentence_window(text: str, start: int, end: int) -> str:
    """Return the line/sentence containing [start:end]."""
    prev = max(text.rfind("\n", 0, start), text.rfind(". ", 0, start), text.rfind("! ", 0, start))
    nxt_candidates = [text.find("\n", end), text.find(". ", end), text.find("! ", end)]
    nxt = min((i for i in nxt_candidates if i != -1), default=len(text))
    lo = prev + 1 if prev >= 0 else 0
    return text[lo:nxt]


def is_negated_or_historical(sentence: str) -> bool:
    """True when the sentence denies or historicizes the claim."""
    return bool(_NEGATION_OR_HISTORY.search(sentence))


def find_affirmative_hits(pattern: str, text: str) -> list[str]:
    """Return pattern once if any non-negated, non-historical match exists."""
    hits: list[str] = []
    try:
        compiled = re.compile(pattern, flags=re.IGNORECASE | re.MULTILINE)
    except re.error:
        compiled = re.compile(re.escape(pattern), flags=re.IGNORECASE | re.MULTILINE)
    for match in compiled.finditer(text):
        window = sentence_window(text, match.start(), match.end())
        if is_negated_or_historical(window):
            continue
        hits.append(pattern)
        break
    return hits


def evaluate(root: Path | None = None, policy: dict | None = None) -> list[str]:
    """Evaluate *root* against *policy*. Returns a list of error strings."""
    root = root or ROOT
    policy = policy if policy is not None else load_policy(root)
    errors: list[str] = []

    try:
        file_specs: dict = policy["files"]
        contents: dict[str, str] = {}
        for rel in file_specs:
            contents[rel] = _read(root / rel)
        for rel in policy.get("extra_forbidden_scan", {}).get("files", []):
            path = root / rel
            if path.is_file():
                contents.setdefault(rel, _read(path))
        prd = _read(root / "PRD.md")
        roadmap = _read(root / "ROADMAP.md")
        adr = contents.get(
            "docs/adr/ADR-STRAT-001-smartlic-confenge-inbound.md",
            _read(root / "docs/adr/ADR-STRAT-001-smartlic-confenge-inbound.md"),
        )
    except FileNotFoundError as exc:
        return [str(exc)]

    for rel, spec in file_specs.items():
        text = contents[rel]
        for phrase in spec.get("required", []):
            if phrase not in text:
                errors.append(f"{rel} missing required phrase: {phrase!r}")
        for pat in spec.get("forbidden", []):
            for hit in find_affirmative_hits(pat, text):
                errors.append(f"{rel} still contains forbidden current-SaaS claim: {hit}")

    extra = policy.get("extra_forbidden_scan", {})
    for rel in extra.get("files", []):
        text = contents.get(rel)
        if text is None:
            continue
        for pat in extra.get("patterns", []):
            for hit in find_affirmative_hits(pat, text):
                errors.append(f"{rel} still contains forbidden current-SaaS claim: {hit}")

    header_rules = policy.get("header_rules", {})
    prd_rules = header_rules.get("PRD.md", {})
    prd_header = _header(prd, int(prd_rules.get("lines", 40)))
    prd_header_l = prd_header.lower()
    for cite in prd_rules.get("must_cite", []):
        if cite not in prd_header:
            errors.append(f"PRD.md header (first {prd_rules.get('lines', 40)} lines) must cite {cite}")
    positioning_any = prd_rules.get("positioning_any", [])
    if positioning_any and not any(p.lower() in prd_header_l or p in prd_header for p in positioning_any):
        errors.append("PRD.md header must state inbound/CONFENGE positioning")
    for pat in prd_rules.get("forbidden", []):
        for hit in find_affirmative_hits(pat, prd_header):
            errors.append(f"PRD.md header still contains forbidden claim: {hit}")

    rm_rules = header_rules.get("ROADMAP.md", {})
    rm_header = _header(roadmap, int(rm_rules.get("lines", 25)))
    for cite in rm_rules.get("must_cite", []):
        if cite not in rm_header:
            errors.append("ROADMAP.md header must cite ADR-STRAT-001" if cite == "ADR-STRAT-001" else f"ROADMAP.md header must cite {cite}")
    for cite, n_lines in rm_rules.get("must_cite_extended", {}).items():
        if cite not in _header(roadmap, int(n_lines)):
            errors.append(f"ROADMAP.md header must cite {cite}")
    for pat in rm_rules.get("forbidden", []):
        for hit in find_affirmative_hits(pat, rm_header):
            errors.append(f"ROADMAP.md header still contains superseded growth/SaaS objective: {hit}")

    if not re.search(r"\*\*Status:\*\*\s*Accepted|Status \| Accepted", adr):
        errors.append("ADR-STRAT-001 must have Status Accepted")

    return errors


def main(root: Path | None = None) -> int:
    try:
        errors = evaluate(root or ROOT)
    except FileNotFoundError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, KeyError) as exc:
        print(f"FAIL: invalid positioning policy: {exc}", file=sys.stderr)
        return 1

    if errors:
        print("Strategic positioning check FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("Strategic positioning check passed (ADR-STRAT-001 / #1262).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
