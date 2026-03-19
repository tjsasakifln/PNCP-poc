#!/usr/bin/env python3
"""
Orquestrador do pipeline Intel-Busca com quality gates.

Executa o pipeline completo de coleta e análise de licitações com
verificações de qualidade entre cada etapa.

Pipeline:
  Collect → [GATE 1: Cobertura] → Enrich → [GATE 2: Cadastral] →
  LLM Gate → [GATE 3: Ruído] → Extract Docs → [GATE 4: Conteúdo] →
  Analyze (manual) → [GATE 5: Recomendação] → Excel + PDF

Usage:
    python scripts/intel-pipeline.py --cnpj 01721078000168 --ufs SC,PR,RS
    python scripts/intel-pipeline.py --cnpj 01721078000168 --ufs SC,PR,RS --dias 30 --top 20
    python scripts/intel-pipeline.py --cnpj 01721078000168 --ufs SC --skip-sicaf
    python scripts/intel-pipeline.py --cnpj 01721078000168 --ufs SC --from-step 6
    python scripts/intel-pipeline.py --cnpj 01721078000168 --ufs SC --no-cache
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ============================================================
# Windows console encoding fix — force UTF-8 even if already wrapped
# ============================================================
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "buffer"):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "buffer"):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except (ValueError, AttributeError):
        pass

# ============================================================
# CONSTANTS
# ============================================================

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
INTEL_DIR = PROJECT_ROOT / "docs" / "intel"

# Step timeouts (seconds)
TIMEOUT_COLLECT = 600      # 10 min — exhaustive PNCP search
TIMEOUT_ENRICH = 300       # 5 min
TIMEOUT_LLM_GATE = 120     # 2 min — pure keyword logic
TIMEOUT_EXTRACT_DOCS = 600  # 10 min — downloads from PNCP
TIMEOUT_EXCEL = 60
TIMEOUT_PDF = 60

# Colors (ANSI codes for terminal)
_C_RESET = "\033[0m"
_C_GREEN = "\033[92m"
_C_RED = "\033[91m"
_C_YELLOW = "\033[93m"
_C_CYAN = "\033[96m"
_C_BOLD = "\033[1m"
_C_MAGENTA = "\033[95m"

# ============================================================
# HELPERS
# ============================================================

def _c(text: str, color: str) -> str:
    """Wrap text in ANSI color if stdout is a terminal."""
    if sys.stdout.isatty() if hasattr(sys.stdout, "isatty") else False:
        return f"{color}{text}{_C_RESET}"
    return text


def _ok(text: str) -> str:
    return _c(text, _C_GREEN)


def _err(text: str) -> str:
    return _c(text, _C_RED)


def _warn(text: str) -> str:
    return _c(text, _C_YELLOW)


def _info(text: str) -> str:
    return _c(text, _C_CYAN)


def _bold(text: str) -> str:
    return _c(text, _C_BOLD)


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def _slug(name: str) -> str:
    """Convert razao_social to slug: lowercase, no accents, hyphens."""
    name = _strip_accents(name.lower().strip())
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name[:40]


def _clean_cnpj(cnpj: str) -> str:
    return re.sub(r"\D", "", cnpj)


def _now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _fmt_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}m{s:02d}s"


def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _find_latest_json(cnpj14: str) -> Path | None:
    """Find the most recently modified intel-{cnpj}-*.json in docs/intel/."""
    INTEL_DIR.mkdir(parents=True, exist_ok=True)
    candidates = list(INTEL_DIR.glob(f"intel-{cnpj14}-*.json"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _run_script(
    script_name: str,
    args: list[str],
    timeout: int,
    step_label: str,
) -> subprocess.CompletedProcess:
    """Run a Python script via subprocess with PYTHONIOENCODING=utf-8."""
    script_path = str(SCRIPTS_DIR / script_name)
    cmd = [sys.executable, script_path] + args
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    print(f"  $ {' '.join(cmd[:4])} {' '.join(cmd[4:])[:100]}")
    t0 = time.time()
    try:
        result = subprocess.run(
            cmd,
            env=env,
            timeout=timeout,
            check=True,
            capture_output=False,  # allow live output
        )
        elapsed = time.time() - t0
        print(f"  {_ok('OK')} {step_label} concluído em {_fmt_duration(elapsed)}")
        return result
    except subprocess.TimeoutExpired:
        elapsed = time.time() - t0
        print(_err(f"\n  ERRO: {step_label} excedeu timeout de {timeout}s ({_fmt_duration(elapsed)})"))
        raise
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - t0
        print(_err(f"\n  ERRO: {step_label} falhou com código {e.returncode} ({_fmt_duration(elapsed)})"))
        raise


# ============================================================
# QUALITY GATE TYPES
# ============================================================

GateResult = tuple[bool, list[str], list[str]]  # (passed, issues, auto_fixed)


def _gate_header(name: str, passed: bool) -> None:
    icon = _ok("PASSED") if passed else _err("FAILED")
    label = _bold(f"[{name}]")
    print(f"\n{label} {icon}")


def _gate_item(msg: str, level: str = "ok") -> None:
    prefix = {
        "ok": _ok("  ✓"),
        "warn": _warn("  ⚠"),
        "err": _err("  ✗"),
        "fix": _info("  →"),
        "info": "   ",
    }.get(level, "   ")
    print(f"{prefix} {msg}")


# ============================================================
# GATE 1: COBERTURA (after collect)
# ============================================================

def gate1_cobertura(data: dict, ufs_requested: list[str]) -> GateResult:
    """Validate coverage: all UFs have data, total > 0, empresa OK."""
    passed = True
    issues: list[str] = []
    fixed: list[str] = []

    editais = data.get("editais", [])
    total_bruto = len(editais)
    empresa = data.get("empresa", {})
    source = empresa.get("_source", {})
    stats = data.get("estatisticas", {})

    _gate_header("GATE 1: Cobertura", True)  # print header first, update after checks

    # 1. empresa._source.status
    empresa_status = source.get("status", "")
    if empresa_status == "API_FAILED":
        issues.append(f"empresa._source.status = API_FAILED — dados cadastrais indisponíveis")
        _gate_item("empresa._source.status = API_FAILED — ABORTANDO", "err")
        passed = False
    else:
        _gate_item(f"Empresa OK: {empresa.get('razao_social', '?')} ({empresa_status or 'OK'})")

    # 2. Total bruto
    _gate_item(f"{total_bruto} editais brutos coletados")
    if total_bruto == 0:
        issues.append("Zero editais brutos — possível falha de coleta ou período muito curto")
        _gate_item("Zero editais — ABORTANDO", "err")
        passed = False
        return passed, issues, fixed

    # 3. UFs coverage
    ufs_with_data = set(e.get("uf", "") for e in editais if e.get("uf"))
    ufs_requested_set = set(uf.upper() for uf in ufs_requested)
    missing_ufs = ufs_requested_set - ufs_with_data
    if missing_ufs:
        issues.append(f"UFs sem dados: {', '.join(sorted(missing_ufs))}")
        _gate_item(f"UFs sem dados: {', '.join(sorted(missing_ufs))} (pode ser zero editais no período)", "warn")
    else:
        _gate_item(f"{len(ufs_with_data)}/{len(ufs_requested_set)} UFs com dados")

    # 4. Compatíveis count
    compat = [e for e in editais if e.get("cnae_compatible")]
    needs_review = [e for e in editais if e.get("needs_llm_review")]
    _gate_item(f"{len(compat)} compatíveis, {len(needs_review)} pendentes revisão LLM")

    # 5. Pagination exhausted warnings
    pagination_exhausted = stats.get("pncp_pagination_exhausted", [])
    if pagination_exhausted:
        for pe in pagination_exhausted[:5]:
            issues.append(f"Paginação esgotada: mod={pe.get('modalidade')} uf={pe.get('uf')} — dados possivelmente incompletos")
            _gate_item(
                f"Paginação esgotada: mod={pe.get('modalidade')} uf={pe.get('uf')} — dados possivelmente incompletos",
                "warn",
            )
        if len(pagination_exhausted) > 5:
            _gate_item(f"... e mais {len(pagination_exhausted) - 5} paginações esgotadas", "warn")

    # Final
    if not issues:
        _gate_item("Cobertura completa sem avisos")
    elif passed and all("Paginação" in i or "UFs sem dados" in i for i in issues):
        pass  # warnings only, not fatal

    return passed, issues, fixed


# ============================================================
# GATE 2: CADASTRAL (after enrich)
# ============================================================

def gate2_cadastral(data: dict, top_n: int) -> GateResult:
    """Validate cadastral enrichment: sanctions, SICAF, enrichment coverage."""
    passed = True
    issues: list[str] = []
    fixed: list[str] = []

    empresa = data.get("empresa", {})
    editais = data.get("editais", [])

    _gate_header("GATE 2: Cadastral", True)

    # 1. Sanctions check
    sancionada = empresa.get("sancionada", False)
    if sancionada:
        issues.append("CRITICAL: empresa SANCIONADA — todas recomendações marcadas como NÃO RECOMENDADO")
        _gate_item(
            "EMPRESA SANCIONADA (CEIS/CNEP/CEPIM/CEAF) — recomendações bloqueadas",
            "err",
        )
        # Mark all editais as NÃO RECOMENDADO
        for e in editais:
            e["recomendacao_override"] = "NÃO RECOMENDADO — empresa sancionada"
        fixed.append("Todos os editais marcados com recomendacao_override = NÃO RECOMENDADO")
        # Don't abort — continue with marked data
    else:
        _gate_item("Empresa sem sanções ativas (CEIS/CNEP/CEPIM/CEAF)")

    # 2. SICAF restrictions
    sicaf = empresa.get("sicaf", {})
    sicaf_restricoes = sicaf.get("restricoes", []) if isinstance(sicaf, dict) else []
    if sicaf_restricoes:
        for r in sicaf_restricoes:
            issues.append(f"SICAF restrição: {r}")
            _gate_item(f"SICAF restrição: {r}", "warn")
    elif sicaf.get("status") == "OK":
        _gate_item("SICAF: sem restrições")
    else:
        _gate_item(f"SICAF: {sicaf.get('status', 'não verificado')}", "info")

    # 3. Enrichment coverage of top candidates
    # Top candidates = cnae_compatible, sorted by valor desc
    compat = sorted(
        [e for e in editais if e.get("cnae_compatible")],
        key=lambda x: float(x.get("valor_estimado") or 0),
        reverse=True,
    )
    top_candidates = compat[:top_n]

    if top_candidates:
        enriched_count = sum(
            1 for e in top_candidates
            if e.get("distancia_km") is not None or e.get("custo_proposta") is not None
        )
        coverage_ratio = enriched_count / len(top_candidates)
        _gate_item(
            f"Enriquecimento: {enriched_count}/{len(top_candidates)} top candidatos com distância/custo "
            f"({coverage_ratio*100:.0f}%)"
        )
        if coverage_ratio < 0.5:
            issues.append(
                f"Baixo enriquecimento: apenas {enriched_count}/{len(top_candidates)} candidatos enriquecidos"
            )
            _gate_item(
                "< 50% enriquecidos — considere re-executar intel-enrich.py com --max-editais maior",
                "warn",
            )
    else:
        _gate_item("Nenhum candidato compatível para verificar cobertura", "warn")

    return passed, issues, fixed


# ============================================================
# GATE 3: RUÍDO (after llm-gate)
# ============================================================

def gate3_ruido(data: dict) -> GateResult:
    """Validate noise gate: compatible ratio, spot samples, zero pending."""
    import random

    passed = True
    issues: list[str] = []
    fixed: list[str] = []

    editais = data.get("editais", [])
    total = len(editais)

    _gate_header("GATE 3: Ruído", True)

    if total == 0:
        issues.append("Zero editais — falha anterior")
        _gate_item("Zero editais", "err")
        return False, issues, fixed

    compat = [e for e in editais if e.get("cnae_compatible")]
    incompat = [e for e in editais if not e.get("cnae_compatible")]
    needs_review = [e for e in editais if e.get("needs_llm_review")]

    ratio = len(compat) / total
    _gate_item(f"{len(compat)}/{total} compatíveis ({ratio*100:.1f}%)")

    # 1. Ratio sanity check
    if ratio < 0.05:
        issues.append(
            f"Ratio compatível muito baixo ({ratio*100:.1f}%) — possível problema de keywords/exclusões"
        )
        _gate_item(
            f"Ratio < 5% ({ratio*100:.1f}%) — verifique keywords no intel-collect.py",
            "warn",
        )
    elif ratio > 0.80:
        issues.append(
            f"Ratio compatível muito alto ({ratio*100:.1f}%) — possível ausência de filtros negativos"
        )
        _gate_item(
            f"Ratio > 80% ({ratio*100:.1f}%) — verifique se filtros negativos estão aplicados",
            "warn",
        )
    else:
        _gate_item(f"Ratio dentro do intervalo esperado (5%–80%)")

    # 2. Needs review = 0
    if needs_review:
        issues.append(f"{len(needs_review)} editais ainda marcados como needs_llm_review")
        _gate_item(f"{len(needs_review)} pendentes LLM review — gate não zerou", "err")
        passed = False
    else:
        _gate_item("Zero pendentes LLM review — gate concluído")

    # 3. Spot check: 5 compatible + 5 incompatible
    sample_compat = random.sample(compat, min(5, len(compat)))
    sample_incompat = random.sample(incompat, min(5, len(incompat)))

    if sample_compat:
        print("\n  Amostra COMPATÍVEIS (spot-check manual):")
        for e in sample_compat:
            obj = (e.get("objeto") or "")[:100]
            uf = e.get("uf", "?")
            val = float(e.get("valor_estimado") or 0)
            src = e.get("llm_review_result", e.get("keyword_match_source", "?"))
            print(f"    [{uf}] R${val:>12,.0f} | {obj[:80]}")
            print(f"           source={src}")

    if sample_incompat:
        print("\n  Amostra INCOMPATÍVEIS (spot-check manual):")
        for e in sample_incompat:
            obj = (e.get("objeto") or "")[:100]
            uf = e.get("uf", "?")
            val = float(e.get("valor_estimado") or 0)
            src = e.get("llm_review_result", e.get("keyword_match_source", "?"))
            print(f"    [{uf}] R${val:>12,.0f} | {obj[:80]}")
            print(f"           source={src}")

    return passed, issues, fixed


# ============================================================
# GATE 4: CONTEÚDO (after extract-docs)
# ============================================================

def gate4_conteudo(data: dict, top_n: int) -> GateResult:
    """Validate document extraction coverage and quality for top-N editais."""
    passed = True
    issues: list[str] = []
    fixed: list[str] = []

    editais = data.get("editais", [])

    _gate_header("GATE 4: Conteúdo", True)

    compat = sorted(
        [e for e in editais if e.get("cnae_compatible")],
        key=lambda x: float(x.get("valor_estimado") or 0),
        reverse=True,
    )
    top20 = compat[:top_n]

    if not top20:
        issues.append("Nenhum edital compatível no top20")
        _gate_item("Top20 vazio", "err")
        return False, issues, fixed

    # 1. Coverage: how many have texto_documentos
    with_docs = [e for e in top20 if e.get("texto_documentos")]
    coverage = len(with_docs) / len(top20)
    _gate_item(f"Cobertura de documentos: {len(with_docs)}/{len(top20)} ({coverage*100:.0f}%)")
    if coverage < 0.5:
        issues.append(f"Baixa cobertura de documentos: {len(with_docs)}/{len(top20)}")
        _gate_item("< 50% com documentos — análise será limitada", "warn")

    # 2. Watermark detection: text that is repetition of short lines
    watermark_count = 0
    for e in with_docs:
        texto = e.get("texto_documentos", "")
        if not texto:
            continue
        lines = [l.strip() for l in texto.split("\n") if l.strip()]
        if len(lines) < 5:
            continue
        # Check if > 70% of lines are the same (watermark/header repeated)
        from collections import Counter
        line_counts = Counter(lines)
        most_common_count = line_counts.most_common(1)[0][1] if line_counts else 0
        if most_common_count / len(lines) > 0.7:
            watermark_count += 1
            e["_doc_extraction_warning"] = "watermark_suspected"
            issues.append(f"Possível texto de marca-d'água em: {(e.get('objeto','')[:60])}")
            _gate_item(f"Extração suspeita (watermark?): {(e.get('objeto','')[:60])}", "warn")

    if watermark_count == 0 and with_docs:
        _gate_item("Nenhuma extração suspeita de watermark detectada")

    # 3. Duplicate check in top20 by objeto normalization
    def _norm_obj(s: str) -> str:
        s = _strip_accents((s or "").lower().strip())
        s = re.sub(r"\s+", " ", s)
        return s[:120]

    seen_objs: dict[str, int] = {}  # normalized_obj -> first index
    dup_indices: list[int] = []
    for i, e in enumerate(top20):
        norm = _norm_obj(e.get("objeto", ""))
        if norm in seen_objs:
            dup_indices.append(i)
            issues.append(f"Duplicata no top20: pos {i+1} == pos {seen_objs[norm]+1} ({norm[:60]})")
            _gate_item(f"Duplicata detectada: posição {i+1} = posição {seen_objs[norm]+1}", "warn")
        else:
            seen_objs[norm] = i

    if dup_indices:
        # Remove duplicates (keep first occurrence)
        indices_to_remove = sorted(dup_indices, reverse=True)
        for idx in indices_to_remove:
            removed = top20.pop(idx)
            fixed.append(f"Removida duplicata: {(removed.get('objeto','')[:60])}")
        _gate_item(f"Removidas {len(indices_to_remove)} duplicatas do top20", "fix")

        # Backfill from remaining compatible editais
        already_in = {id(e) for e in top20}
        backfill_pool = [e for e in compat[top_n:] if id(e) not in already_in]
        added = 0
        for candidate in backfill_pool:
            if len(top20) >= top_n:
                break
            norm = _norm_obj(candidate.get("objeto", ""))
            if norm not in seen_objs:
                top20.append(candidate)
                seen_objs[norm] = len(top20) - 1
                added += 1
        if added:
            _gate_item(f"Backfill: {added} editais adicionados para repor duplicatas", "fix")
            fixed.append(f"Backfill: {added} editais adicionados")

    elif not dup_indices:
        _gate_item("Nenhuma duplicata no top20")

    return passed, issues, fixed


# ============================================================
# GATE 5: RECOMENDAÇÃO (before Excel/PDF)
# ============================================================

def gate5_recomendacao(data: dict, top_n: int) -> GateResult:
    """Final quality gate: zero NÃO PARTICIPAR, zero duplicates, capacity check."""
    passed = True
    issues: list[str] = []
    fixed: list[str] = []

    editais = data.get("editais", [])
    empresa = data.get("empresa", {})

    _gate_header("GATE 5: Recomendação", True)

    # Determine capital social for capacity check
    capital_social = 0.0
    try:
        cs_raw = str(empresa.get("capital_social") or "0").strip()
        # Handle Brazilian format: "1.232.000,00" or "1232000,00" or "1232000.00"
        if "," in cs_raw:
            # Brazilian decimal: remove thousand separators (dots), convert comma to dot
            cs_raw = cs_raw.replace(".", "").replace(",", ".")
        capital_social = float(cs_raw)
    except Exception:
        capital_social = 0.0

    capacity_limit = capital_social * 10 if capital_social > 0 else float("inf")

    _gate_item(
        f"Capital social: R${capital_social:,.2f} → capacidade máxima: R${capacity_limit:,.2f}"
        if capital_social > 0 else "Capital social não disponível — verificação de capacidade ignorada"
    )

    # Work with top-N compatible editais
    compat = sorted(
        [e for e in editais if e.get("cnae_compatible")],
        key=lambda x: float(x.get("valor_estimado") or 0),
        reverse=True,
    )
    top20 = list(compat[:top_n])
    remaining_pool = list(compat[top_n:])

    def _norm_obj(s: str) -> str:
        s = _strip_accents((s or "").lower().strip())
        return re.sub(r"\s+", " ", s)[:120]

    removed: list[dict] = []

    # Pass 1: Remove NÃO PARTICIPAR recommendations
    nao_participar = [
        e for e in top20
        if "NÃO PARTICIPAR" in (e.get("analise", {}) or {}).get("recomendacao_acao", "").upper()
        or "NÃO PARTICIPAR" in (e.get("recomendacao_override", "") or "").upper()
    ]
    if nao_participar:
        for e in nao_participar:
            top20.remove(e)
            removed.append(e)
            obj = (e.get("objeto") or "")[:60]
            issues.append(f"NÃO PARTICIPAR removido: {obj}")
            _gate_item(f"NÃO PARTICIPAR removido: {obj}", "fix")
        fixed.append(f"Removidos {len(nao_participar)} editais NÃO PARTICIPAR")
    else:
        _gate_item("Nenhum NÃO PARTICIPAR no top20")

    # Pass 2: Remove duplicates
    seen_objs: dict[str, int] = {}
    dup_indices = []
    for i, e in enumerate(top20):
        norm = _norm_obj(e.get("objeto", ""))
        if norm in seen_objs:
            dup_indices.append(i)
        else:
            seen_objs[norm] = i

    if dup_indices:
        for idx in sorted(dup_indices, reverse=True):
            removed.append(top20.pop(idx))
            issues.append(f"Duplicata removida em posição {idx+1}")
            _gate_item(f"Duplicata removida em posição {idx+1}", "fix")
        fixed.append(f"Removidas {len(dup_indices)} duplicatas")
    else:
        _gate_item("Nenhuma duplicata")

    # Pass 3: Capacity check (10x capital social)
    if capital_social > 0:
        over_capacity = [
            e for e in top20
            if float(e.get("valor_estimado") or 0) > capacity_limit
        ]
        if over_capacity:
            for e in over_capacity:
                val = float(e.get("valor_estimado") or 0)
                obj = (e.get("objeto") or "")[:60]
                top20.remove(e)
                removed.append(e)
                issues.append(f"Acima de 10x capital (R${val:,.0f} > R${capacity_limit:,.0f}): {obj}")
                _gate_item(
                    f"Acima capacidade: R${val:>12,.0f} > limite R${capacity_limit:,.0f} → removido",
                    "fix",
                )
            fixed.append(f"Removidos {len(over_capacity)} editais acima da capacidade")
        else:
            _gate_item(f"Todos os editais dentro da capacidade (≤ R${capacity_limit:,.0f})")

    # Pass 4: Backfill from remaining pool
    already_norms = {_norm_obj(e.get("objeto", "")) for e in top20}
    added = 0
    for candidate in remaining_pool:
        if len(top20) >= top_n:
            break
        # Skip if NÃO PARTICIPAR or over capacity
        if "NÃO PARTICIPAR" in (candidate.get("analise", {}) or {}).get("recomendacao_acao", "").upper():
            continue
        val = float(candidate.get("valor_estimado") or 0)
        if capital_social > 0 and val > capacity_limit:
            continue
        norm = _norm_obj(candidate.get("objeto", ""))
        if norm not in already_norms:
            top20.append(candidate)
            already_norms.add(norm)
            added += 1
            candidate["_backfill"] = True

    if added:
        _gate_item(f"Backfill: {added} editais adicionados (marcados _backfill=True)", "fix")
        fixed.append(f"Backfill: {added} novos editais")
        if added > 0:
            issues.append(
                f"Backfill: {added} editais adicionados — precisam de análise manual (sem campo 'analise')"
            )

    # Pass 5: Missing 'analise' field
    missing_analise = [e for e in top20 if not e.get("analise")]
    if missing_analise:
        issues.append(f"{len(missing_analise)} editais sem campo 'analise' — revisão manual necessária")
        _gate_item(
            f"{len(missing_analise)} editais sem 'analise' — revise manualmente",
            "warn",
        )
        for e in missing_analise:
            e["_analise_pending"] = True
    else:
        _gate_item("Todos os editais com campo 'analise'")

    # Pass 6: Top 3 sanity check
    top3 = top20[:3]
    top3_ok = []
    for e in top3:
        analise = e.get("analise") or {}
        rec = (analise.get("recomendacao_acao") or "").upper()
        has_participar = "PARTICIPAR" in rec and "NÃO" not in rec
        top3_ok.append(has_participar)
        obj = (e.get("objeto") or "")[:55]
        val = float(e.get("valor_estimado") or 0)
        status = _ok("PARTICIPAR") if has_participar else _warn("sem recomendação clara")
        _gate_item(f"Top{top3.index(e)+1}: R${val:>12,.0f} | {obj} → {status}")

    if top3 and not any(top3_ok):
        issues.append("Nenhum dos top 3 tem recomendação PARTICIPAR clara")
        _gate_item("AVISO: Nenhum dos top 3 recomenda participar claramente", "warn")

    # Final scorecard
    total_removed = len(nao_participar) + len(dup_indices) + (
        len(over_capacity) if capital_social > 0 else 0
    )
    print(f"\n  {_bold('Scorecard Final:')}")
    print(f"    Top{top_n} final: {len(top20)} editais")
    print(f"    Removidos: {total_removed} (NÃO PARTICIPAR + duplicatas + capacidade)")
    print(f"    Backfill: {added}")
    print(f"    Sem análise: {len(missing_analise)}")

    return passed, issues, fixed


# ============================================================
# SCORECARD PRINTER
# ============================================================

def print_gate_summary(gate_name: str, passed: bool, issues: list[str], fixed: list[str]) -> None:
    if passed and not issues:
        print(_ok(f"  → {gate_name}: PASSED sem problemas"))
    elif passed:
        print(_warn(f"  → {gate_name}: PASSED com {len(issues)} avisos, {len(fixed)} auto-correções"))
    else:
        print(_err(f"  → {gate_name}: FAILED — {len(issues)} problemas críticos"))


# ============================================================
# MAIN PIPELINE
# ============================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Orquestrador Intel-Busca com quality gates.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--cnpj", required=True, help="CNPJ da empresa (com ou sem formatação)")
    parser.add_argument("--ufs", required=True, help="UFs separadas por vírgula (ex: SC,PR,RS)")
    parser.add_argument("--dias", type=int, default=30, help="Período de busca em dias (default: 30)")
    parser.add_argument("--top", type=int, default=20, help="Top-N editais para análise (default: 20)")
    parser.add_argument("--skip-sicaf", action="store_true", help="Pular coleta SICAF")
    parser.add_argument(
        "--from-step", type=int, default=1, metavar="N",
        help="Retomar a partir do passo N (1-7). Requer JSON existente em docs/intel/",
    )
    parser.add_argument(
        "--no-cache", action="store_true",
        help="Ignorar cache do PNCP (recoleta tudo)"
    )
    args = parser.parse_args()

    cnpj14 = _clean_cnpj(args.cnpj)
    if len(cnpj14) != 14:
        print(_err(f"CNPJ inválido: {args.cnpj} (deve ter 14 dígitos)"))
        return 1

    ufs = [u.strip().upper() for u in args.ufs.split(",") if u.strip()]
    if not ufs:
        print(_err("--ufs não pode ser vazio"))
        return 1

    today = _now_str()
    INTEL_DIR.mkdir(parents=True, exist_ok=True)

    print(_bold(f"\n{'='*60}"))
    print(_bold(f"  Intel Pipeline — CNPJ {cnpj14} | UFs {','.join(ufs)}"))
    print(_bold(f"  Dias: {args.dias} | Top: {args.top} | Data: {today}"))
    print(_bold(f"{'='*60}\n"))

    pipeline_t0 = time.time()
    step_times: dict[str, float] = {}
    all_gate_results: dict[str, tuple[bool, list[str], list[str]]] = {}

    # ── Determine JSON path ──────────────────────────────────────
    # After step 1 (collect), we know the slug from razao_social.
    # For --from-step >= 2, we auto-detect the most recent JSON.

    json_path: Path | None = None

    if args.from_step >= 2:
        json_path = _find_latest_json(cnpj14)
        if json_path is None:
            print(_err(f"--from-step {args.from_step}: nenhum JSON encontrado em {INTEL_DIR} para CNPJ {cnpj14}"))
            return 1
        print(_info(f"Retomando de: {json_path}\n"))

    # ── STEP 1: COLLECT ─────────────────────────────────────────
    if args.from_step <= 1:
        step_label = "Step 1: Collect"
        print(_bold(f"\n[{step_label}]"))
        t0 = time.time()

        collect_args = [
            "--cnpj", cnpj14,
            "--ufs", ",".join(ufs),
            "--dias", str(args.dias),
        ]
        # intel-collect.py uses --output; we let it auto-name so we can find it after
        try:
            _run_script("intel-collect.py", collect_args, TIMEOUT_COLLECT, step_label)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return 1

        step_times["collect"] = time.time() - t0

        # Find the JSON just created
        json_path = _find_latest_json(cnpj14)
        if json_path is None:
            print(_err("Collect não gerou JSON — verifique erros acima"))
            return 1
        print(_info(f"  JSON criado: {json_path}"))

        # ── GATE 1: COBERTURA ────────────────────────────────────
        data = _load_json(json_path)
        passed, issues, fixed = gate1_cobertura(data, ufs)
        all_gate_results["gate1"] = (passed, issues, fixed)
        print_gate_summary("Gate 1", passed, issues, fixed)
        if not passed:
            print(_err("\nPipeline ABORTADO no Gate 1. Corrija os problemas e tente novamente."))
            return 1

    # ── STEP 2: ENRICH ──────────────────────────────────────────
    if args.from_step <= 2:
        step_label = "Step 2: Enrich"
        print(_bold(f"\n[{step_label}]"))
        t0 = time.time()

        enrich_args = ["--input", str(json_path)]
        if args.skip_sicaf:
            enrich_args.append("--skip-sicaf")

        try:
            _run_script("intel-enrich.py", enrich_args, TIMEOUT_ENRICH, step_label)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            print(_warn("  Step 2 falhou — continuando com dados parciais"))

        step_times["enrich"] = time.time() - t0

        # ── GATE 2: CADASTRAL ────────────────────────────────────
        data = _load_json(json_path)
        passed, issues, fixed = gate2_cadastral(data, args.top)
        # Save if any auto-fixes were applied
        if fixed:
            _save_json(json_path, data)
            print(_info(f"  JSON atualizado com {len(fixed)} correções automáticas"))
        all_gate_results["gate2"] = (passed, issues, fixed)
        print_gate_summary("Gate 2", passed, issues, fixed)
        if not passed:
            print(_err("\nPipeline ABORTADO no Gate 2."))
            return 1

    # ── STEP 3: LLM GATE ────────────────────────────────────────
    if args.from_step <= 3:
        step_label = "Step 3: LLM Gate"
        print(_bold(f"\n[{step_label}]"))
        t0 = time.time()

        llm_args = ["--input", str(json_path)]
        try:
            _run_script("intel-llm-gate.py", llm_args, TIMEOUT_LLM_GATE, step_label)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            print(_warn("  Step 3 falhou — continuando sem reclassificação LLM"))

        step_times["llm_gate"] = time.time() - t0

        # ── GATE 3: RUÍDO ────────────────────────────────────────
        data = _load_json(json_path)
        passed, issues, fixed = gate3_ruido(data)
        all_gate_results["gate3"] = (passed, issues, fixed)
        print_gate_summary("Gate 3", passed, issues, fixed)
        if not passed:
            print(_err("\nPipeline ABORTADO no Gate 3."))
            return 1

    # ── STEP 4: EXTRACT DOCS ────────────────────────────────────
    if args.from_step <= 4:
        step_label = "Step 4: Extract Docs"
        print(_bold(f"\n[{step_label}]"))
        t0 = time.time()

        extract_args = [
            "--input", str(json_path),
            "--top", str(args.top),
        ]
        try:
            _run_script("intel-extract-docs.py", extract_args, TIMEOUT_EXTRACT_DOCS, step_label)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            print(_warn("  Step 4 falhou parcialmente — continuando com documentos disponíveis"))

        step_times["extract_docs"] = time.time() - t0

        # ── GATE 4: CONTEÚDO ─────────────────────────────────────
        data = _load_json(json_path)
        passed, issues, fixed = gate4_conteudo(data, args.top)
        if fixed:
            _save_json(json_path, data)
            print(_info(f"  JSON atualizado com {len(fixed)} correções automáticas"))
        all_gate_results["gate4"] = (passed, issues, fixed)
        print_gate_summary("Gate 4", passed, issues, fixed)
        if not passed:
            print(_err("\nPipeline ABORTADO no Gate 4."))
            return 1

    # ── STEP 5: ANALYZE (MANUAL) ────────────────────────────────
    if args.from_step <= 5:
        print(_bold(f"\n[Step 5: Analyze]"))
        print(_warn("  ┌─────────────────────────────────────────────────────────┐"))
        print(_warn("  │  Step 5 requer análise manual.                          │"))
        print(_warn("  │  Execute separadamente e depois retome com:             │"))
        print(_warn(f"  │  --from-step 6 --cnpj {cnpj14} --ufs {','.join(ufs)}"))
        print(_warn("  │                                                         │"))
        print(_warn(f"  │  JSON a analisar: {str(json_path)[-50:]}"))
        print(_warn("  └─────────────────────────────────────────────────────────┘"))
        print()
        print("  Dica: Abra o JSON, leia os top-20 editais com texto_documentos e")
        print("        preencha o campo 'analise' de cada um com:")
        print("        - resumo_objeto")
        print("        - requisitos_tecnicos")
        print("        - requisitos_habilitacao")
        print("        - nivel_dificuldade")
        print("        - recomendacao_acao  (PARTICIPAR / NÃO PARTICIPAR / AVALIAR)")
        print()

        total_elapsed = time.time() - pipeline_t0
        print(_bold(f"\n{'='*60}"))
        print(_bold(f"  Pipeline PAUSADO para análise manual"))
        print(f"  Tempo acumulado: {_fmt_duration(total_elapsed)}")
        print(f"  JSON: {json_path}")
        print(_bold(f"{'='*60}\n"))
        return 0

    # ── GATE 5: RECOMENDAÇÃO (pre-Excel/PDF) ────────────────────
    if args.from_step <= 6:
        print(_bold(f"\n[Gate 5: Recomendação]"))
        data = _load_json(json_path)
        passed, issues, fixed = gate5_recomendacao(data, args.top)
        if fixed:
            _save_json(json_path, data)
            print(_info(f"  JSON atualizado com {len(fixed)} correções automáticas"))
        all_gate_results["gate5"] = (passed, issues, fixed)
        print_gate_summary("Gate 5", passed, issues, fixed)
        if not passed:
            print(_err("\nPipeline ABORTADO no Gate 5."))
            return 1

    # ── STEP 6: EXCEL ────────────────────────────────────────────
    if args.from_step <= 6:
        step_label = "Step 6: Excel"
        print(_bold(f"\n[{step_label}]"))
        t0 = time.time()

        # Build output xlsx path using same basename as JSON
        xlsx_path = json_path.with_suffix(".xlsx")
        excel_args = [
            "--input", str(json_path),
            "--output", str(xlsx_path),
        ]
        try:
            _run_script("intel-excel.py", excel_args, TIMEOUT_EXCEL, step_label)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            print(_warn("  Step 6 falhou — Excel não gerado"))

        step_times["excel"] = time.time() - t0

    # ── STEP 7: PDF REPORT ───────────────────────────────────────
    if args.from_step <= 7:
        step_label = "Step 7: PDF Report"
        print(_bold(f"\n[{step_label}]"))
        t0 = time.time()

        pdf_path = json_path.with_suffix(".pdf")
        report_args = [
            "--input", str(json_path),
            "--output", str(pdf_path),
        ]
        try:
            _run_script("intel-report.py", report_args, TIMEOUT_PDF, step_label)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            print(_warn("  Step 7 falhou — PDF não gerado"))

        step_times["pdf"] = time.time() - t0

    # ── FINAL SUMMARY ────────────────────────────────────────────
    total_elapsed = time.time() - pipeline_t0

    print(_bold(f"\n{'='*60}"))
    print(_bold(f"  PIPELINE CONCLUÍDO"))
    print(_bold(f"{'='*60}"))
    print()

    # Timing per step
    if step_times:
        print(_bold("  Tempos por passo:"))
        for step, dur in step_times.items():
            print(f"    {step:<20} {_fmt_duration(dur)}")
        print(f"    {'TOTAL':<20} {_fmt_duration(total_elapsed)}")

    # Gate summary
    print()
    print(_bold("  Quality Gates:"))
    for gate_name, (gp, gi, gf) in all_gate_results.items():
        status = _ok("PASSED") if gp else _err("FAILED")
        print(f"    {gate_name:<10} {status}  ({len(gi)} issues, {len(gf)} fixes)")

    # Output files
    print()
    print(_bold("  Arquivos gerados:"))
    if json_path and json_path.exists():
        print(f"    JSON:  {json_path}")
    xlsx_path = json_path.with_suffix(".xlsx") if json_path else None
    if xlsx_path and xlsx_path.exists():
        print(f"    Excel: {xlsx_path}")
    pdf_path = json_path.with_suffix(".pdf") if json_path else None
    if pdf_path and pdf_path.exists():
        print(f"    PDF:   {pdf_path}")

    print()
    all_passed = all(gp for gp, _, _ in all_gate_results.values())
    if all_passed:
        print(_ok(f"  Todos os quality gates passaram. Pipeline bem-sucedido."))
    else:
        failed = [k for k, (gp, _, _) in all_gate_results.items() if not gp]
        print(_warn(f"  Atenção: gates com falha: {', '.join(failed)}"))

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
