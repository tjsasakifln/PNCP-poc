"""
HARD-000 / HARD-001: Semantic deduplication module for Report B2G.

Extracted from collect-report-data.py to improve testability and maintainability.

Provides:
- normalize_for_dedup(text) → set of normalized tokens
- jaccard_similarity(set_a, set_b) → float
- semantic_dedup(all_editais, source_priority) → (deduped_list, stats)
"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from typing import Any


# ============================================================
# Portuguese suffix stripping (lightweight stemming)
# ============================================================

_PT_SUFFIXES = re.compile(
    r"(ações|ação|amento|amentos|ência|ências|mente|idade|idades|ismo|ista|ável|ível|"
    r"ções|ção|ados|ado|idas|ida|idos|ido|ando|endo|indo|aram|eram|iram|aram|"
    r"antes|ante|ores|or|eiras|eira|eiros|eiro|"
    r"ações|ação|ções|ção)$"
)

_ACCENT_MAP = str.maketrans(
    "áàâãäéèêëíìîïóòôõöúùûüçñ",
    "aaaaaeeeeiiiiooooouuuucn",
)

_STOPWORDS = frozenset({
    "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "para", "por", "com", "sem", "sob", "sobre", "entre", "ate",
    "que", "qual", "quais", "como", "uma", "uns", "umas",
    "seu", "sua", "seus", "suas", "este", "esta", "esse", "essa",
    "contratacao", "empresa", "especializada", "execucao", "servicos",
    "servico", "prestacao", "objeto", "referente", "conforme",
    "municipio", "prefeitura", "municipal", "estado", "governo",
})


# ============================================================
# Utility
# ============================================================

def _safe_float(v: Any, default: float | None = None) -> float | None:
    """Safe float conversion."""
    if v is None:
        return default
    try:
        if isinstance(v, str):
            v = v.replace(",", ".")
        return float(v)
    except (ValueError, TypeError):
        return default


# ============================================================
# Public API
# ============================================================

def normalize_for_dedup(text: str) -> set[str]:
    """Normalize procurement object text for Jaccard comparison.

    Steps: lowercase → remove accents → remove punctuation → remove stopwords → strip suffixes.
    Returns set of normalized tokens (>3 chars).
    """
    if not text:
        return set()
    t = text.lower().translate(_ACCENT_MAP)
    t = re.sub(r"[^a-z\s]", " ", t)
    tokens: set[str] = set()
    for word in t.split():
        if len(word) <= 3 or word in _STOPWORDS:
            continue
        stemmed = _PT_SUFFIXES.sub("", word)
        if len(stemmed) < 3:
            stemmed = word
        tokens.add(stemmed)
    return tokens


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Jaccard similarity coefficient between two token sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def semantic_dedup(
    all_editais: list[dict],
    source_priority: dict[str, int] | None = None,
) -> tuple[list[dict], dict]:
    """Two-layer dedup: exact key → semantic similarity.

    Layer 1: Exact match on link/ID (existing logic)
    Layer 2: For remaining, group by (cnpj_orgao, valor±10%, data±3d) then Jaccard≥0.60

    Returns: (deduped_list, stats_dict)
    """
    if source_priority is None:
        source_priority = {"PNCP": 1, "PCP": 2, "LICITANET": 3, "BLL": 4, "BNC": 5}

    stats = {
        "exact_removed": 0,
        "semantic_removed": 0,
        "candidates_evaluated": 0,
        "semantic_warnings": [],
    }

    # --- Layer 1: Exact link dedup ---
    seen_links: dict[str, int] = {}
    layer1: list[dict] = []
    for ed in all_editais:
        link = (ed.get("link") or "").strip()
        ed_id = ed.get("_id") or ed.get("id") or ""
        key = link or ed_id
        if key and key in seen_links:
            stats["exact_removed"] += 1
            continue
        if key:
            seen_links[key] = len(layer1)
        layer1.append(ed)

    # --- Layer 2: Semantic dedup ---
    tokens_cache: list[set[str]] = []
    for ed in layer1:
        tokens_cache.append(normalize_for_dedup(ed.get("objeto", "")))

    orgao_groups: dict[str, list[int]] = defaultdict(list)
    for i, ed in enumerate(layer1):
        cnpj = re.sub(r"[^0-9]", "", ed.get("cnpj_orgao") or ed.get("orgao_cnpj") or "")
        orgao_key = cnpj if len(cnpj) >= 8 else (ed.get("orgao") or "unknown").lower()[:30]
        orgao_groups[orgao_key].append(i)

    removed_indices: set[int] = set()

    for _orgao_key, indices in orgao_groups.items():
        if len(indices) < 2:
            continue

        for a_pos in range(len(indices)):
            i = indices[a_pos]
            if i in removed_indices:
                continue
            ed_a = layer1[i]
            val_a = _safe_float(ed_a.get("valor_estimado")) or 0.0
            data_a = ed_a.get("data_abertura") or ed_a.get("data_publicacao") or ""

            for b_pos in range(a_pos + 1, len(indices)):
                j = indices[b_pos]
                if j in removed_indices:
                    continue
                ed_b = layer1[j]
                val_b = _safe_float(ed_b.get("valor_estimado")) or 0.0

                stats["candidates_evaluated"] += 1

                # Value proximity check (±10% or both zero)
                if val_a > 0 and val_b > 0:
                    ratio = min(val_a, val_b) / max(val_a, val_b)
                    if ratio < 0.90:
                        continue
                elif val_a > 0 or val_b > 0:
                    pass  # PCP has no values — still might match

                # Date proximity check (±3 days)
                data_b = ed_b.get("data_abertura") or ed_b.get("data_publicacao") or ""
                if data_a and data_b:
                    try:
                        da = datetime.strptime(data_a[:10], "%Y-%m-%d")
                        db = datetime.strptime(data_b[:10], "%Y-%m-%d")
                        if abs((da - db).days) > 3:
                            continue
                    except (ValueError, TypeError):
                        pass

                # Jaccard similarity on normalized objeto tokens
                sim = jaccard_similarity(tokens_cache[i], tokens_cache[j])
                if sim >= 0.60:
                    src_a = ed_a.get("_source_name") or ed_a.get("fonte") or "PNCP"
                    src_b = ed_b.get("_source_name") or ed_b.get("fonte") or "PNCP"
                    pri_a = source_priority.get(src_a, 99)
                    pri_b = source_priority.get(src_b, 99)

                    if pri_b < pri_a:
                        loser_idx, winner_idx = i, j
                    else:
                        loser_idx, winner_idx = j, i

                    removed_indices.add(loser_idx)
                    stats["semantic_removed"] += 1

                    # Merge: fill empty fields in winner from loser
                    winner = layer1[winner_idx]
                    loser = layer1[loser_idx]
                    for field in ("valor_estimado", "modalidade", "orgao", "data_abertura", "data_encerramento"):
                        w_val = winner.get(field)
                        l_val = loser.get(field)
                        if (w_val is None or w_val == "" or w_val == 0) and l_val:
                            winner[field] = l_val

                    winner.setdefault("_dedup_semantic_matches", []).append({
                        "score": round(sim, 3),
                        "merged_from": loser.get("_source_name") or loser.get("fonte") or "unknown",
                        "merged_link": loser.get("link", ""),
                    })

                    if sim < 0.70:
                        stats["semantic_warnings"].append({
                            "objeto_a": (ed_a.get("objeto") or "")[:80],
                            "objeto_b": (ed_b.get("objeto") or "")[:80],
                            "score": round(sim, 3),
                        })

    deduped = [ed for i, ed in enumerate(layer1) if i not in removed_indices]
    return deduped, stats
