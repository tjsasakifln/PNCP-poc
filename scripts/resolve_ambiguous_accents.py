"""LLM-based resolver for ambiguous Portuguese accent decisions.

The deterministic normalizer in ``fix_content_accents.py`` intentionally
leaves a handful of words unchanged because they have two valid spellings
distinguished only by grammatical role:

    e      conjunção "and"        →  é      verbo "ser" (3ª pessoa)
    esta   pronome demonstrativo  →  está   verbo "estar" (3ª pessoa)
    pais   plural de "pai"        →  país   nação
    por    preposição             →  pôr    verbo "colocar"

This script resolves those cases automatically by calling OpenAI GPT-4.1-nano
with the surrounding context (≈60 chars before/after each occurrence) and a
strict Portuguese-grammar rubric. Decisions are cached in
``scripts/.accent_cache.json`` so re-running is free and idempotent.

Intended workflow:
    1. Author adds/edits static content in ``frontend/lib/*.ts``.
    2. Author runs ``python scripts/fix_content_accents.py --all`` (deterministic).
    3. Author runs ``python scripts/resolve_ambiguous_accents.py --all`` (LLM).
    4. CI runs ``python scripts/check_content_accents.py`` (deterministic, offline).

The CI check does NOT call this script — the LLM pass is a one-shot manual
operation. After it runs, the content file is fixed at rest and the CI check
has nothing left to complain about.

Environment:
    OPENAI_API_KEY must be set. The script automatically loads
    ``backend/.env`` if present.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from _pt_accents import is_slug_like  # noqa: E402
from fix_content_accents import extract_string_literals, URL_PATTERN  # noqa: E402

# ---------------------------------------------------------------------------
# Ambiguous tokens
# ---------------------------------------------------------------------------

# Each entry: (unaccented_form, accented_form, rule_description_for_llm).
# Word-boundary is applied by the scanner.
AMBIGUOUS: dict[str, tuple[str, str]] = {
    "e": ("e", "é"),
    "E": ("E", "É"),
    "esta": ("esta", "está"),
    "Esta": ("Esta", "Está"),
    "pais": ("pais", "país"),
    "Pais": ("Pais", "País"),
    "por": ("por", "pôr"),
    "Por": ("Por", "Pôr"),
}

RULES_FOR_LLM = """\
Você é um linter de português brasileiro revisando conteúdo sobre licitações públicas. Para cada trecho, decida se a palavra entre [[ ]] deve receber acento.

REGRA DE OURO: Quando houver QUALQUER dúvida, marque FALSE (sem acento). Só marque TRUE se o contexto deixar INEQUIVOCAMENTE claro que o acento é necessário.

---

## Regra 1 — "e" vs "é"

"e" é conjunção coordenativa ("and") em >90% dos casos. Só vire verbo "é" (forma do "ser") quando:
- O sujeito está imediatamente antes do "e" e o predicativo vem depois.
- A substituição por "é" faz sentido como afirmação ("X é Y").

### "e" (SEM acento — conjunção) — os MUITOS casos
Listas e coordenações de itens (palavras, números, incisos, artigos):
  "bens [[e]] serviços"                         → e (dois substantivos na mesma lista)
  "obras [[e]] serviços de engenharia"          → e
  "padrões de desempenho [[e]] qualidade"       → e
  "artigos 6, inciso XLI, [[e]] 29"             → e (lista de itens numerados)
  "arts. 28, 29, [[e]] 33"                      → e
  "impugnação, recurso [[e]] publicação"        → e
  "entre X [[e]] Y"                             → e
  "de um lado ... [[e]] de outro"               → e
  "federal, estadual [[e]] municipal"           → e
Conjunção ligando orações completas:
  "a empresa apresentou o documento [[e]] foi habilitada" → e (duas ações)
  "licita [[e]] contrata"                                 → e

### "é" (COM acento — verbo "ser")
Só quando substitui "é" de forma inequívoca:
  "dispensa de licitação [[e]] permitida por lei"   → é (licitação É permitida)
  "o processo [[e]] inviável"                        → é (processo É inviável)
  "o critério de julgamento [[e]] obrigatoriamente"  → é (critério É obrigatoriamente)
  "a inexigibilidade [[e]] uma modalidade"           → é
  "isso [[e]] importante"                            → é

TESTE MENTAL: substitua "e" por "é" e depois por "e também". Qual faz mais sentido?
- "bens é serviços" → sem sentido → é CONJUNÇÃO (false)
- "dispensa é permitida" → faz sentido → é VERBO (true)

