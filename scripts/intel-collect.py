#!/usr/bin/env python3
"""
Coleta deterministica de dados para o comando /intel-busca.

Busca exaustiva no PNCP por editais abertos de licitacoes competitivas
para um dado CNPJ + UFs. Zero falsos negativos, zero falsos positivos.

Usage:
    python scripts/intel-collect.py --cnpj 12345678000190 --ufs SC,PR,RS
    python scripts/intel-collect.py --cnpj 12.345.678/0001-90 --ufs SC --dias 60
    python scripts/intel-collect.py --cnpj 12345678000190 --ufs SC,PR --output out.json

Requires:
    pip install httpx pyyaml
"""
from __future__ import annotations

import argparse
import concurrent.futures
import importlib.util
import io
import json
import os
import re
import sys
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Fix Windows console encoding for Unicode output
# Guard: only wrap if not already wrapped (collect-report-data.py also wraps on import)
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "buffer") and not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "buffer") and not isinstance(sys.stderr, io.TextIOWrapper):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except (ValueError, AttributeError):
        pass  # Already wrapped or buffer closed

# ============================================================
# IMPORT from collect-report-data.py (hyphenated filename)
# ============================================================

# Ensure scripts/ is on sys.path so collect-report-data.py can import its siblings (report_dedup)
_scripts_dir = str(Path(__file__).resolve().parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

_crd_path = str(Path(__file__).resolve().parent / "collect-report-data.py")
_spec = importlib.util.spec_from_file_location("collect_report_data", _crd_path)
if _spec is None or _spec.loader is None:
    print(f"ERROR: Cannot load {_crd_path}")
    sys.exit(1)
_crd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_crd)

# Pull out everything we need
ApiClient = _crd.ApiClient
_clean_cnpj = _crd._clean_cnpj
_format_cnpj = _crd._format_cnpj
_safe_float = _crd._safe_float
_parse_date_flexible = _crd._parse_date_flexible
_source_tag = _crd._source_tag
_fmt_brl = _crd._fmt_brl
_strip_accents = _crd._strip_accents
collect_opencnpj = _crd.collect_opencnpj
map_sector = _crd.map_sector
PNCP_BASE = _crd.PNCP_BASE
PNCP_FILES_BASE = _crd.PNCP_FILES_BASE
PNCP_MAX_PAGE_SIZE = _crd.PNCP_MAX_PAGE_SIZE
MODALIDADES = _crd.MODALIDADES
MODALIDADES_EXCLUIDAS = _crd.MODALIDADES_EXCLUIDAS
PNCP_MAX_PAGES_UF = _crd.PNCP_MAX_PAGES_UF
PNCP_MAX_PAGES = _crd.PNCP_MAX_PAGES
CNAE_KEYWORD_REFINEMENTS = _crd.CNAE_KEYWORD_REFINEMENTS
_compile_keyword_patterns = _crd._compile_keyword_patterns
_compute_keyword_density = _crd._compute_keyword_density
_check_hard_exclusions = _crd._check_hard_exclusions
_load_json_cache = _crd._load_json_cache
_save_json_cache = _crd._save_json_cache
DOCS_CACHE_FILE = _crd.DOCS_CACHE_FILE
CNAE_INCOMPATIBLE_OBJECTS = _crd.CNAE_INCOMPATIBLE_OBJECTS

# ============================================================
# CONSTANTS
# ============================================================

VERSION = "1.0.0"
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Competitive modalidades ONLY (Concorrencias + Pregoes)
# Excluded: Dispensa(8), Inexigibilidade(9), Inaplicabilidade(14),
#           Dialogo Competitivo(2), Concurso(3), Credenciamento(12), Chamada Publica(15)
MODALIDADES_BUSCA = {
    k: v for k, v in MODALIDADES.items()
    if k not in MODALIDADES_EXCLUIDAS and k not in {2, 3, 12, 15}
}

# CNAE keyword density gate: 1% minimum (lower than report's 2% for zero false negatives)
INTEL_DENSITY_MIN = 0.01


