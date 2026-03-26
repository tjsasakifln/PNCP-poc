#!/usr/bin/env python3
"""
intel-validate.py — Programmatic validation for Gates 2, 4, and 5 of /intel-busca.

Validates analysis quality after intel-analyze.py fills top20[].analise,
enforcing semantic compatibility, field completeness, and report coherence
before PDF generation.

Usage:
    python scripts/intel-validate.py --input docs/intel/intel-CNPJ-slug-YYYY-MM-DD.json
    python scripts/intel-validate.py --input data.json --fix
    python scripts/intel-validate.py --input data.json --fix --strict
    python scripts/intel-validate.py --input data.json --output validation-report.json

Requires:
    No external dependencies (stdlib only).
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ============================================================
# Windows console encoding fix
# ============================================================
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "buffer") and not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "buffer") and not isinstance(sys.stderr, io.TextIOWrapper):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except (ValueError, AttributeError):
        pass

# Ensure scripts/ is on sys.path for lib imports
_scripts_dir = str(Path(__file__).resolve().parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from lib.intel_logging import setup_intel_logging

logger = setup_intel_logging("intel-validate")

# ============================================================
# CONSTANTS
# ============================================================

# ANSI colors
_C_RESET = "\033[0m"
_C_GREEN = "\033[92m"
_C_RED = "\033[91m"
_C_YELLOW = "\033[93m"
_C_CYAN = "\033[96m"
_C_BOLD = "\033[1m"


def _c(text: str, color: str) -> str:
    if sys.stdout.isatty() if hasattr(sys.stdout, "isatty") else False:
        return f"{color}{text}{_C_RESET}"
    return text


def _ok(msg: str) -> None:
    logger.info("PASS %s", msg)


def _fail(msg: str) -> None:
    logger.error("FAIL %s", msg)


def _warn(msg: str) -> None:
    logger.warning("WARN %s", msg)


def _fix(msg: str) -> None:
    logger.info("FIX  %s", msg)


def _header(title: str) -> None:
    bar = "=" * 60
    logger.info(bar)
    logger.info(title)
    logger.info(bar)


# ============================================================
# GATE 2: SEMANTIC COMPATIBILITY
# ============================================================

# Pattern: (object_regex, cnae_prefix_set, reason)
# If the tender object matches the regex AND ALL company CNAEs
# are within cnae_prefix_set, the tender is incompatible.
HARD_INCOMPATIBLE_PATTERNS: dict[str, tuple[str, set[str], str]] = {
    "software_for_construction": (
        r"software|sistema|erp|tic\b|tecnologia da informa",
        {"42", "43", "41"},
        "Software/TI quando empresa e de construcao",
    ),
    "food_for_engineering": (
        r"aliment|refei[çc]|merenda|cozinha|nutri",
        {"71", "42", "43"},
        "Alimentacao quando empresa e de engenharia",
    ),
    "cleaning_for_construction": (
        r"limpeza|conserva[çc]|zeladoria|jardinagem",
        {"42", "43", "41"},
        "Limpeza/conservacao quando empresa e de obras",
    ),
    "concession_for_construction": (
        r"concess[ãa]o|zona azul|ilumina[çc][ãa]o p[úu]blica|transporte coletivo",
        {"42", "43", "41"},
        "Concessao de servico publico",
    ),
}


def _normalize_text(text: str) -> str:
    """Lowercase and strip accents for matching."""
    import unicodedata

    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _extract_cnae_prefixes(empresa: dict) -> set[str]:
    """Extract 2-digit CNAE prefixes from empresa data."""
    prefixes: set[str] = set()
    principal = str(empresa.get("cnae_principal") or "").strip()
    if len(principal) >= 2:
        prefixes.add(principal[:2])

    secundarios = empresa.get("cnaes_secundarios") or []
    if isinstance(secundarios, str):
        secundarios = [s.strip() for s in secundarios.split(",") if s.strip()]
    for cnae in secundarios:
        cnae_str = str(cnae).strip()
        if len(cnae_str) >= 2:
            prefixes.add(cnae_str[:2])

    return prefixes


def _edital_id(edital: dict, idx: int) -> str:
    """Build a short identifier for an edital (for issue messages)."""
    obj = (edital.get("objeto") or "")[:60]
    return f"#{idx+1} ({obj})"


def gate2_semantic(
    top20: list[dict],
    empresa: dict,
    do_fix: bool = False,
) -> dict:
    """Validate semantic compatibility between top20 tenders and company CNAEs."""
    result: dict[str, Any] = {
        "passed": True,
        "issues": [],
        "auto_fixed": [],
    }

    cnae_prefixes = _extract_cnae_prefixes(empresa)
    if not cnae_prefixes:
        result["issues"].append("Sem CNAEs na empresa — gate 2 ignorado")
        _warn("Sem CNAEs na empresa — gate 2 ignorado")
        return result

    indices_to_remove: list[int] = []
    gate2_decisions: list[dict] = []

    for idx, edital in enumerate(top20):
        objeto_raw = edital.get("objeto") or ""
        objeto_norm = _normalize_text(objeto_raw)

        for pattern_name, (regex, trigger_cnaes, reason) in HARD_INCOMPATIBLE_PATTERNS.items():
            if not re.search(regex, objeto_norm, re.IGNORECASE):
                continue

            # Check if ALL company CNAEs fall within the trigger set
            if cnae_prefixes.issubset(trigger_cnaes):
                eid = _edital_id(edital, idx)
                issue = f"{eid}: {reason} (pattern={pattern_name})"
                result["issues"].append(issue)
                result["passed"] = False

                decision = {
                    "edital_idx": idx,
                    "pattern": pattern_name,
                    "reason": reason,
                    "objeto_excerpt": objeto_raw[:80],
                    "company_cnaes": sorted(cnae_prefixes),
                    "action": "REMOVE" if do_fix else "FLAGGED",
                }
                gate2_decisions.append(decision)

                if do_fix and idx not in indices_to_remove:
                    indices_to_remove.append(idx)
                    result["auto_fixed"].append(f"Removido {eid} do top20")
                    _fix(f"Removido {eid}: {reason}")
                else:
                    _fail(issue)
                break  # One pattern match is enough per edital

    # Apply removals (reverse order to preserve indices)
    removed_editais = []
    for idx in sorted(indices_to_remove, reverse=True):
        removed_editais.append(top20.pop(idx))

    if not result["issues"]:
        _ok("Nenhuma incompatibilidade semantica detectada")
        result["passed"] = True

    return result, gate2_decisions, removed_editais


# ============================================================
# GATE 4: ANALYSIS COMPLETENESS
# ============================================================

FORBIDDEN_WORDS_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("verificar", re.compile(r"verific(?:ar|a[çc][ãa]o|ado|ando)", re.IGNORECASE)),
    ("possivelmente", re.compile(r"possivelmente", re.IGNORECASE)),
    ("buscar edital", re.compile(r"buscar\s+edital", re.IGNORECASE)),
    ("nao detalhado", re.compile(r"n[ãa]o\s+detalhad[oa]", re.IGNORECASE)),
    ("a confirmar", re.compile(r"a\s+confirmar", re.IGNORECASE)),
]

CRITERIO_JULGAMENTO_ENUM = {
    "menor preco",
    "menor preco global",
    "menor preco por item",
    "menor preco por lote",
    "maior desconto",
    "melhor tecnica",
    "tecnica e preco",
    "maior lance",
    "maior retorno economico",
    "nao se aplica",
    # Allow compound values from the edital like "Menor Preço Global, modo de disputa Aberto"
}

REGIME_EXECUCAO_ENUM = {
    "empreitada por preco global",
    "empreitada por preco unitario",
    "empreitada integral",
    "tarefa",
    "contratacao integrada",
    "contratacao semi-integrada",
    "fornecimento e prestacao de servico associado",
    "regime de contratacao integrada",
    "nao se aplica",
    "registro de precos",
}

CONSORCIO_ENUM = {
    "permitido",
    "vedado",
    "nao mencionado no edital",
    "nao mencionado",
}

RECOMENDACAO_ENUM = {
    "participar",
    "nao participar",
}

# Values that are always invalid for recomendacao_acao
RECOMENDACAO_INVALID = {
    "verificar",
    "avaliar",
    "avaliar com cautela",
    "",
}

REQUIRED_ANALISE_FIELDS = [
    "data_sessao",
    "criterio_julgamento",
    "regime_execucao",
    "consorcio",
    "recomendacao_acao",
]

# Replacement value for forbidden words when --fix is used
REPLACEMENT_VALUE = "Nao consta no edital disponivel"


def _is_valid_date(val: str) -> bool:
    """Check if value is a valid date DD/MM/YYYY or acceptable 'not available' text."""
    val_clean = val.strip()
    # Accept explicit "not available" text
    acceptable_missing = [
        "nao consta no edital disponivel",
        "nao consta no edital",
        "nao informado",
        "nao disponivel",
    ]
    if _normalize_text(val_clean) in acceptable_missing:
        return True
    # Try DD/MM/YYYY
    try:
        datetime.strptime(val_clean, "%d/%m/%Y")
        return True
    except ValueError:
        pass
    # Try YYYY-MM-DD
    try:
        datetime.strptime(val_clean, "%Y-%m-%d")
        return True
    except ValueError:
        pass
    return False


def _check_enum_field(val: str, enum_set: set[str]) -> bool:
    """Check if the normalized value starts with any enum value."""
    val_norm = _normalize_text(val.strip())
    if not val_norm:
        return False
    # Exact match
    if val_norm in enum_set:
        return True
    # Prefix match (for compound values like "Menor Preço Global, modo de disputa Aberto")
    for enum_val in enum_set:
        if val_norm.startswith(enum_val):
            return True
    return False


def gate4_completeness(
    top20: list[dict],
    empresa: dict,
    do_fix: bool = False,
) -> dict:
    """Validate analysis completeness for each tender in top20."""
    result: dict[str, Any] = {
        "passed": True,
        "issues": [],
        "forbidden_words_found": [],
        "missing_fields": [],
    }

    sancoes = empresa.get("sancoes") or {}
    has_active_sanction = any(v for v in sancoes.values()) if isinstance(sancoes, dict) else bool(sancoes)
    is_sancionada = bool(empresa.get("sancionada")) or has_active_sanction

    for idx, edital in enumerate(top20):
        analise = edital.get("analise") or {}
        eid = _edital_id(edital, idx)

        # 1. Forbidden words check — scan ALL string fields in analise
        for field_name, field_val in analise.items():
            texts_to_check: list[str] = []
            if isinstance(field_val, str):
                texts_to_check.append(field_val)
            elif isinstance(field_val, list):
                texts_to_check.extend(str(v) for v in field_val if isinstance(v, str))

            for text in texts_to_check:
                for word_label, pattern in FORBIDDEN_WORDS_PATTERNS:
                    if pattern.search(text):
                        result["forbidden_words_found"].append({
                            "edital_idx": idx,
                            "edital_id": eid,
                            "field": field_name,
                            "word": word_label,
                        })
                        issue = f"{eid}: campo '{field_name}' contem palavra proibida '{word_label}'"
                        result["issues"].append(issue)
                        result["passed"] = False
                        _fail(issue)

                        if do_fix:
                            # Replace the forbidden word occurrence
                            cleaned = pattern.sub(REPLACEMENT_VALUE, text)
                            if isinstance(field_val, str):
                                analise[field_name] = cleaned
                            # For lists, rebuild
                            elif isinstance(field_val, list):
                                analise[field_name] = [
                                    cleaned if str(v) == text else v
                                    for v in field_val
                                ]
                            _fix(f"Substituido '{word_label}' em {eid}.{field_name}")

        # 1b. "Não consta no edital" embedded in sentences (all fields)
        # Rule: "Não consta no edital disponível" is OK as standalone value,
        # but NOT OK when embedded in a longer sentence (len > 50).
        _nao_consta_embedded = re.compile(r"N[ãa]o\s+consta", re.IGNORECASE)
        for field_name, field_val in analise.items():
            if not isinstance(field_val, str):
                continue
            val_stripped = field_val.strip()
            if not _nao_consta_embedded.search(val_stripped):
                continue
            # Allow standalone "Não consta..." values (short, self-contained)
            if len(val_stripped) <= 50:
                continue
            # Longer text containing "Não consta" = placeholder leaked into sentence
            issue = (
                f"{eid}: campo '{field_name}' contem 'Nao consta' embutido em sentenca "
                f"({len(val_stripped)} chars): '{val_stripped[:80]}...'"
            )
            result["issues"].append(issue)
            result["passed"] = False
            _fail(issue)
            if do_fix:
                # Replace the embedded placeholder with empty marker
                cleaned_val = re.sub(
                    r"N[ãa]o\s+consta\s+no\s+edital\s*(?:dispon[ií]vel)?",
                    "",
                    val_stripped,
                    flags=re.IGNORECASE,
                ).strip()
                if cleaned_val:
                    analise[field_name] = cleaned_val
                else:
                    analise[field_name] = REPLACEMENT_VALUE
                _fix(f"Removido 'Nao consta' embutido de {eid}.{field_name}")

        # 2. Required fields with concrete values
        # data_sessao
        data_sessao_val = str(analise.get("data_sessao") or "").strip()
        if not data_sessao_val or not _is_valid_date(data_sessao_val):
            result["missing_fields"].append({"edital_idx": idx, "edital_id": eid, "field": "data_sessao"})
            issue = f"{eid}: data_sessao ausente ou invalida ('{data_sessao_val}')"
            result["issues"].append(issue)
            result["passed"] = False
            _fail(issue)
            if do_fix and not data_sessao_val:
                analise["data_sessao"] = "Nao consta no edital disponivel"
                _fix(f"Definido data_sessao = 'Nao consta no edital disponivel' em {eid}")

        # criterio_julgamento
        cj_val = str(analise.get("criterio_julgamento") or "").strip()
        if not _check_enum_field(cj_val, CRITERIO_JULGAMENTO_ENUM):
            result["missing_fields"].append({"edital_idx": idx, "edital_id": eid, "field": "criterio_julgamento"})
            issue = f"{eid}: criterio_julgamento invalido ('{cj_val}')"
            result["issues"].append(issue)
            result["passed"] = False
            _fail(issue)

        # regime_execucao
        re_val = str(analise.get("regime_execucao") or "").strip()
        if not _check_enum_field(re_val, REGIME_EXECUCAO_ENUM):
            result["missing_fields"].append({"edital_idx": idx, "edital_id": eid, "field": "regime_execucao"})
            issue = f"{eid}: regime_execucao invalido ('{re_val}')"
            result["issues"].append(issue)
            result["passed"] = False
            _fail(issue)

        # consorcio
        cons_val = str(analise.get("consorcio") or "").strip()
        if not _check_enum_field(cons_val, CONSORCIO_ENUM):
            result["missing_fields"].append({"edital_idx": idx, "edital_id": eid, "field": "consorcio"})
            issue = f"{eid}: consorcio invalido ('{cons_val}')"
            result["issues"].append(issue)
            result["passed"] = False
            _fail(issue)

        # recomendacao_acao — check for "Não consta no edital" placeholder (FALHA 4)
        rec_val = str(analise.get("recomendacao_acao") or "").strip()
        _nao_consta_pattern = re.compile(r"N[ãa]o\s+consta\s+no\s+edital", re.IGNORECASE)
        if _nao_consta_pattern.search(rec_val):
            issue = f"{eid}: recomendacao_acao contém placeholder de campo vazio"
            result["issues"].append(issue)
            result["passed"] = False
            _fail(issue)
            if do_fix:
                cleaned_rec = _nao_consta_pattern.sub("", rec_val).strip(" .,;-")
                analise["recomendacao_acao"] = cleaned_rec if cleaned_rec else "NAO PARTICIPAR"
                _fix(f"Removido placeholder 'Nao consta no edital' de recomendacao_acao em {eid}")
                rec_val = analise["recomendacao_acao"]

        rec_norm = _normalize_text(rec_val)

        # Must be PARTICIPAR or NAO PARTICIPAR, never VERIFICAR/AVALIAR/empty
        is_valid_rec = False
        for valid in RECOMENDACAO_ENUM:
            if rec_norm.startswith(valid) or valid in rec_norm:
                is_valid_rec = True
                break

        if not is_valid_rec or rec_norm in RECOMENDACAO_INVALID:
            result["missing_fields"].append({"edital_idx": idx, "edital_id": eid, "field": "recomendacao_acao"})
            issue = f"{eid}: recomendacao_acao invalida ('{rec_val}')"
            result["issues"].append(issue)
            result["passed"] = False
            _fail(issue)
            if do_fix:
                # Replace invalid recommendations with NAO PARTICIPAR
                analise["recomendacao_acao"] = "NAO PARTICIPAR"
                _fix(f"Substituido recomendacao_acao = 'NAO PARTICIPAR' em {eid}")

        # 3. Recommendation coherence
        status_temporal = edital.get("status_temporal", "")
        if status_temporal == "EXPIRADO" and "nao participar" not in rec_norm:
            issue = f"{eid}: EXPIRADO mas recomendacao nao e NAO PARTICIPAR ('{rec_val}')"
            result["issues"].append(issue)
            result["passed"] = False
            _fail(issue)
            if do_fix:
                analise["recomendacao_acao"] = "NAO PARTICIPAR"
                _fix(f"Corrigido: EXPIRADO -> NAO PARTICIPAR em {eid}")

        if is_sancionada and "nao participar" not in rec_norm:
            issue = f"{eid}: empresa sancionada mas recomendacao nao e NAO PARTICIPAR ('{rec_val}')"
            result["issues"].append(issue)
            result["passed"] = False
            _fail(issue)
            if do_fix:
                analise["recomendacao_acao"] = "NAO PARTICIPAR"
                _fix(f"Corrigido: empresa sancionada -> NAO PARTICIPAR em {eid}")

        # 4. Compatibilidade CNAE = 0% must be NAO PARTICIPAR
        cnae_conf = edital.get("_cnae_confidence")
        if cnae_conf is not None:
            try:
                cnae_pct = float(cnae_conf)
            except (TypeError, ValueError):
                cnae_pct = -1
            if cnae_pct == 0 and "nao participar" not in rec_norm:
                issue = f"{eid}: Compatibilidade CNAE 0% mas recomendacao e PARTICIPAR"
                result["issues"].append(issue)
                result["passed"] = False
                _fail(issue)
                if do_fix:
                    analise["recomendacao_acao"] = "NAO PARTICIPAR"
                    obs = analise.get("observacoes_criticas", "")
                    note = "Objeto incompatível com atividade da empresa (Compatibilidade CNAE 0%)."
                    analise["observacoes_criticas"] = f"{note} {obs}" if obs else note
                    _fix(f"Corrigido: CNAE 0% -> NAO PARTICIPAR em {eid}")

        # 5. Compatibilidade CNAE < 20% AND aderência Baixa must be NAO PARTICIPAR
        victory_fit = edital.get("_victory_fit")
        if cnae_conf is not None and victory_fit is not None:
            try:
                cnae_pct = float(cnae_conf)
                fit_val = float(victory_fit)
            except (TypeError, ValueError):
                cnae_pct, fit_val = -1, -1
            if cnae_pct < 20 and fit_val < 0.15 and "nao participar" not in rec_norm:
                issue = (
                    f"{eid}: Compatibilidade {cnae_pct:.0f}% + Aderência {fit_val:.0%} "
                    f"mas recomendacao e PARTICIPAR"
                )
                result["issues"].append(issue)
                result["passed"] = False
                _fail(issue)
                if do_fix:
                    analise["recomendacao_acao"] = "NAO PARTICIPAR"
                    obs = analise.get("observacoes_criticas", "")
                    note = (
                        f"Duplo sinal de incompatibilidade: Compatibilidade {cnae_pct:.0f}% "
                        f"e Aderência {fit_val:.0%}."
                    )
                    analise["observacoes_criticas"] = f"{note} {obs}" if obs else note
                    _fix(f"Corrigido: CNAE {cnae_pct:.0f}%+fit {fit_val:.0%} -> NAO PARTICIPAR em {eid}")

        # 6. Bid score < 0.20 must be NAO PARTICIPAR
        bid_score = edital.get("_bid_score") or {}
        bid_composite = bid_score.get("_composite")
        if bid_composite is not None:
            try:
                comp_val = float(bid_composite)
            except (TypeError, ValueError):
                comp_val = -1
            if comp_val < 0.20 and "nao participar" not in rec_norm:
                issue = f"{eid}: bid_score {comp_val:.0%} mas recomendacao e PARTICIPAR"
                result["issues"].append(issue)
                result["passed"] = False
                _fail(issue)
                if do_fix:
                    analise["recomendacao_acao"] = "NAO PARTICIPAR"
                    _fix(f"Corrigido: bid_score {comp_val:.0%} -> NAO PARTICIPAR em {eid}")

        # nivel_dificuldade: accept dict (v2) or string (legacy)
        dif = analise.get("nivel_dificuldade")
        if isinstance(dif, dict):
            geral = str(dif.get("geral", "")).upper()
            if geral and geral not in {"BAIXO", "MEDIO", "ALTO"}:
                issue = f"{eid}: nivel_dificuldade.geral invalido: '{geral}'"
                result["issues"].append(issue)
                result["passed"] = False
                _fail(issue)
                if do_fix:
                    dif["geral"] = "MEDIO"
                    _fix(f"{eid}: nivel_dificuldade.geral corrigido para MEDIO")
        elif isinstance(dif, str):
            pass  # Legacy format, handled by existing enum check

    if result["passed"]:
        _ok("Todos os campos obrigatorios preenchidos corretamente")

    return result


# ============================================================
# GATE 5: REPORT COHERENCE
# ============================================================

def gate5_coherence(
    top20: list[dict],
    do_fix: bool = False,
    data_root: dict | None = None,
) -> dict:
    """Validate report coherence: no expired, no sector-incompatible, completeness threshold."""
    result: dict[str, Any] = {
        "passed": True,
        "campos_completos_pct": 0,
        "issues": [],
        "auto_fixed": [],
    }

    indices_to_remove: list[int] = []

    # 1. No EXPIRADO tenders in top20
    for idx, edital in enumerate(top20):
        if edital.get("status_temporal") == "EXPIRADO":
            eid = _edital_id(edital, idx)
            issue = f"{eid}: status_temporal EXPIRADO nao deveria estar no top20"
            result["issues"].append(issue)
            result["passed"] = False
            if do_fix:
                indices_to_remove.append(idx)
                result["auto_fixed"].append(f"Removido EXPIRADO {eid}")
                _fix(f"Removido EXPIRADO {eid}")
            else:
                _fail(issue)

    # 2. NAO PARTICIPAR por motivo legitimo PERMANECE no top20 (cliente precisa da informacao)
    #    So remove se for incompatibilidade semantica (edital fora do setor)
    nao_participar_count = 0
    for idx, edital in enumerate(top20):
        if idx in indices_to_remove:
            continue
        analise = edital.get("analise") or {}
        rec = _normalize_text(str(analise.get("recomendacao_acao") or ""))
        if "nao participar" in rec:
            nao_participar_count += 1
    if nao_participar_count > 0:
        _ok(f"{nao_participar_count} edital(is) NAO PARTICIPAR no top20 (mantidos com justificativa)")

    # 2b. All editais in top20[:20] must have analise populated
    for idx, edital in enumerate(top20[:20]):
        if idx in indices_to_remove:
            continue
        analise = edital.get("analise")
        if not analise:
            eid = _edital_id(edital, idx)
            issue = f"{eid}: edital sem analise no top20"
            result["issues"].append(issue)
            result["passed"] = False
            _fail(issue)

    # 2c. proximos_passos must not reference municipalities of NAO PARTICIPAR editais (FALHA 3)
    # Build set of municipality names from NAO PARTICIPAR editais
    nao_participar_municipios: set[str] = set()
    for edital in top20:
        analise_np = edital.get("analise") or {}
        rec_np = _normalize_text(str(analise_np.get("recomendacao_acao") or ""))
        if "nao participar" in rec_np:
            municipio = str(edital.get("municipio_nome") or edital.get("municipio") or "").strip()
            if municipio:
                nao_participar_municipios.add(_normalize_text(municipio))

    if nao_participar_municipios:
        proximos_passos: list = data_root.get("proximos_passos") if isinstance(data_root, dict) else []
        proximos_passos = proximos_passos if isinstance(proximos_passos, list) else []
        indices_passo_to_remove: list[int] = []
        for passo_idx, passo in enumerate(proximos_passos):
            passo_norm = _normalize_text(str(passo))
            for municipio_norm in nao_participar_municipios:
                if municipio_norm and municipio_norm in passo_norm:
                    issue = (
                        f"proximo_passo #{passo_idx+1} menciona municipio de edital NAO PARTICIPAR"
                        f" ('{municipio_norm}'): '{str(passo)[:80]}'"
                    )
                    result["issues"].append(issue)
                    result["passed"] = False
                    _fail(issue)
                    if do_fix and passo_idx not in indices_passo_to_remove:
                        indices_passo_to_remove.append(passo_idx)
                        result["auto_fixed"].append(f"Removido proximo_passo #{passo_idx+1}")
                        _fix(f"Removido proximo_passo #{passo_idx+1} (municipio NAO PARTICIPAR)")
                    break
        if do_fix and indices_passo_to_remove and isinstance(data_root, dict):
            data_root["proximos_passos"] = [
                p for i, p in enumerate(proximos_passos) if i not in indices_passo_to_remove
            ]

    # 3. All tenders have data_sessao filled or status_temporal defined
    for idx, edital in enumerate(top20):
        if idx in indices_to_remove:
            continue
        analise = edital.get("analise") or {}
        data_sessao = str(analise.get("data_sessao") or "").strip()
        status_temporal = str(edital.get("status_temporal") or "").strip()
        if not data_sessao and not status_temporal:
            eid = _edital_id(edital, idx)
            issue = f"{eid}: sem data_sessao e sem status_temporal"
            result["issues"].append(issue)
            result["passed"] = False
            _fail(issue)

    # Apply removals
    removed = []
    for idx in sorted(set(indices_to_remove), reverse=True):
        removed.append(top20.pop(idx))

    # 4. Calculate campos_completos_pct
    total_fields = 0
    complete_fields = 0
    for edital in top20:
        analise = edital.get("analise") or {}
        for field in REQUIRED_ANALISE_FIELDS:
            total_fields += 1
            val = str(analise.get(field) or "").strip()
            val_norm = _normalize_text(val)
            is_empty = not val or val_norm == "n/a"
            has_forbidden = any(p.search(val) for _, p in FORBIDDEN_WORDS_PATTERNS)
            if not is_empty and not has_forbidden:
                complete_fields += 1

    campos_pct = round(complete_fields / total_fields * 100) if total_fields > 0 else 0
    result["campos_completos_pct"] = campos_pct

    # 5. Threshold check
    if campos_pct < 60:
        issue = f"campos_completos_pct = {campos_pct}% (minimo 60%)"
        result["issues"].append(issue)
        result["passed"] = False
        _fail(issue)
    else:
        _ok(f"campos_completos_pct = {campos_pct}% (>= 60%)")

    if not result["issues"]:
        _ok("Coerencia do relatorio validada")

    return result, removed


# ============================================================
# V4 VALIDATION (new capabilities)
# ============================================================

def validate_v4_fields(top20: list[dict], empresa: dict) -> dict[str, Any]:
    """Validate v4 fields: cnae_confidence, victory_fit, bid_simulation, delta."""
    result: dict[str, Any] = {
        "passed": True,
        "issues": [],
        "stats": {
            "with_confidence": 0,
            "with_fit": 0,
            "with_bid": 0,
            "with_delta": 0,
            "with_structured": 0,
        },
    }

    for idx, edital in enumerate(top20):
        eid = _edital_id(edital, idx)

        # cnae_confidence
        conf = edital.get("cnae_confidence")
        if conf is not None:
            result["stats"]["with_confidence"] += 1
            try:
                conf_f = float(conf)
                if not (0 <= conf_f <= 1):
                    result["issues"].append(f"{eid}: cnae_confidence={conf} fora do range 0-1")
                    result["passed"] = False
            except (ValueError, TypeError):
                result["issues"].append(f"{eid}: cnae_confidence={conf!r} nao e numerico")
                result["passed"] = False

        # victory fit
        fit = edital.get("_victory_fit")
        if fit is not None:
            result["stats"]["with_fit"] += 1
            try:
                fit_f = float(fit)
                if not (0 <= fit_f <= 1):
                    result["issues"].append(f"{eid}: _victory_fit={fit} fora do range 0-1")
                    result["passed"] = False
            except (ValueError, TypeError):
                result["issues"].append(f"{eid}: _victory_fit={fit!r} nao e numerico")
                result["passed"] = False

        # bid simulation
        bid = edital.get("_bid_simulation")
        if bid and isinstance(bid, dict):
            result["stats"]["with_bid"] += 1
            if bid.get("has_data") and bid.get("lance_sugerido", 0) <= 0:
                result["issues"].append(f"{eid}: bid has_data=true mas lance_sugerido <= 0")
                result["passed"] = False

        # delta
        delta = edital.get("_delta_status")
        if delta:
            result["stats"]["with_delta"] += 1
            valid_deltas = {"NOVO", "ATUALIZADO", "VENCENDO", "INALTERADO"}
            if delta not in valid_deltas:
                result["issues"].append(f"{eid}: _delta_status='{delta}' invalido")
                result["passed"] = False

        # structured extraction
        struct = edital.get("_structured_extraction")
        if struct and isinstance(struct, dict):
            result["stats"]["with_structured"] += 1

    return result


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """Entry point for intel-validate CLI."""
    from lib.constants import INTEL_VERSION
    from lib.cli_validation import validate_input_file

    parser = argparse.ArgumentParser(
        description="Validacao programatica dos Gates 2, 4 e 5 do pipeline /intel-busca.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Exemplos:
  python scripts/intel-validate.py --input data.json
  python scripts/intel-validate.py --input data.json --fix
  python scripts/intel-validate.py --input data.json --fix --strict""",
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="JSON de entrada com top20[].analise (output do intel-analyze.py). Deve existir.",
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Caminho para salvar o relatorio de validacao JSON (default: <input>-validation.json)",
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Auto-corrigir problemas encontrados e salvar JSON corrigido in-place. "
             "Corrige: datas expiradas, campos vazios, recomendacoes incoerentes.",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Exit code 1 se qualquer gate falhar (para uso em CI/CD pipelines)",
    )
    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {INTEL_VERSION}")
    args = parser.parse_args()

    # ── Validate arguments ──
    validate_input_file(args.input)

    # Load input JSON
    input_path = Path(args.input)

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error("JSON invalido em %s: %s", input_path, e)
        sys.exit(2)

    if not isinstance(data, dict):
        logger.error("JSON raiz deve ser um objeto (dict)")
        sys.exit(2)

    top20 = data.get("top20", [])
    if not isinstance(top20, list):
        logger.error("campo 'top20' deve ser uma lista")
        sys.exit(2)

    empresa = data.get("empresa", {})
    if not isinstance(empresa, dict):
        logger.error("campo 'empresa' deve ser um objeto (dict)")
        sys.exit(2)

    if not top20:
        logger.error("top20 vazio ou ausente no JSON")
        sys.exit(2)

    logger.info("Validando %d editais no top20...", len(top20))
    logger.info("Empresa: %s (CNPJ: %s)", empresa.get("razao_social", "N/A"), empresa.get("cnpj", "N/A"))

    # ── GATE 2: Semantic Compatibility ──
    _header("GATE 2: Compatibilidade Semantica")
    gate2_result, gate2_decisions, gate2_removed = gate2_semantic(top20, empresa, do_fix=args.fix)

    # ── GATE 4: Analysis Completeness ──
    _header("GATE 4: Completude da Analise")
    gate4_result = gate4_completeness(top20, empresa, do_fix=args.fix)

    # ── GATE 5: Report Coherence ──
    _header("GATE 5: Coerencia do Relatorio")
    gate5_result, gate5_removed = gate5_coherence(top20, do_fix=args.fix, data_root=data)

    # ── V4 Fields Validation ──
    _header("V4: Campos de Inteligencia Avancada")
    v4_result = validate_v4_fields(top20, empresa)
    stats = v4_result["stats"]
    logger.info("Confianca CNAE:     %d/%d editais", stats["with_confidence"], len(top20))
    logger.info("Aderencia perfil:   %d/%d editais", stats["with_fit"], len(top20))
    logger.info("Simulacao lance:    %d/%d editais", stats["with_bid"], len(top20))
    logger.info("Status delta:       %d/%d editais", stats["with_delta"], len(top20))
    logger.info("Extracao estrut.:   %d/%d editais", stats["with_structured"], len(top20))
    if v4_result["issues"]:
        for issue in v4_result["issues"]:
            _fail(issue)
    else:
        _ok("Campos v4 validos")

    # Combine all removed editais
    all_removed = []
    for e in gate2_removed:
        all_removed.append({
            "gate": "gate2",
            "objeto": (e.get("objeto") or "")[:80],
            "valor_estimado": e.get("valor_estimado"),
        })
    for e in gate5_removed:
        all_removed.append({
            "gate": "gate5",
            "objeto": (e.get("objeto") or "")[:80],
            "valor_estimado": e.get("valor_estimado"),
        })

    # Build validation report
    overall_passed = gate2_result["passed"] and gate4_result["passed"] and gate5_result["passed"]

    report: dict[str, Any] = {
        "validation_timestamp": datetime.now(timezone.utc).isoformat(),
        "gates": {
            "gate2_semantic": {
                "passed": gate2_result["passed"],
                "issues": gate2_result["issues"],
                "auto_fixed": gate2_result["auto_fixed"],
            },
            "gate4_completeness": {
                "passed": gate4_result["passed"],
                "issues": gate4_result["issues"],
                "forbidden_words_found": gate4_result["forbidden_words_found"],
                "missing_fields": gate4_result["missing_fields"],
            },
            "gate5_coherence": {
                "passed": gate5_result["passed"],
                "campos_completos_pct": gate5_result["campos_completos_pct"],
                "issues": gate5_result["issues"],
            },
            "v4_fields": {
                "passed": v4_result["passed"],
                "stats": v4_result["stats"],
                "issues": v4_result["issues"],
            },
        },
        "overall_passed": overall_passed,
        "top20_removed": all_removed,
        "top20_warnings": [],
    }

    # Collect warnings (non-blocking issues)
    remaining_count = len(top20)
    if remaining_count < 5:
        report["top20_warnings"].append(
            f"Apenas {remaining_count} editais restantes no top20 apos validacao"
        )
    if gate5_result["campos_completos_pct"] < 80:
        report["top20_warnings"].append(
            f"campos_completos_pct = {gate5_result['campos_completos_pct']}% — abaixo do ideal (80%)"
        )

    # ── Summary ──
    _header("RESUMO")
    total_issues = (
        len(gate2_result["issues"])
        + len(gate4_result["issues"])
        + len(gate5_result["issues"])
    )
    logger.info("Gate 2 (Semantica):    %s", "PASS" if gate2_result["passed"] else "FAIL")
    logger.info("Gate 4 (Completude):   %s", "PASS" if gate4_result["passed"] else "FAIL")
    logger.info("Gate 5 (Coerencia):    %s", "PASS" if gate5_result["passed"] else "FAIL")
    logger.info("Campos completos:      %s%%", gate5_result["campos_completos_pct"])
    logger.info("Issues encontradas:    %d", total_issues)
    logger.info("Editais removidos:     %d", len(all_removed))
    logger.info("Top20 restante:        %d", remaining_count)
    logger.info("Overall:               %s", "PASS" if overall_passed else "FAIL")

    # Save validation report
    if args.output:
        output_path = Path(args.output)
    else:
        stem = input_path.stem
        output_path = input_path.parent / f"{stem}-validation.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Relatorio salvo em: {output_path}")

    # Save fixed JSON in-place if --fix
    if args.fix:
        # Store gate2 decisions in the JSON for audit trail
        if gate2_decisions:
            existing_decisions = data.get("gate2_decisions", [])
            existing_decisions.extend(gate2_decisions)
            data["gate2_decisions"] = existing_decisions

        # Update top20 in data (already mutated in-place by removals)
        data["top20"] = top20

        with open(input_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"JSON corrigido salvo em: {input_path}")  # user-facing

    # Exit code logic:
    # --fix + still failing = exit 1 (fix didn't resolve everything)
    # --strict = exit 1 on ANY remaining failure
    if args.fix and not overall_passed:
        logger.error("EXIT 1: --fix usado mas issues permanecem apos correcao")
        sys.exit(1)
    if args.strict and not overall_passed:
        logger.error("EXIT 1: --strict e gates falharam")
        sys.exit(1)


if __name__ == "__main__":
    main()