---

## Regra 2 — "esta" vs "está"

"esta" é pronome demonstrativo ("this (f)"); "está" é verbo "estar" (3ª pessoa presente).
### "está" (COM acento — verbo)
  "o pregão [[esta]] previsto no artigo"         → está (pregão ESTÁ previsto)
  "o processo [[esta]] em andamento"              → está
### "esta" (SEM acento — demonstrativo)
  "[[esta]] modalidade é comum"                   → esta (THIS modality)
  "nos termos [[desta]] lei"                      → esta (irrelevante, já sem acento)
TESTE: se for seguido de particípio ("previsto", "em andamento", "disponível") = VERBO.
Se vier antes de substantivo feminino ("esta empresa", "esta lei") = DEMONSTRATIVO.

---

## Regra 3 — "pais" vs "país"

Em textos de licitações, economia, comércio e governo, "pais" é QUASE SEMPRE "país" (nação).
Só é "pais" (plural de "pai") em contexto familiar/escolar inequívoco.
### "país" (COM acento — nação)
  "todo o [[pais]] usa o sistema"                 → país
  "municípios do [[pais]]"                         → país
  "portais de compras do [[pais]]"                 → país
  "empresas do [[pais]] participam"                → país
  "em todo o [[pais]]"                             → país
### "pais" (SEM acento — progenitores)
  "os [[pais]] do aluno assinaram"                 → pais
  "reunião com os [[pais]] dos alunos"             → pais
  "responsabilidade dos [[pais]] pela educação"    → pais

---

## Regra 4 — "por" vs "pôr"

"por" é preposição (90%+). "pôr" é verbo infinitivo ("colocar").
### "pôr" (COM acento — verbo)
  "decidiu [[por]] fim ao contrato"               → pôr ("colocar fim")
  "precisa [[por]] a assinatura no documento"     → pôr
### "por" (SEM acento — preposição)
  "licitação [[por]] menor preço"                 → por
  "[[por]] meio de"                                → por
  "[[por]] fim, o licitante"                       → por (locução adverbial "por fim" = "finalmente")
  "passou [[por]] várias fases"                    → por

---

Responda EXCLUSIVAMENTE em JSON válido:
{"d": [{"i": 0, "a": true}, {"i": 1, "a": false}, ...]}