# ============================================================
# HELPERS
# ============================================================

def _today() -> datetime:
    return datetime.now(timezone.utc)


def _date_compact(dt: datetime) -> str:
    return dt.strftime("%Y%m%d")


def _date_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


# ============================================================
# STEP 3: EXHAUSTIVE PNCP SEARCH (no keyword filtering)
# ============================================================

def search_pncp_exhaustive(
    api: ApiClient,
    ufs: list[str],
    dias: int,
    modalidades: dict[int, str],
) -> tuple[list[dict], dict]:
    """Fetch ALL editais from PNCP for the given UFs, modalidades, and date range.

    NO keyword filtering at this stage -- captures everything to avoid false negatives.
    Deduplicates by {cnpj_orgao}/{anoCompra}/{sequencialCompra}.

    Returns (raw_editais, source_meta).
    """
    data_inicial = _date_compact(_today() - timedelta(days=dias))
    data_final = _date_compact(_today())

    all_items: list[dict] = []
    seen_ids: set[str] = set()
    source_meta = {
        "total_raw_api": 0,
        "total_after_dedup": 0,
        "pages_fetched": 0,
        "errors": 0,
        "pagination_exhausted": [],
    }

    use_per_uf = 1 <= len(ufs) <= 10
    uf_iterations: list[str | None] = list(ufs) if use_per_uf else [None]
    max_pages = PNCP_MAX_PAGES_UF if use_per_uf else PNCP_MAX_PAGES

    for mod_code, mod_name in sorted(modalidades.items()):
        print(f"\n  Modalidade {mod_code} ({mod_name}):")

        for uf_filter in uf_iterations:
            if uf_filter:
                print(f"    UF {uf_filter}:", end=" ", flush=True)

            page_count = 0
            uf_items = 0

            for page in range(1, max_pages + 1):
                params = {
                    "dataInicial": data_inicial,
                    "dataFinal": data_final,
                    "codigoModalidadeContratacao": mod_code,
                    "pagina": page,
                    "tamanhoPagina": PNCP_MAX_PAGE_SIZE,
                }
                if uf_filter:
                    params["uf"] = uf_filter

                uf_label = f" uf={uf_filter}" if uf_filter else ""
                data, status = api.get(
                    f"{PNCP_BASE}/contratacoes/publicacao",
                    params=params,
                    label=f"PNCP mod={mod_code}{uf_label} p={page}",
                )

                if status != "API" or not data:
                    source_meta["errors"] += 1
                    break

                items = data if isinstance(data, list) else data.get("data", data.get("resultado", []))
                if not isinstance(items, list) or not items:
                    break

                page_count += 1
                source_meta["pages_fetched"] += 1
                source_meta["total_raw_api"] += len(items)

                for item in items:
                    orgao_entity = item.get("orgaoEntidade") or {}
                    cnpj_compra = orgao_entity.get("cnpj") or item.get("cnpjCompra") or ""
                    cnpj_clean = re.sub(r"[^0-9]", "", str(cnpj_compra))
                    ano = str(item.get("anoCompra") or "")
                    seq = str(item.get("sequencialCompra") or "")

                    dedup_key = f"{cnpj_clean}/{ano}/{seq}"
                    if dedup_key in seen_ids:
                        continue
                    seen_ids.add(dedup_key)

                    # Parse the raw item into our format
                    unidade = item.get("unidadeOrgao") or {}
                    uf = (unidade.get("ufSigla") or item.get("ufSigla") or "").upper()

                    # UF filter (when not using server-side UF param)
                    if ufs and uf and uf not in ufs:
                        continue

                    objeto = (item.get("objetoCompra") or item.get("objeto") or "").strip()
                    orgao = (orgao_entity.get("razaoSocial") or
                             unidade.get("nomeUnidade") or
                             item.get("nomeOrgao") or "")
                    municipio = unidade.get("municipioNome") or ""
                    valor = _safe_float(item.get("valorTotalEstimado") or item.get("valorEstimado"))
                    modalidade_nome = item.get("modalidadeNome") or mod_name

                    # Dates
                    data_pub_raw = item.get("dataPublicacaoPncp") or ""
                    data_abertura_raw = item.get("dataAberturaProposta") or ""
                    data_encerramento_raw = item.get("dataEncerramentoProposta") or ""

                    data_publicacao = _parse_date_flexible(data_pub_raw) or ""
                    data_abertura = data_abertura_raw  # Keep full ISO for proposals
                    data_encerramento = data_encerramento_raw

                    # Link
                    link_sistema = item.get("linkSistemaOrigem") or ""
                    if cnpj_clean and ano and seq:
                        link = f"https://pncp.gov.br/app/editais/{cnpj_clean}/{ano}/{seq}"
                    elif link_sistema:
                        link = link_sistema
                    else:
                        link = ""

                    parsed = {
                        "_id": f"{cnpj_clean}/{ano}/{seq}" if (cnpj_clean and ano and seq) else f"unknown/{uuid.uuid4().hex[:12]}",
                        "objeto": objeto,
                        "orgao": orgao,
                        "cnpj_orgao": cnpj_clean,
                        "uf": uf,
                        "municipio": municipio,
                        "valor_estimado": valor,
                        "modalidade_code": mod_code,
                        "modalidade_nome": modalidade_nome,
                        "data_publicacao": data_publicacao,
                        "data_abertura_proposta": data_abertura,
                        "data_encerramento_proposta": data_encerramento,
                        "link_pncp": link,
                        "ano_compra": ano,
                        "sequencial_compra": seq,
                    }
                    all_items.append(parsed)
                    uf_items += 1

                if len(items) < PNCP_MAX_PAGE_SIZE:
                    break

                time.sleep(0.5)  # Rate limiting

            if uf_filter:
                # Print inline summary for this UF
                print(f"{page_count} pages, {uf_items} editais")

            # Check pagination exhaustion
            if page_count == max_pages:
                source_meta["pagination_exhausted"].append(
                    f"mod={mod_code} uf={uf_filter or 'ALL'}"
                )

    source_meta["total_after_dedup"] = len(all_items)
    return all_items, source_meta


# ============================================================
# STEP 4: CNAE KEYWORD GATE
# ============================================================

def apply_cnae_keyword_gate(
    editais: list[dict],
    keywords: list[str],
    keyword_patterns: list[re.Pattern],
    sector_key: str,
    cnae_prefix: str,
    all_cnae_prefixes: set[str] | None = None,
    all_sector_keys: set[str] | None = None,
) -> None:
    """Classify each edital as cnae_compatible or not. Mutates in place.

    Uses sector keywords + CNAE refinements for matching.
    All editais pass through -- we just flag them.
    When multiple CNAEs are provided, an edital is only excluded if it's
    incompatible with ALL CNAEs (not just the primary one).
    """
    _all_prefixes = all_cnae_prefixes or {cnae_prefix}
    _all_sectors = all_sector_keys or {sector_key}

    # Aggregate CNAE-specific exclude patterns from ALL CNAEs
    # An exclude only applies if it comes from the PRIMARY CNAE —
    # secondary CNAEs ADD coverage, they don't restrict it
    cnae_refinements = CNAE_KEYWORD_REFINEMENTS.get(cnae_prefix, {})
    exclude_terms = cnae_refinements.get("exclude_patterns", [])
    exclude_patterns = _compile_keyword_patterns(exclude_terms) if exclude_terms else []

    # CNAE-object incompatibility: only reject if ALL company CNAEs are incompatible
    # Build per-prefix compiled patterns
    per_cnae_incompat: dict[str, list[re.Pattern]] = {}
    for prefix in _all_prefixes:
        pats = CNAE_INCOMPATIBLE_OBJECTS.get(prefix, [])
        compiled = []
        for pat_str in pats:
            try:
                compiled.append(re.compile(pat_str, re.IGNORECASE))
            except re.error:
                pass
        if compiled:
            per_cnae_incompat[prefix] = compiled

    stats = {"compatible": 0, "incompatible": 0, "needs_llm": 0}

    for ed in editais:
        objeto = ed.get("objeto", "")
        objeto_lower = _strip_accents(objeto.lower())

        if not objeto_lower.strip():
            ed["cnae_compatible"] = False
            ed["keyword_density"] = 0.0
            ed["match_keywords"] = []
            ed["needs_llm_review"] = True
            ed["exclusion_reason"] = "objeto vazio"
            stats["incompatible"] += 1
            stats["needs_llm"] += 1
            continue

        # Check hard exclusions (sector-level)
        exclusion = _check_hard_exclusions(objeto_lower, sector_key)
        if exclusion:
            ed["cnae_compatible"] = False
            ed["keyword_density"] = 0.0
            ed["match_keywords"] = []
            ed["needs_llm_review"] = False
            ed["exclusion_reason"] = f"hard_exclusion: {exclusion}"
            stats["incompatible"] += 1
            continue

        # Check CNAE-object incompatibility — only reject if ALL CNAEs are incompatible
        if per_cnae_incompat:
            all_incompatible = True
            incompat_detail = ""
            for prefix, cpats in per_cnae_incompat.items():
                prefix_hit = False
                for cpat in cpats:
                    if cpat.search(objeto_lower):
                        prefix_hit = True
                        incompat_detail = cpat.pattern
                        break
                if not prefix_hit:
                    all_incompatible = False
                    break
            # Also compatible if some CNAEs have NO incompatibility patterns at all
            cnaes_without_rules = _all_prefixes - set(per_cnae_incompat.keys())
            if cnaes_without_rules:
                all_incompatible = False
            if all_incompatible:
                ed["cnae_compatible"] = False
                ed["keyword_density"] = 0.0
                ed["match_keywords"] = []
                ed["needs_llm_review"] = False
                ed["exclusion_reason"] = f"cnae_incompatible_all: {incompat_detail}"
                stats["incompatible"] += 1
                continue

        # Check CNAE-refinement exclude patterns
        exclude_hit = False
        for ep in exclude_patterns:
            if ep.search(objeto_lower):
                exclude_hit = True
                break
        if exclude_hit:
            ed["cnae_compatible"] = False
            ed["keyword_density"] = 0.0
            ed["match_keywords"] = []
            ed["needs_llm_review"] = False
            ed["exclusion_reason"] = "cnae_refinement_exclusion"
            stats["incompatible"] += 1
            continue

        # Keyword matching
        matched_kws = []
        for kw in keywords:
            kw_lower = _strip_accents(kw.lower().strip())
            if not kw_lower:
                continue
            # Simple word presence check for the match_keywords list
            if kw_lower in objeto_lower:
                matched_kws.append(kw)

        # Density via compiled patterns (more accurate, word-boundary)
        density = _compute_keyword_density(objeto_lower, keyword_patterns)

        # Compatibility gate: at least 1 keyword match with density >= 1%
        is_compatible = len(matched_kws) >= 1 and density >= INTEL_DENSITY_MIN

        ed["cnae_compatible"] = is_compatible
        ed["keyword_density"] = round(density, 4)
        ed["match_keywords"] = matched_kws
        ed["needs_llm_review"] = not is_compatible and len(matched_kws) == 0
        ed["exclusion_reason"] = None if is_compatible else (
            "zero_keyword_match" if len(matched_kws) == 0 else f"low_density_{density:.4f}"
        )

        if is_compatible:
            stats["compatible"] += 1
        else:
            stats["incompatible"] += 1
            if ed["needs_llm_review"]:
                stats["needs_llm"] += 1

    print(f"\n  CNAE Gate: {stats['compatible']} compativeis, "
          f"{stats['incompatible']} incompativeis, "
          f"{stats['needs_llm']} precisam LLM review")