- Cada objeto deve ter o "i" do caso correspondente e "a" = true (acentuar) ou false (sem acento).
- A lista "d" deve conter EXATAMENTE um item para CADA caso recebido — nenhum pode faltar.
- DEFAULT CONSERVADOR: na dúvida, marque false.
"""


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


CACHE_PATH = _HERE / ".accent_cache.json"


def _cache_key(token: str, context: str) -> str:
    """Deterministic key for (token, context) pair."""
    h = hashlib.sha1()
    h.update(token.encode("utf-8"))
    h.update(b"\x1f")
    h.update(context.encode("utf-8"))
    return h.hexdigest()[:16]


def load_cache() -> dict[str, bool]:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_cache(cache: dict[str, bool]) -> None:
    CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------


@dataclass
class Occurrence:
    path: Path
    file_offset: int          # absolute byte offset of the token in the file
    token: str                # the matched form (e.g. "e", "Esta")
    context: str              # ~120 chars of surrounding text (for LLM)
    cache_key: str = field(init=False)

    def __post_init__(self) -> None:
        self.cache_key = _cache_key(self.token, self.context)


# Build one compiled regex to find all AMBIGUOUS forms in one pass.
_TOKEN_RE = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in AMBIGUOUS) + r")\b"
)

# Context window around each occurrence
_CONTEXT_BEFORE = 60
_CONTEXT_AFTER = 60


def scan_file(path: Path) -> list[Occurrence]:
    src = path.read_text(encoding="utf-8")
    literals = extract_string_literals(src)
    occurrences: list[Occurrence] = []

    for lit in literals:
        if is_slug_like(lit.content):
            continue
        content = lit.content

        # Skip any occurrence that lies within a URL/email span inside the literal.
        url_spans: list[tuple[int, int]] = [
            (m.start(), m.end()) for m in URL_PATTERN.finditer(content)
        ]

        def _in_url(start: int, end: int) -> bool:
            for us, ue in url_spans:
                if us <= start and end <= ue:
                    return True
            return False

        for m in _TOKEN_RE.finditer(content):
            if _in_url(m.start(), m.end()):
                continue
            token = m.group(1)
            ctx_start = max(0, m.start() - _CONTEXT_BEFORE)
            ctx_end = min(len(content), m.end() + _CONTEXT_AFTER)
            before = content[ctx_start : m.start()]
            after = content[m.end() : ctx_end]
            highlighted = f"{before}[[{token}]]{after}"
            # Normalize whitespace for stable cache keys
            highlighted = re.sub(r"\s+", " ", highlighted).strip()

            file_offset = lit.start + m.start()
            occurrences.append(
                Occurrence(
                    path=path,
                    file_offset=file_offset,
                    token=token,
                    context=highlighted,
                )
            )

    return occurrences


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------


def _load_env() -> None:
    """Load OPENAI_API_KEY from backend/.env if not already set."""
    if os.environ.get("OPENAI_API_KEY"):
        return
    env_file = Path("backend/.env")
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() == "OPENAI_API_KEY" and v.strip():
            os.environ["OPENAI_API_KEY"] = v.strip()
            return


_CLIENT = None


def _get_client():
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT
    _load_env()
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "error: openai SDK not installed. Run: pip install openai"
        ) from exc
    _CLIENT = OpenAI()
    return _CLIENT


def _call_llm(cases: list[Occurrence]) -> dict[int, bool]:
    """One LLM call. Returns {index → decision} dict (may be partial).

    Uses indexed decisions so missing entries are detectable.
    """
    payload = [
        {"i": i, "token": c.token, "trecho": c.context}
        for i, c in enumerate(cases)
    ]
    user_msg = (
        RULES_FOR_LLM
        + "\n\nCasos (JSON):\n"
        + json.dumps(payload, ensure_ascii=False)
    )
    response = _get_client().chat.completions.create(
        model="gpt-4.1-mini",  # nano underperforms on pais/país disambiguation
        temperature=0.0,
        messages=[
            {
                "role": "system",
                "content": (
                    "Você é um especialista em gramática do português brasileiro. "
                    "Responda apenas com JSON válido, sem texto adicional."
                ),
            },
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or "{}"
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"error: LLM returned invalid JSON: {exc}\nRaw: {content[:500]}"
        )

    raw = parsed.get("d")
    if not isinstance(raw, list):
        raise SystemExit(
            f"error: LLM 'd' field is not a list. Raw: {content[:500]}"
        )

    result: dict[int, bool] = {}
    for item in raw:
        # Accept two shapes: {"i": N, "a": bool} or bare bool (legacy)
        if isinstance(item, dict) and "i" in item and "a" in item:
            try:
                idx = int(item["i"])
            except (TypeError, ValueError):
                continue
            result[idx] = bool(item["a"])
        elif isinstance(item, bool):
            # Positional fallback — assume i is the list index
            result[len(result)] = item
    return result


def classify_batch(cases: list[Occurrence], *, depth: int = 0) -> list[bool]:
    """Return one bool per case, in order.

    Robust to LLM dropping entries: uses indexed responses and recursively
    splits the batch on mismatch. Max recursion depth: 3 (batch sizes go
    40→20→10→5→1).
    """
    if not cases:
        return []

    response = _call_llm(cases)

    # Check completeness
    missing = [i for i in range(len(cases)) if i not in response]
    if not missing:
        return [response[i] for i in range(len(cases))]

    # Partial response: retry only the missing indexes, recursively.
    if depth >= 4 or len(cases) == 1:
        # Give up — mark missing as "no accent" (safest default).
        print(
            f"  WARN: giving up on {len(missing)} unresolved case(s) at depth "
            f"{depth} — defaulting to 'no accent'",
            file=sys.stderr,
        )
        for i in missing:
            response[i] = False
        return [response[i] for i in range(len(cases))]

    print(
        f"  retry: {len(missing)} missing from {len(cases)}-case batch "
        f"(depth {depth})",
        file=sys.stderr,
    )
    missing_cases = [cases[i] for i in missing]
    # Recurse on the missing slice (split in half)
    if len(missing_cases) > 8:
        mid = len(missing_cases) // 2
        retry_a = classify_batch(missing_cases[:mid], depth=depth + 1)
        retry_b = classify_batch(missing_cases[mid:], depth=depth + 1)
        retry_decisions = retry_a + retry_b
    else:
        retry_decisions = classify_batch(missing_cases, depth=depth + 1)

    for orig_idx, decision in zip(missing, retry_decisions):
        response[orig_idx] = decision

    return [response[i] for i in range(len(cases))]


BATCH_SIZE = 40


def resolve_occurrences(
    occurrences: list[Occurrence],
    *,
    cache: dict[str, bool],
    dry_run: bool = False,
) -> list[tuple[Occurrence, bool]]:
    """Classify each occurrence (using cache where possible).

    Returns a list of (occurrence, accent_decision) pairs.
    """
    resolved: list[tuple[Occurrence, bool]] = []
    pending: list[Occurrence] = []

    for occ in occurrences:
        if occ.cache_key in cache:
            resolved.append((occ, cache[occ.cache_key]))
        else:
            pending.append(occ)

    if pending and not dry_run:
        print(
            f"  classifying {len(pending)} new occurrence(s) via GPT-4.1-nano...",
            file=sys.stderr,
        )
        for start in range(0, len(pending), BATCH_SIZE):
            batch = pending[start : start + BATCH_SIZE]
            decisions = classify_batch(batch)
            for occ, decision in zip(batch, decisions):
                cache[occ.cache_key] = decision
                resolved.append((occ, decision))
        save_cache(cache)
    elif pending and dry_run:
        print(
            f"  dry-run: {len(pending)} new occurrence(s) would be classified "
            f"(call LLM without --dry-run)",
            file=sys.stderr,
        )
        for occ in pending:
            resolved.append((occ, False))  # placeholder

    return resolved


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------


def apply_decisions(
    path: Path, decisions: list[tuple[Occurrence, bool]]
) -> int:
    """Rewrite the file applying only the decisions that require changes.

    Returns the number of tokens actually modified.
    """
    src = path.read_text(encoding="utf-8")
    # Sort by offset DESC so splicing does not invalidate earlier offsets.
    edits = sorted(
        [(occ, decision) for occ, decision in decisions if decision],
        key=lambda pair: pair[0].file_offset,
        reverse=True,
    )
    if not edits:
        return 0

    pieces = list(src)
    modified = 0
    for occ, _ in edits:
        unacc, acc = AMBIGUOUS[occ.token]
        end = occ.file_offset + len(unacc)
        # Safety: confirm the bytes at that position match the expected token.
        if "".join(pieces[occ.file_offset:end]) != unacc:
            # Offset got desynced (another edit shifted things). Skip.
            print(
                f"  WARN: offset mismatch at {path}:{occ.file_offset} — skipping",
                file=sys.stderr,
            )
            continue
        pieces[occ.file_offset:end] = list(acc)
        modified += 1

    path.write_text("".join(pieces), encoding="utf-8")
    return modified


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


LIB_GLOB = "frontend/lib/*.ts"


def _expand_targets(paths: list[str], all_libs: bool) -> list[Path]:
    if all_libs:
        import glob

        return sorted(
            Path(p) for p in glob.glob(LIB_GLOB) if Path(p).is_file()
        )
    out: list[Path] = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            print(f"error: file not found: {p}", file=sys.stderr)
            sys.exit(2)
        out.append(path)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "LLM-based ambiguous accent resolver for SmartLic static content."
        ),
    )
    parser.add_argument("paths", nargs="*", help="TS/TSX files to process")
    parser.add_argument(
        "--all", action="store_true", help=f"Process all files matching {LIB_GLOB}"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and report occurrences without calling LLM or writing files",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Delete the cache file before running (forces re-classification)",
    )
    args = parser.parse_args(argv)

    if not args.paths and not args.all:
        parser.error("provide PATH(s) or --all")

    if args.clear_cache and CACHE_PATH.exists():
        CACHE_PATH.unlink()
        print(f"cleared cache: {CACHE_PATH}", file=sys.stderr)

    targets = _expand_targets(args.paths, args.all)
    cache = load_cache()
    total_changes = 0

    for path in targets:
        occurrences = scan_file(path)
        if not occurrences:
            print(f"skip {path}: no ambiguous tokens")
            continue

        print(f"scan {path}: {len(occurrences)} ambiguous occurrence(s)")
        decisions = resolve_occurrences(
            occurrences, cache=cache, dry_run=args.dry_run
        )

        if args.dry_run:
            # Just print summary — don't apply
            acc = sum(1 for _, d in decisions if d)
            print(f"  would accent: {acc}/{len(decisions)}")
            continue

        changes = apply_decisions(path, decisions)
        total_changes += changes
        print(f"  applied {changes} accent correction(s)")

    if not args.dry_run:
        print(
            f"\nDone — {total_changes} accent correction(s) across "
            f"{len(targets)} file(s)."
        )
        print(f"Cache: {CACHE_PATH} ({len(cache)} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