# ============================================================
# STEP 5: FETCH DOCUMENT LISTINGS (top 50 by valor)
# ============================================================

def fetch_documents_top50(api: ApiClient, editais: list[dict]) -> None:
    """Fetch document listings for top 50 cnae_compatible editais by valor. Mutates in place."""
    compatible = [ed for ed in editais if ed.get("cnae_compatible")]
    compatible_sorted = sorted(
        compatible,
        key=lambda e: (e.get("valor_estimado") or 0.0),
        reverse=True,
    )
    top50 = compatible_sorted[:50]
    top50_ids = {ed["_id"] for ed in top50}

    # Load docs cache
    docs_cache: dict = {}
    docs_cache_lock = threading.Lock()
    try:
        docs_cache = _load_json_cache(DOCS_CACHE_FILE)
        if docs_cache:
            print(f"  Docs cache: {len(docs_cache)} entradas carregadas do disco")
    except Exception:
        pass

    print(f"\n  Buscando documentos para top {len(top50)} editais compativeis por valor...")
    counter_lock = threading.Lock()
    counters = {"cached": 0, "fetched": 0, "failed": 0}

    def _fetch_single(ed: dict) -> None:
        cnpj_orgao = ed.get("cnpj_orgao", "")
        ano = ed.get("ano_compra", "")
        seq = ed.get("sequencial_compra", "")

        if not (cnpj_orgao and ano and seq):
            ed["documentos"] = []
            ed["documentos_source"] = _source_tag("UNAVAILABLE", "Dados insuficientes")
            return

        cache_key = f"{cnpj_orgao}/{ano}/{seq}"

        # Check cache
        with docs_cache_lock:
            cached = docs_cache.get(cache_key)

        if cached is not None:
            ed["documentos"] = cached
            ed["documentos_source"] = _source_tag("API", f"{len(cached)} documentos (cache)")
            with counter_lock:
                counters["cached"] += 1
            return

        data, status = api.get(
            f"{PNCP_FILES_BASE}/orgaos/{cnpj_orgao}/compras/{ano}/{seq}/arquivos",
            label=f"Docs: {cnpj_orgao}/{ano}/{seq}",
        )

        if status == "API" and isinstance(data, list):
            docs = []
            for d in data:
                docs.append({
                    "tipo": d.get("tipoDocumentoNome") or d.get("tipoDocumentoDescricao") or "",
                    "tipo_id": d.get("tipoDocumentoId"),
                    "titulo": d.get("titulo", ""),
                    "sequencial": d.get("sequencialDocumento"),
                    "download_url": (
                        f"https://pncp.gov.br/pncp-api/v1/orgaos/{cnpj_orgao}/compras/{ano}/{seq}"
                        f"/arquivos/{d.get('sequencialDocumento')}"
                    ) if d.get("sequencialDocumento") else None,
                    "ativo": d.get("statusAtivo", True),
                })
            ed["documentos"] = docs
            ed["documentos_source"] = _source_tag("API", f"{len(docs)} documentos encontrados")
            with docs_cache_lock:
                docs_cache[cache_key] = docs
            with counter_lock:
                counters["fetched"] += 1
        else:
            ed["documentos"] = []
            ed["documentos_source"] = _source_tag("API_FAILED")
            with counter_lock:
                counters["failed"] += 1

        time.sleep(0.05)

    # Only fetch for top 50
    to_fetch = [ed for ed in editais if ed["_id"] in top50_ids]

    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as pool:
        list(pool.map(_fetch_single, to_fetch))

    print(f"  Documentos: {counters['cached']} do cache, {counters['fetched']} da API, {counters['failed']} falhas")

    # Save docs cache
    try:
        _save_json_cache(DOCS_CACHE_FILE, docs_cache)
    except Exception as e:
        print(f"  WARN: Falha ao salvar docs cache: {e}")


# ============================================================
# STEP 6: ASSEMBLE OUTPUT
# ============================================================

def assemble_output(
    empresa: dict,
    editais: list[dict],
    cnpj_formatted: str,
    ufs: list[str],
    dias: int,
    sector_name: str,
    sector_key: str,
    keywords: list[str],
    source_meta: dict,
    all_cnaes: list[str] | None = None,
    all_sector_keys: set[str] | None = None,
) -> dict:
    """Build the final JSON output structure."""
    now = _today()
    data_inicio = _date_iso(now - timedelta(days=dias))
    data_fim = _date_iso(now)

    # Statistics
    compatible = [ed for ed in editais if ed.get("cnae_compatible")]
    incompatible = [ed for ed in editais if not ed.get("cnae_compatible")]
    needs_llm = [ed for ed in editais if ed.get("needs_llm_review")]

    valor_total_compat = sum(_safe_float(ed.get("valor_estimado")) or 0.0 for ed in compatible)

    capital = _safe_float(empresa.get("capital_social")) or 0.0
    capacidade_10x = capital * 10.0 if capital > 0 else 0.0

    top20_dentro = 0
    if capacidade_10x > 0:
        compat_sorted = sorted(compatible, key=lambda e: (e.get("valor_estimado") or 0.0), reverse=True)
        for ed in compat_sorted[:20]:
            v = _safe_float(ed.get("valor_estimado")) or 0.0
            if 0 < v <= capacidade_10x:
                top20_dentro += 1

    # Sort editais: compatible first (by valor desc), then incompatible (by valor desc)
    compatible_sorted = sorted(compatible, key=lambda e: (e.get("valor_estimado") or 0.0), reverse=True)
    incompatible_sorted = sorted(incompatible, key=lambda e: (e.get("valor_estimado") or 0.0), reverse=True)
    editais_sorted = compatible_sorted + incompatible_sorted

    return {
        "empresa": empresa,
        "busca": {
            "cnpj": cnpj_formatted,
            "ufs": ufs,
            "dias": dias,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "modalidades": sorted(MODALIDADES_BUSCA.keys()),
            "setor": sector_name,
            "sector_key": sector_key,
            "keywords_count": len(keywords),
            "keywords_sample": keywords[:20],
            "cnaes_count": len(all_cnaes) if all_cnaes else 1,
            "sector_keys": sorted(all_sector_keys) if all_sector_keys else [sector_key],
        },
        "estatisticas": {
            "total_bruto": len(editais),
            "total_cnae_compativel": len(compatible),
            "total_cnae_incompativel": len(incompatible),
            "total_needs_llm_review": len(needs_llm),
            "valor_total_compativel": round(valor_total_compat, 2),
            "capacidade_10x": round(capacidade_10x, 2),
            "top20_dentro_capacidade": top20_dentro,
            "pncp_pages_fetched": source_meta.get("pages_fetched", 0),
            "pncp_errors": source_meta.get("errors", 0),
            "pncp_pagination_exhausted": source_meta.get("pagination_exhausted", []),
        },
        "editais": editais_sorted,
        "_metadata": {
            "generated_at": now.isoformat(),
            "script": "intel-collect.py",
            "version": VERSION,
            "sources": {
                "pncp": {
                    "raw_api_items": source_meta.get("total_raw_api", 0),
                    "after_dedup": source_meta.get("total_after_dedup", 0),
                    "pages_fetched": source_meta.get("pages_fetched", 0),
                    "errors": source_meta.get("errors", 0),
                },
                "opencnpj": empresa.get("_source", {}).get("status", "UNKNOWN"),
            },
        },
    }


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Intel Collect - Busca exaustiva PNCP para /intel-busca",
    )
    parser.add_argument("--cnpj", required=True, help="CNPJ da empresa (com ou sem formatacao)")
    parser.add_argument("--ufs", required=True, help="UFs separadas por virgula (ex: SC,PR,RS)")
    parser.add_argument("--dias", type=int, default=30, help="Periodo de busca em dias (default: 30)")
    parser.add_argument("--output", type=str, default=None, help="Caminho do JSON de saida")
    parser.add_argument("--quiet", action="store_true", help="Reduzir output no console")
    args = parser.parse_args()

    t0 = time.time()

    # ── Step 1: Parse args, fetch company data ──
    cnpj14 = _clean_cnpj(args.cnpj)
    cnpj_formatted = _format_cnpj(cnpj14)
    ufs = [u.strip().upper() for u in args.ufs.split(",") if u.strip()]
    dias = args.dias

    print(f"{'='*60}")
    print(f"  INTEL-COLLECT v{VERSION}")
    print(f"  CNPJ: {cnpj_formatted}")
    print(f"  UFs:  {', '.join(ufs)}")
    print(f"  Dias: {dias}")
    print(f"  Modalidades: {sorted(MODALIDADES_BUSCA.keys())}")
    print(f"{'='*60}")

    api = ApiClient(verbose=not args.quiet)

    print("\n[1/6] Perfil da empresa...")
    empresa = collect_opencnpj(api, cnpj14)
    if empresa.get("_source", {}).get("status") == "API_FAILED":
        print(f"\nERROR: Nao foi possivel obter dados da empresa para CNPJ {cnpj_formatted}")
        print("Verifique o CNPJ e tente novamente.")
        api.close()
        sys.exit(1)

    razao = empresa.get("razao_social", "N/A")
    cnae_principal = empresa.get("cnae_principal", "")
    capital = empresa.get("capital_social", 0.0)
    uf_sede = empresa.get("uf_sede", "")
    print(f"  Empresa: {razao}")
    print(f"  CNAE: {cnae_principal}")
    print(f"  Capital: {_fmt_brl(capital)}")
    print(f"  UF Sede: {uf_sede}")

    # ── Step 2: Map ALL CNAEs -> keywords (principal + secundários) ──
    print("\n[2/6] Mapeando TODOS os CNAEs para keywords...")

    # Collect all CNAEs (principal + secondary)
    all_cnaes: list[str] = []
    if cnae_principal:
        all_cnaes.append(cnae_principal)
    cnaes_sec_raw = empresa.get("cnaes_secundarios", "")
    if cnaes_sec_raw:
        # May be comma-separated string or list
        if isinstance(cnaes_sec_raw, list):
            all_cnaes.extend(str(c).strip() for c in cnaes_sec_raw if str(c).strip())
        else:
            all_cnaes.extend(c.strip() for c in str(cnaes_sec_raw).split(",") if c.strip())
    print(f"  CNAEs encontrados: {len(all_cnaes)} (1 principal + {len(all_cnaes)-1} secundarios)")

    # Map each CNAE to sector + keywords, aggregating all
    all_keywords: list[str] = []
    all_sector_keys: set[str] = set()
    all_cnae_prefixes: set[str] = set()
    primary_sector_name = ""
    primary_sector_key = ""

    for i, cnae_raw in enumerate(all_cnaes):
        s_name, s_keywords, s_key = map_sector(cnae_raw)
        all_keywords.extend(s_keywords)
        all_sector_keys.add(s_key)

        # Extract 4-digit prefix
        cnae_d = re.sub(r"[^0-9]", "", cnae_raw.split("-")[0].split(" ")[0])[:7]
        prefix = cnae_d[:4]
        if prefix:
            all_cnae_prefixes.add(prefix)

        # Add CNAE refinement extra keywords
        cnae_ref = CNAE_KEYWORD_REFINEMENTS.get(prefix, {})
        extra_inc = cnae_ref.get("extra_include", [])
        if extra_inc:
            all_keywords.extend(extra_inc)

        # Add CNAE description words
        cnae_desc_part = cnae_raw.split("-")[-1].split("/")[-1] if "-" in cnae_raw else cnae_raw
        desc_words = [w.strip().lower() for w in cnae_desc_part.split() if len(w.strip()) > 3]
        all_keywords.extend(desc_words)

        if i == 0:
            primary_sector_name = s_name
            primary_sector_key = s_key
            print(f"  CNAE principal: {cnae_raw} → {s_name} ({s_key})")
        elif s_key != "geral":
            print(f"  CNAE secundario: {prefix} → {s_name}")

    sector_name = primary_sector_name
    sector_key = primary_sector_key
    cnae_prefix = re.sub(r"[^0-9]", "", cnae_principal.split("-")[0].split(" ")[0])[:4]

    # Deduplicate keywords
    seen_kw: set[str] = set()
    unique_keywords: list[str] = []
    for kw in all_keywords:
        kw_low = kw.lower().strip()
        if kw_low and kw_low not in seen_kw:
            seen_kw.add(kw_low)
            unique_keywords.append(kw)
    keywords = unique_keywords

    print(f"  Setores cobertos: {', '.join(sorted(all_sector_keys))}")
    print(f"  Prefixos CNAE: {', '.join(sorted(all_cnae_prefixes))}")
    print(f"  Total keywords (dedup): {len(keywords)}")

    # Compile patterns
    keyword_patterns = _compile_keyword_patterns(keywords)
    print(f"  Patterns compilados: {len(keyword_patterns)}")

    # ── Step 3: Exhaustive PNCP search ──
    print(f"\n[3/6] Busca exaustiva PNCP ({dias} dias, {len(ufs)} UFs, {len(MODALIDADES_BUSCA)} modalidades)...")
    editais, source_meta = search_pncp_exhaustive(api, ufs, dias, MODALIDADES_BUSCA)
    print(f"\n  Total bruto (dedup): {len(editais)} editais")
    if source_meta["pagination_exhausted"]:
        print(f"  WARN: Paginacao esgotada em: {source_meta['pagination_exhausted']}")

    # ── Step 4: CNAE keyword gate ──
    print(f"\n[4/6] Aplicando gate de keywords CNAE ({len(all_cnae_prefixes)} prefixos, {len(all_sector_keys)} setores)...")
    apply_cnae_keyword_gate(
        editais, keywords, keyword_patterns, sector_key, cnae_prefix,
        all_cnae_prefixes=all_cnae_prefixes,
        all_sector_keys=all_sector_keys,
    )

    # ── Step 5: Fetch documents for top 50 ──
    print(f"\n[5/6] Buscando documentos PNCP...")
    fetch_documents_top50(api, editais)

    # ── Step 6: Save output ──
    print(f"\n[6/6] Montando JSON de saida...")
    output = assemble_output(
        empresa=empresa,
        editais=editais,
        cnpj_formatted=cnpj_formatted,
        ufs=ufs,
        dias=dias,
        sector_name=sector_name,
        sector_key=sector_key,
        keywords=keywords,
        source_meta=source_meta,
        all_cnaes=all_cnaes,
        all_sector_keys=all_sector_keys,
    )

    # Determine output path
    if args.output:
        out_path = args.output
    else:
        today_str = _date_iso(_today())
        out_dir = str(_PROJECT_ROOT / "docs" / "intel")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"intel-{cnpj14}-{today_str}.json")

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)

    elapsed = time.time() - t0

    # Summary
    stats = output["estatisticas"]
    print(f"\n{'='*60}")
    print(f"  RESULTADO")
    print(f"{'='*60}")
    print(f"  Total bruto:          {stats['total_bruto']}")
    print(f"  CNAE compativeis:     {stats['total_cnae_compativel']}")
    print(f"  CNAE incompativeis:   {stats['total_cnae_incompativel']}")
    print(f"  Precisam LLM review:  {stats['total_needs_llm_review']}")
    print(f"  Valor total compat:   {_fmt_brl(stats['valor_total_compativel'])}")
    print(f"  Capacidade 10x:       {_fmt_brl(stats['capacidade_10x'])}")
    print(f"  Top 20 dentro cap:    {stats['top20_dentro_capacidade']}")
    print(f"  Paginas PNCP:         {stats['pncp_pages_fetched']}")
    print(f"  Erros PNCP:           {stats['pncp_errors']}")
    print(f"  Tempo total:          {elapsed:.1f}s")
    print(f"  Salvo em:             {out_path}")
    print(f"{'='*60}")

    api.print_stats()
    api.close()


if __name__ == "__main__":
    main()
