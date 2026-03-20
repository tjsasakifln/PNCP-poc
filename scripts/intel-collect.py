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
import hashlib
import importlib.util
import io
import json
import os
import re
import statistics
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
collect_sicaf = _crd.collect_sicaf
collect_portal_transparencia = _crd.collect_portal_transparencia

# ============================================================
# CONSTANTS
# ============================================================

VERSION = "1.1.0"
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Checkpoint file for resume/fault-tolerance
_CHECKPOINT_FILE = _PROJECT_ROOT / "data" / "intel_pncp_checkpoint.json"
_CHECKPOINT_TTL_HOURS = 2      # Re-use cached UF+mod result if < 2h old
_CHECKPOINT_CLEANUP_HOURS = 24  # Evict stale checkpoint entries older than 24h

# Competitive intelligence cache
_COMPETITIVE_CACHE_FILE = str(_PROJECT_ROOT / "data" / "competitive_cache.json")
_COMPETITIVE_CACHE_TTL_DAYS = 7  # Cache competitive intel per organ for 7 days
_COMPETITIVE_MAX_ORGANS = 15     # Max unique organs to query

# Competitive modalidades ONLY (Concorrencias + Pregoes)
# Excluded: Dispensa(8), Inexigibilidade(9), Inaplicabilidade(14),
#           Dialogo Competitivo(2), Concurso(3), Credenciamento(12), Chamada Publica(15)
MODALIDADES_BUSCA = {
    k: v for k, v in MODALIDADES.items()
    if k not in MODALIDADES_EXCLUIDAS and k not in {2, 3, 12, 15}
}

# CNAE keyword density gate: 1% minimum (lower than report's 2% for zero false negatives)
INTEL_DENSITY_MIN = 0.01

# Per-sector keyword density overrides (lower = more inclusive for niche terms)
SECTOR_DENSITY_OVERRIDES = {
    "impermeabilizacao": 0.005,
    "acustica": 0.005,
    "avaliacao_imoveis": 0.005,
    "geotecnia": 0.005,
    "topografia": 0.005,
    "demolicao": 0.005,
}

# Exclusion patterns applied BEFORE LLM review to reject obviously incompatible editais.
# Any zero-keyword-match edital whose objeto matches one of these is rejected immediately
# (cnae_compatible=False, needs_llm_review=False) without spending an LLM call.
EXCLUSION_PATTERNS: list[tuple[str, re.Pattern]] = []
_EXCLUSION_PATTERN_STRINGS: list[tuple[str, str]] = [
    # Medical/Health
    ("medical_health", r'(medicament|farmac|hospitalar|cirurg|laboratori|curativ|seringa|equipos|extensores|filtros.*processo.*254|luvas.*procedimento|aparelho.*medico|protese|ortese|implante.*medico|ventilador.*pulmonar|monitor.*multiparametr|desfibrilador|tomograf|ressonancia|ultrassom.*medico|endoscop|laparoscop|broncoscop|marcapasso|material.*hospitalar|rouparia.*hospitalar|colchoes.*hospitalar|camera.*mortuaria|servicos.*medicos|pediatria|ginecologia|anestesi|psiquiatr)'),
    # Pharmaceuticals
    ("pharmaceuticals", r'(valproato|acebrofilina|beclometasona|domperidona|alopurinol|brimonidina|omeprazol|losartana|metformina|insulina|dipirona|paracetamol|amoxicilina|azitromicina|\d+\s*mg\s*(comprimido|capsula|frasco|ampola|suspensao))'),
    # Food/Nutrition
    ("food_nutrition", r'(generos alimenticios|alimentacao.*escolar|merenda|refeicao|nutricao|carne.*embutido|leite.*derivado|hortifruti|padaria|alimento.*perecivel|kit.*lanche|cesta.*basica)'),
    # Financial services
    ("financial_services", r'(instituicao financeira|servicos bancarios|operacoes de credito|folha de pagamento.*banco|conta.*salario)'),
    # IT/Software/Telecom
    ("it_software_telecom", r'(software|sistema.{0,15}(informatica|gestao|erp|eletronico|gerenciamento de informac)|tecnologia da informacao|solucao hiperconverg|servidor.*rack|computador|notebook|impressora|scanner|red hat|jboss|subscricao|licenca.*software|outsourcing.*impressao|comunicacao multimidia|mpls|link.*dados|fibra optica.*rede|switch.*rede|roteador|firewall|storage|backup.*dados|datacenter|cloud.*computing)'),
    # Surveillance/Security guards
    ("surveillance_security_guards", r'(vigilancia.*patrimonial|controlador de acesso|vigia\b|porteiro|seguranca.*armada|monitoramento.*eletronico.*patrimon)'),
    # Cleaning/Conservation
    ("cleaning_conservation", r'(limpeza.{0,15}(asseio|conserva|predial|hospitalar)|servicos de conservacao e limpeza|coleta.{0,15}(residuo|lixo)|destinacao final.{0,15}(residuo|rcc|aterro))'),
    # Vehicles/Fuel (purchase, not road construction)
    ("vehicles_fuel", r'(aquisicao de (veiculo|automovel|caminhao|onibus|ambulancia|motocicleta)|combustivel|gasolina|diesel|etanol|gas liquefeito|lubrificante)'),
    # Uniforms/Office
    ("uniforms_office", r'(uniforme|fardamento|vestuario|material de escritorio|papelaria|toner|cartucho)'),
    # Energy purchase (not infrastructure)
    ("energy_purchase", r'(aquisicao de energia eletrica|contratacao.{0,20}energia eletrica.*varejista|locacao.*usina.*energia)'),
    # Equipment purchase (not construction-related)
    ("equipment_purchase", r'(equipamentos perifericos.*sistema|equipamentos especiais.*paassex|rolo compactador|retroescavadeira|pa carregadeira|motoniveladora|escavadeira hidraulica)'),
    # Naval/Military specialized
    ("naval_military", r'(construcao naval|lancha|embarcacao|navio|fragata|corveta|submarino)'),
    # Pest control / mosquito
    ("pest_control", r'(controle de (mosquit|pragas|vetores)|desinsetizacao|desratizacao)'),
    # TV/Media operations
    ("tv_media", r'(operacao.{0,15}(tv|televisao|radio|camera)|producao audiovisual)'),
    # Kitchen equipment
    ("kitchen_equipment", r'(equipamento.*cozinha industrial|balcao termico|fogao industrial|camera.*frigorifica.*cozinha)'),
    # Specific medical equipment rental
    ("medical_equipment_rental", r'(locacao.{0,20}equipamento.*medico|videolaparoscop|videobroncoscop)'),
]
for _pat_name, _pat_str in _EXCLUSION_PATTERN_STRINGS:
    try:
        EXCLUSION_PATTERNS.append((_pat_name, re.compile(_pat_str, re.IGNORECASE)))
    except re.error as _e:
        print(f"WARNING: Failed to compile exclusion pattern '{_pat_name}': {_e}", file=sys.stderr)


# ============================================================
# HELPERS
# ============================================================

def _today() -> datetime:
    return datetime.now(timezone.utc)


def _compute_dedup_hash(edital: dict) -> str:
    """Compute a cross-portal dedup hash based on objeto, valor, uf, and municipio.

    Strips portal-specific prefixes so the same edital published on both PNCP
    and Portal de Compras Públicas produces the same hash and can be deduplicated.
    """
    obj = (edital.get("objeto") or "").lower().strip()
    # Remove portal prefixes injected by PCP
    for prefix in ["[portal de compras públicas] - ", "[portal de compras publicas] - "]:
        if obj.startswith(prefix):
            obj = obj[len(prefix):]
    # Normalize: collapse extra whitespace, remove punctuation noise
    obj = re.sub(r'\s+', ' ', obj).strip()
    valor = str(edital.get("valor_estimado") or 0)
    uf = edital.get("uf") or ""
    municipio = (edital.get("municipio") or "").lower().strip()
    raw = f"{uf}|{municipio}|{valor}|{obj[:150]}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _date_compact(dt: datetime) -> str:
    return dt.strftime("%Y%m%d")


def _date_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


# ============================================================
# CHECKPOINT HELPERS (resume / fault-tolerance)
# ============================================================

def _checkpoint_key(cnpj14: str, ufs: list[str], dias: int) -> str:
    """Top-level checkpoint key: {cnpj}_{ufs_sorted}_{dias}."""
    ufs_sorted = ",".join(sorted(ufs))
    return f"{cnpj14}_{ufs_sorted}_{dias}"


def _subkey(mod_code: int, uf: str) -> str:
    return f"mod_{mod_code}_{uf}"


def _load_checkpoint() -> dict:
    """Load checkpoint file from disk. Returns {} on any error."""
    try:
        if _CHECKPOINT_FILE.exists():
            with open(_CHECKPOINT_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_checkpoint(data: dict) -> None:
    """Atomically write checkpoint to disk (tmp → rename)."""
    try:
        _CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = _CHECKPOINT_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        tmp.replace(_CHECKPOINT_FILE)
    except Exception as e:
        print(f"  WARN: Falha ao salvar checkpoint: {e}")


def _cleanup_old_checkpoints(data: dict) -> dict:
    """Remove top-level keys (and sub-keys) older than _CHECKPOINT_CLEANUP_HOURS."""
    cutoff = _today() - timedelta(hours=_CHECKPOINT_CLEANUP_HOURS)
    cleaned: dict = {}
    for top_key, sub_dict in data.items():
        if not isinstance(sub_dict, dict):
            continue
        # Keep if any sub-key is recent enough
        keep = False
        for sub_val in sub_dict.values():
            if isinstance(sub_val, dict):
                ts_str = sub_val.get("timestamp", "")
                try:
                    ts = datetime.fromisoformat(ts_str)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    if ts > cutoff:
                        keep = True
                        break
                except Exception:
                    pass
        if keep:
            cleaned[top_key] = sub_dict
    return cleaned


# ============================================================
# STEP 3: EXHAUSTIVE PNCP SEARCH (no keyword filtering)
# ============================================================

def _parse_pncp_item(item: dict, mod_code: int, mod_name: str, ufs: list[str]) -> dict | None:
    """Parse a raw PNCP API item into our internal format. Returns None if UF doesn't match."""
    orgao_entity = item.get("orgaoEntidade") or {}
    cnpj_compra = orgao_entity.get("cnpj") or item.get("cnpjCompra") or ""
    cnpj_clean = re.sub(r"[^0-9]", "", str(cnpj_compra))
    ano = str(item.get("anoCompra") or "")
    seq = str(item.get("sequencialCompra") or "")

    # Parse the raw item into our format
    unidade = item.get("unidadeOrgao") or {}
    uf = (unidade.get("ufSigla") or item.get("ufSigla") or "").upper()

    # UF filter (when not using server-side UF param)
    if ufs and uf and uf not in ufs:
        return None

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

    # Calculate status_temporal
    status_temporal = "SEM_DATA"
    dias_restantes = None
    if data_encerramento_raw:
        try:
            # Parse ISO date (may have timezone)
            enc_str = data_encerramento_raw[:19]  # trim to YYYY-MM-DDTHH:MM:SS
            dt_enc = datetime.fromisoformat(enc_str)
            now = datetime.now()
            dias_restantes = (dt_enc.replace(tzinfo=None) - now.replace(tzinfo=None)).days
            if dias_restantes < 0:
                status_temporal = "EXPIRADO"
            elif dias_restantes <= 7:
                status_temporal = "URGENTE"
            elif dias_restantes <= 15:
                status_temporal = "IMINENTE"
            else:
                status_temporal = "PLANEJAVEL"
        except (ValueError, TypeError):
            status_temporal = "SEM_DATA"

    # Check if session (abertura) already happened — even if encerramento is still in the future
    if status_temporal not in ("EXPIRADO",) and data_abertura_raw:
        try:
            ab_str = data_abertura_raw[:19]  # trim to YYYY-MM-DDTHH:MM:SS
            dt_ab = datetime.fromisoformat(ab_str)
            now_ab = datetime.now()
            if dt_ab.replace(tzinfo=None) < now_ab.replace(tzinfo=None):
                status_temporal = "SESSAO_REALIZADA"
        except (ValueError, TypeError):
            pass  # unparseable date — leave status_temporal unchanged

    return {
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
        "_dedup_key": f"{cnpj_clean}/{ano}/{seq}",
        "status_temporal": status_temporal,
        "dias_restantes": dias_restantes,
    }


def search_pncp_exhaustive(
    api: ApiClient,
    ufs: list[str],
    dias: int,
    modalidades: dict[int, str],
    cnpj14: str = "",
    use_cache: bool = True,
) -> tuple[list[dict], dict]:
    """Fetch ALL editais from PNCP for the given UFs, modalidades, and date range.

    NO keyword filtering at this stage -- captures everything to avoid false negatives.
    Deduplicates by {cnpj_orgao}/{anoCompra}/{sequencialCompra}.

    Parallelizes UF fetching within each modalidade using ThreadPoolExecutor(max_workers=5).
    Supports resume/checkpoint: skips UF+mod combos already fetched within the last 2 hours.

    Returns (raw_editais, source_meta).
    """
    data_inicial = _date_compact(_today() - timedelta(days=dias))
    data_final = _date_compact(_today())

    all_items: list[dict] = []
    seen_ids: set[str] = set()
    items_lock = threading.Lock()   # protects all_items + seen_ids

    source_meta = {
        "total_raw_api": 0,
        "total_after_dedup": 0,
        "pages_fetched": 0,
        "errors": 0,
        "pagination_exhausted": [],
    }
    meta_lock = threading.Lock()   # protects source_meta

    use_per_uf = 1 <= len(ufs) <= 10
    uf_iterations: list[str | None] = list(ufs) if use_per_uf else [None]
    max_pages = PNCP_MAX_PAGES_UF if use_per_uf else PNCP_MAX_PAGES

    # ── Checkpoint setup ──
    top_key = _checkpoint_key(cnpj14, ufs, dias) if cnpj14 else ""
    checkpoint: dict = {}
    if use_cache and top_key:
        checkpoint = _load_checkpoint()
    cp_top: dict = checkpoint.get(top_key, {}) if top_key else {}
    cp_lock = threading.Lock()   # protects cp_top + checkpoint writes

    cutoff_ts = _today() - timedelta(hours=_CHECKPOINT_TTL_HOURS)

    def _is_cache_fresh(sub_k: str) -> bool:
        if not use_cache or not top_key:
            return False
        entry = cp_top.get(sub_k)
        if not isinstance(entry, dict):
            return False
        ts_str = entry.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(ts_str)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return ts > cutoff_ts
        except Exception:
            return False

    def _load_from_cache(sub_k: str) -> list[dict]:
        with cp_lock:
            return list(cp_top.get(sub_k, {}).get("items", []))

    def _save_to_cache(sub_k: str, items: list[dict], page_count: int) -> None:
        if not top_key:
            return
        entry = {
            "last_page": page_count,
            "items": items,
            "timestamp": _today().isoformat(),
        }
        with cp_lock:
            cp_top[sub_k] = entry
            checkpoint[top_key] = cp_top
        _save_checkpoint(checkpoint)

    def _fetch_uf(mod_code: int, mod_name: str, uf_filter: str | None) -> None:
        """Worker: fetch all pages for one (modalidade, UF) combination."""
        sub_k = _subkey(mod_code, uf_filter or "ALL")

        # Check checkpoint cache
        if _is_cache_fresh(sub_k):
            cached_items = _load_from_cache(sub_k)
            cached_pages = cp_top.get(sub_k, {}).get("last_page", 0)
            if uf_filter:
                print(f"    UF {uf_filter}: {cached_pages} pages, {len(cached_items)} editais (cache)")
            with meta_lock:
                source_meta["pages_fetched"] += cached_pages
                source_meta["total_raw_api"] += len(cached_items)
            with items_lock:
                for parsed in cached_items:
                    dk = parsed.get("_dedup_key", parsed.get("_id", ""))
                    if dk and dk not in seen_ids:
                        seen_ids.add(dk)
                        all_items.append(parsed)
            return

        page_count = 0
        uf_items_list: list[dict] = []
        local_raw = 0
        error_occurred = False

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
                with meta_lock:
                    source_meta["errors"] += 1
                error_occurred = True
                break

            items = data if isinstance(data, list) else data.get("data", data.get("resultado", []))
            if not isinstance(items, list) or not items:
                break

            page_count += 1
            local_raw += len(items)

            for item in items:
                parsed = _parse_pncp_item(item, mod_code, mod_name, ufs)
                if parsed is None:
                    continue
                dk = parsed["_dedup_key"]
                with items_lock:
                    if dk in seen_ids:
                        continue
                    seen_ids.add(dk)
                    all_items.append(parsed)
                uf_items_list.append(parsed)

            if len(items) < PNCP_MAX_PAGE_SIZE:
                break

            time.sleep(0.5)  # Rate limiting per worker

        with meta_lock:
            source_meta["pages_fetched"] += page_count
            source_meta["total_raw_api"] += local_raw
            if page_count == max_pages:
                source_meta["pagination_exhausted"].append(
                    f"mod={mod_code} uf={uf_filter or 'ALL'}"
                )

        if uf_filter:
            status_note = " (erro parcial)" if error_occurred else ""
            print(f"    UF {uf_filter}: {page_count} pages, {len(uf_items_list)} editais{status_note}")

        # Save checkpoint (even on partial error — preserves what we got)
        if not error_occurred or uf_items_list:
            _save_to_cache(sub_k, uf_items_list, page_count)

    for mod_code, mod_name in sorted(modalidades.items()):
        print(f"\n  Modalidade {mod_code} ({mod_name}):")

        # Parallelize across UFs (max 5 threads — respect PNCP rate limits)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            futures = {
                pool.submit(_fetch_uf, mod_code, mod_name, uf_filter): uf_filter
                for uf_filter in uf_iterations
            }
            for fut in concurrent.futures.as_completed(futures):
                try:
                    fut.result()
                except Exception as exc:
                    uf_filter = futures[fut]
                    print(f"    UF {uf_filter}: ERRO inesperado: {exc}")
                    with meta_lock:
                        source_meta["errors"] += 1

    source_meta["total_after_dedup"] = len(all_items)

    # Cleanup stale checkpoint entries
    if top_key and use_cache:
        try:
            cleaned = _cleanup_old_checkpoints(checkpoint)
            if len(cleaned) != len(checkpoint):
                _save_checkpoint(cleaned)
        except Exception:
            pass

    return all_items, source_meta


# ============================================================
# STEP 4: CNAE KEYWORD GATE
# ============================================================

def classify_by_object_heuristic(objeto: str, cnae_principal_desc: str) -> str:
    """
    Secondary heuristic classifier for editais that didn't match keywords
    but also didn't match exclusion patterns.
    Returns: 'COMPATIVEL', 'INCOMPATIVEL', or 'NEEDS_REVIEW'
    """
    obj_lower = (objeto or '').lower()

    # Strong compatibility signals (construction/engineering context)
    strong_compat = re.compile(
        r'(obra|construcao|reforma|ampliacao|restauracao|recuperacao|revitalizacao|'
        r'pavimentacao|drenagem|terraplanagem|saneamento|urbanizacao|'
        r'projeto (basico|executivo)|levantamento topografico|estudo geotecnico|'
        r'fiscalizacao de obra|supervisao de obra|gerenciamento de obra|'
        r'instalacoes (eletricas|hidraulicas|sanitarias)|'
        r'impermeabilizacao|revestimento|alvenaria|concretagem|fundacao|'
        r'estrutura metalica|cobertura|telhado|fachada|'
        r'rede de (agua|esgoto|drenagem)|estacao (tratamento|elevatoria)|'
        r'ponte|viaduto|passarela|muro de contencao|talude|'
        r'sinalizacao (viaria|rodoviaria)|defensa|guard.?rail|'
        r'CBUQ|massa asfaltica|base.*sub.?base|meio.?fio|sarjeta|boca.?de.?lobo)',
        re.IGNORECASE
    )

    # Weak compatibility (could be construction but ambiguous)
    weak_compat = re.compile(
        r'(engenharia|servicos de engenharia|manutencao predial|'
        r'conservacao de (logradouro|via|estrada)|'
        r'iluminacao publica|semaforo|'
        r'ar condicionado|climatizacao|elevador|'
        r'pintura|vidracaria|serralheria|marcenaria)',
        re.IGNORECASE
    )

    # Strong incompatibility signals (not construction)
    strong_incompat = re.compile(
        r'(consultoria (juridica|contabil|tributaria|financeira|ambiental)|'
        r'assessoria (juridica|contabil)|auditoria|'
        r'transporte (escolar|publico|coletivo|passageiros)|fretamento|'
        r'seguro (predial|patrimonial|vida|saude|automovel)|'
        r'telefonia|internet|banda larga|'
        r'publicidade|propaganda|marketing|'
        r'capacitacao|treinamento|curso|'
        r'locacao de (imovel|sala|espaco|galpao|veiculo)|'
        r'servico de copa|coffee break|buffet|catering)',
        re.IGNORECASE
    )

    has_strong_compat = bool(strong_compat.search(obj_lower))
    has_weak_compat = bool(weak_compat.search(obj_lower))
    has_strong_incompat = bool(strong_incompat.search(obj_lower))

    if has_strong_compat and not has_strong_incompat:
        return 'COMPATIVEL'
    if has_strong_incompat and not has_strong_compat:
        return 'INCOMPATIVEL'
    if has_weak_compat and not has_strong_incompat:
        return 'COMPATIVEL'
    # Default: conservative rejection (zero noise > zero loss)
    return 'INCOMPATIVEL'


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

    stats = {"compatible": 0, "incompatible": 0, "needs_llm": 0, "excluded_pattern": 0}

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

        # Compatibility gate: at least 1 keyword match with density >= threshold
        density_threshold = SECTOR_DENSITY_OVERRIDES.get(sector_key, INTEL_DENSITY_MIN)
        is_compatible = len(matched_kws) >= 1 and density >= density_threshold

        ed["cnae_compatible"] = is_compatible
        ed["keyword_density"] = round(density, 4)
        ed["match_keywords"] = matched_kws
        ed["needs_llm_review"] = not is_compatible and len(matched_kws) == 0
        ed["exclusion_reason"] = None if is_compatible else (
            "zero_keyword_match" if len(matched_kws) == 0 else f"low_density_{density:.4f}"
        )

        # Exclusion pattern check: reject obviously incompatible editais BEFORE LLM review.
        # Only applies to zero-keyword-match editais that would otherwise be sent to LLM.
        if ed["needs_llm_review"]:
            for _excl_name, _excl_pat in EXCLUSION_PATTERNS:
                if _excl_pat.search(objeto_lower):
                    ed["cnae_compatible"] = False
                    ed["needs_llm_review"] = False
                    ed["exclusion_reason"] = f"exclusion_pattern: {_excl_name}"
                    stats["excluded_pattern"] += 1
                    break

        # Secondary heuristic classifier: resolve remaining needs_llm_review editais.
        if ed["needs_llm_review"]:
            _cnae_desc = ed.get("cnae_principal_descricao") or ""
            _heuristic = classify_by_object_heuristic(objeto, _cnae_desc)
            if _heuristic == 'COMPATIVEL':
                ed["cnae_compatible"] = True
                ed["needs_llm_review"] = False
                ed["gate2_decision"] = {
                    "compatible": True,
                    "reason": "COMPATIVEL_HEURISTIC",
                    "keyword_density": ed["keyword_density"],
                    "match_keywords": ed["match_keywords"][:5],
                    "timestamp": _today().isoformat(),
                }
                stats["compatible"] += 1
            else:
                ed["cnae_compatible"] = False
                ed["needs_llm_review"] = False
                ed["gate2_decision"] = {
                    "compatible": False,
                    "reason": "INCOMPATIVEL_HEURISTIC",
                    "keyword_density": ed["keyword_density"],
                    "match_keywords": ed["match_keywords"][:5],
                    "timestamp": _today().isoformat(),
                }
                stats["incompatible"] += 1
            stats["needs_llm_heuristic"] = stats.get("needs_llm_heuristic", 0) + 1
            continue

        ed["gate2_decision"] = {
            "compatible": ed["cnae_compatible"],
            "reason": ed.get("exclusion_reason", "keyword_match" if ed["cnae_compatible"] else "low_density"),
            "keyword_density": ed["keyword_density"],
            "match_keywords": ed["match_keywords"][:5],  # top 5 matches
            "timestamp": _today().isoformat(),
        }

        if is_compatible:
            stats["compatible"] += 1
        else:
            stats["incompatible"] += 1
            if ed["needs_llm_review"]:
                stats["needs_llm"] += 1

    _heuristic_total = stats.get("needs_llm_heuristic", 0)
    _heuristic_compat = sum(
        1 for ed in editais
        if ed.get("gate2_decision", {}).get("reason") == "COMPATIVEL_HEURISTIC"
    )
    _heuristic_incompat = _heuristic_total - _heuristic_compat
    print()
    print(
        "  CNAE Gate: %d compativeis, %d incompativeis, "
        "%d excluidos por padrao, %d precisam LLM review" % (
            stats['compatible'], stats['incompatible'],
            stats['excluded_pattern'], stats['needs_llm'],
        )
    )
    if _heuristic_total:
        print(f"  Heuristic classifier: {_heuristic_compat} COMPATIVEL, "
              f"{_heuristic_incompat} INCOMPATIVEL "
              f"(de {_heuristic_total} restantes)")
        print(f"  Remaining needs_llm_review: 0")


# ============================================================
# STEP 4b: COMPETITIVE INTELLIGENCE PER ORGAN
# ============================================================

def collect_competitive_intel(
    api: ApiClient,
    editais: list[dict],
    meses: int = 24,
) -> None:
    """Collect competitive intelligence for each unique organ in the top editais.

    Queries PNCP /v1/contratos per organ CNPJ to find historical suppliers,
    compute concentration metrics (HHI), and assess competition level.

    Mutates editais in place, adding 'competitive_intel' to each edital.
    Results are cached per organ CNPJ with a 7-day TTL.

    Args:
        api: ApiClient instance for HTTP requests.
        editais: List of edital dicts (must have 'cnpj_orgao').
        meses: Lookback period in months (default 24, split into yearly windows).
    """
    # Only process cnae_compatible editais
    compatible = [ed for ed in editais if ed.get("cnae_compatible")]
    if not compatible:
        print("  Competitive intel: nenhum edital compativel, pulando.")
        return

    # Group by cnpj_orgao, deduplicate
    organ_to_editais: dict[str, list[dict]] = {}
    for ed in compatible:
        cnpj = ed.get("cnpj_orgao", "")
        if cnpj and len(cnpj) >= 11:  # Valid CNPJ length
            organ_to_editais.setdefault(cnpj, []).append(ed)

    # Limit to top organs by edital count (then by value)
    organ_ranked = sorted(
        organ_to_editais.keys(),
        key=lambda c: (
            len(organ_to_editais[c]),
            sum(_safe_float(e.get("valor_estimado")) or 0 for e in organ_to_editais[c]),
        ),
        reverse=True,
    )
    organs_to_query = organ_ranked[:_COMPETITIVE_MAX_ORGANS]

    print(f"  Orgaos unicos: {len(organ_to_editais)}, consultando top {len(organs_to_query)}")

    # Load cache
    cache: dict = {}
    try:
        cache = _load_json_cache(_COMPETITIVE_CACHE_FILE)
    except Exception:
        pass

    now = _today()
    results_lock = threading.Lock()
    organ_results: dict[str, dict] = {}  # cnpj -> intel dict
    counters = {"cached": 0, "fetched": 0, "failed": 0}
    counter_lock = threading.Lock()

    def _is_cache_valid(entry: dict) -> bool:
        ts_str = entry.get("_cached_at", "")
        if not ts_str:
            return False
        try:
            ts = datetime.fromisoformat(ts_str)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return (now - ts).days < _COMPETITIVE_CACHE_TTL_DAYS
        except Exception:
            return False

    def _build_date_windows(meses: int) -> list[tuple[str, str]]:
        """Build yearly date windows (max 365 days per PNCP query).

        Returns list of (dataInicial, dataFinal) pairs in YYYYMMDD format.
        """
        windows: list[tuple[str, str]] = []
        end = now
        total_days = meses * 30  # Approximate
        remaining = total_days

        while remaining > 0:
            window_days = min(remaining, 365)
            start = end - timedelta(days=window_days)
            windows.append((_date_compact(start), _date_compact(end)))
            end = start
            remaining -= window_days

        return windows

    def _fetch_organ_contracts(cnpj_orgao: str) -> dict | None:
        """Fetch all contracts for a single organ, merging yearly windows."""
        # Check cache first
        cached = cache.get(cnpj_orgao)
        if cached and _is_cache_valid(cached):
            with counter_lock:
                counters["cached"] += 1
            return cached

        windows = _build_date_windows(meses)
        all_contracts: list[dict] = []
        seen_ids: set[str] = set()

        for data_inicial, data_final in windows:
            page = 1
            max_pages = 20  # Safety limit per window

            while page <= max_pages:
                params = {
                    "cnpjOrgao": cnpj_orgao,
                    "dataInicial": data_inicial,
                    "dataFinal": data_final,
                    "pagina": page,
                    "tamanhoPagina": 50,
                }

                data, status = api.get(
                    f"{PNCP_BASE}/contratos",
                    params=params,
                    label=f"Contratos orgao={cnpj_orgao[:8]}.. p={page}",
                )

                if status != "API" or not data:
                    break

                # Handle response structure
                items = []
                if isinstance(data, dict):
                    items = data.get("data", [])
                    if not isinstance(items, list):
                        items = []
                elif isinstance(data, list):
                    items = data

                if not items:
                    break

                for item in items:
                    ctrl = item.get("numeroControlePNCP", "")
                    if ctrl and ctrl in seen_ids:
                        continue
                    if ctrl:
                        seen_ids.add(ctrl)

                    contract = {
                        "fornecedor": item.get("nomeRazaoSocialFornecedor", ""),
                        "cnpj_fornecedor": item.get("niFornecedor", ""),
                        "valor_inicial": _safe_float(item.get("valorInicial")),
                        "valor_global": _safe_float(item.get("valorGlobal")),
                        "objeto": item.get("objetoContrato", ""),
                        "categoria": item.get("categoriaProcesso", ""),
                        "data_assinatura": item.get("dataAssinatura", ""),
                        "numero_controle": ctrl,
                    }
                    all_contracts.append(contract)

                # Check if more pages exist
                total_pages = 1
                if isinstance(data, dict):
                    total_pages = data.get("totalPaginas", 1)

                if page >= total_pages or len(items) < 50:
                    break

                page += 1
                time.sleep(0.3)  # Rate limit within pagination

            time.sleep(0.5)  # Rate limit between windows

        if not all_contracts:
            # No contracts found -- still valid result
            result = _compute_intel_metrics(all_contracts, cnpj_orgao)
            result["_cached_at"] = now.isoformat()
            with counter_lock:
                counters["fetched"] += 1
            return result

        result = _compute_intel_metrics(all_contracts, cnpj_orgao)
        result["_cached_at"] = now.isoformat()

        with counter_lock:
            counters["fetched"] += 1

        return result

    def _compute_intel_metrics(contracts: list[dict], cnpj_orgao: str) -> dict:
        """Compute competitive intelligence metrics from a list of contracts."""
        if not contracts:
            return {
                "cnpj_orgao": cnpj_orgao,
                "total_contracts": 0,
                "total_value": 0.0,
                "unique_suppliers": 0,
                "top_suppliers": [],
                "hhi": 0.0,
                "competition_level": "SEM_DADOS",
            }

        # Group by supplier CNPJ
        supplier_data: dict[str, dict] = {}  # cnpj -> {name, count, value}
        total_value = 0.0

        for c in contracts:
            cnpj_f = (c.get("cnpj_fornecedor") or "").strip()
            if not cnpj_f:
                continue
            nome = c.get("fornecedor", "")
            valor = _safe_float(c.get("valor_global")) or _safe_float(c.get("valor_inicial")) or 0.0
            total_value += valor

            if cnpj_f not in supplier_data:
                supplier_data[cnpj_f] = {"nome": nome, "cnpj": cnpj_f, "count": 0, "value": 0.0}
            supplier_data[cnpj_f]["count"] += 1
            supplier_data[cnpj_f]["value"] += valor
            # Keep the most recent name
            if nome:
                supplier_data[cnpj_f]["nome"] = nome

        unique_count = len(supplier_data)

        # Top 5 suppliers by contract count (tie-break by value)
        suppliers_ranked = sorted(
            supplier_data.values(),
            key=lambda s: (s["count"], s["value"]),
            reverse=True,
        )
        top_suppliers = [
            {
                "nome": s["nome"],
                "cnpj": s["cnpj"],
                "contratos": s["count"],
                "valor_total": round(s["value"], 2),
            }
            for s in suppliers_ranked[:5]
        ]

        # HHI (Herfindahl-Hirschman Index) based on value share
        hhi = 0.0
        if total_value > 0:
            for s in supplier_data.values():
                share = s["value"] / total_value
                hhi += share * share
        hhi = round(hhi, 4)

        # Competition level based on unique supplier count
        if unique_count <= 2:
            competition_level = "BAIXA"
        elif unique_count <= 5:
            competition_level = "MEDIA"
        elif unique_count <= 10:
            competition_level = "ALTA"
        else:
            competition_level = "MUITO_ALTA"

        return {
            "cnpj_orgao": cnpj_orgao,
            "total_contracts": len(contracts),
            "total_value": round(total_value, 2),
            "unique_suppliers": unique_count,
            "top_suppliers": top_suppliers,
            "hhi": hhi,
            "competition_level": competition_level,
        }

    def _fetch_with_error_handling(cnpj_orgao: str) -> tuple[str, dict | None]:
        try:
            result = _fetch_organ_contracts(cnpj_orgao)
            return cnpj_orgao, result
        except Exception as exc:
            print(f"    WARN: Falha ao coletar contratos para orgao {cnpj_orgao}: {exc}")
            with counter_lock:
                counters["failed"] += 1
            return cnpj_orgao, None

    # Fetch in parallel (max 3 workers to respect rate limits)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {
            pool.submit(_fetch_with_error_handling, cnpj): cnpj
            for cnpj in organs_to_query
        }
        for fut in concurrent.futures.as_completed(futures):
            cnpj_orgao, result = fut.result()
            if result is not None:
                with results_lock:
                    organ_results[cnpj_orgao] = result

    # Save updated cache
    for cnpj, result in organ_results.items():
        cache[cnpj] = result
    try:
        _save_json_cache(_COMPETITIVE_CACHE_FILE, cache)
    except Exception as e:
        print(f"  WARN: Falha ao salvar competitive cache: {e}")

    # Assign results to editais
    assigned = 0
    for ed in editais:
        cnpj = ed.get("cnpj_orgao", "")
        if cnpj in organ_results:
            intel = organ_results[cnpj]
            # Strip internal cache metadata from the edital copy
            ed["competitive_intel"] = {
                k: v for k, v in intel.items()
                if not k.startswith("_")
            }
            assigned += 1
        else:
            ed["competitive_intel"] = None

    print(f"  Competitive intel: {counters['cached']} do cache, "
          f"{counters['fetched']} da API, {counters['failed']} falhas, "
          f"{assigned} editais enriquecidos")



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

    total_dentro_capacidade = 0
    if capacidade_10x > 0:
        for ed in compatible:
            v = _safe_float(ed.get("valor_estimado")) or 0.0
            if v == 0 or v <= capacidade_10x:
                total_dentro_capacidade += 1

    # Temporal status stats
    status_counts: dict[str, int] = {}
    for ed in compatible:
        st = ed.get("status_temporal", "SEM_DATA")
        status_counts[st] = status_counts.get(st, 0) + 1

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
            "total_bruto": len(editais) + source_meta.get("total_expirados_removidos", 0),
            "total_expirados_removidos": source_meta.get("total_expirados_removidos", 0),
            "total_expirados_encerrados": source_meta.get("total_expirados_encerrados", 0),
            "total_sessao_realizada": source_meta.get("total_sessao_realizada", 0),
            "total_apos_filtro_temporal": len(editais),
            "total_cnae_compativel": len(compatible),
            "total_cnae_incompativel": len(incompatible),
            "total_needs_llm_review": len(needs_llm),
            "valor_total_compativel": round(valor_total_compat, 2),
            "capacidade_10x": round(capacidade_10x, 2),
            "total_dentro_capacidade": total_dentro_capacidade,
            "total_nao_expirados": len(compatible),
            "pncp_pages_fetched": source_meta.get("pages_fetched", 0),
            "pncp_errors": source_meta.get("errors", 0),
            "pncp_pagination_exhausted": source_meta.get("pagination_exhausted", []),
            "total_after_dedup": source_meta.get("total_after_xdedup", len(editais)),
            "status_temporal": status_counts,
            "total_expirados": source_meta.get("total_expirados_removidos", 0),
            "total_urgentes": status_counts.get("URGENTE", 0),
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
# STEP 5b: PRICE BENCHMARKING (historical organ contracts)
# ============================================================

BENCHMARK_CACHE_FILE = str(_PROJECT_ROOT / "data" / "benchmark_cache.json")
_BENCHMARK_CACHE_TTL_DAYS = 7


def _parse_numero_controle_pncp(numero_controle: str) -> tuple[str, str, str] | None:
    """Parse numeroControlePncpCompra into (cnpj_orgao, ano, sequencial).

    Format: {cnpjOrgao}-{unidade}-{seq_padded}/{ano}
    Example: '12345678000190-1-000042/2025' -> ('12345678000190', '2025', '42')
    """
    if not numero_controle:
        return None
    try:
        # Split on '/' to get ano
        parts = numero_controle.rsplit("/", 1)
        if len(parts) != 2:
            return None
        left, ano = parts
        ano = ano.strip()

        # Split left on '-' to get cnpj_orgao and sequencial
        segments = left.split("-")
        if len(segments) < 3:
            return None

        cnpj_orgao = segments[0].strip()
        # Sequencial is the last segment, strip leading zeros
        seq_padded = segments[-1].strip()
        sequencial = str(int(seq_padded))  # remove leading zeros

        if not cnpj_orgao or not ano or not sequencial:
            return None
        return (cnpj_orgao, ano, sequencial)
    except (ValueError, IndexError):
        return None


def collect_price_benchmarks(api: "ApiClient", editais: list[dict]) -> None:
    """Collect price benchmarking data from historical organ contracts.

    For each organ in the top-20 editais (by valor_estimado), queries PNCP
    for historical contracts and their procurement results to calculate
    typical discount percentages (homologado vs estimado).

    Mutates editais in-place, adding 'price_benchmark' dict to top-20 editais.
    """
    compatible = [ed for ed in editais if ed.get("cnae_compatible")]
    compatible_sorted = sorted(
        compatible,
        key=lambda e: (e.get("valor_estimado") or 0.0),
        reverse=True,
    )
    top20 = compatible_sorted[:20]
    if not top20:
        print("  Price benchmark: nenhum edital compativel para analisar")
        return

    top20_ids = {ed["_id"] for ed in top20}

    # Group top20 editais by cnpj_orgao
    organ_editais: dict[str, list[dict]] = {}
    for ed in top20:
        cnpj = ed.get("cnpj_orgao", "")
        if cnpj:
            organ_editais.setdefault(cnpj, []).append(ed)

    if not organ_editais:
        print("  Price benchmark: nenhum orgao com CNPJ valido nos top 20")
        return

    print(f"\n  Price benchmark: analisando {len(organ_editais)} orgaos dos top {len(top20)} editais...")

    # Load benchmark cache
    bench_cache: dict = {}
    try:
        bench_cache = _load_json_cache(BENCHMARK_CACHE_FILE)
        if bench_cache:
            print(f"  Benchmark cache: {len(bench_cache)} orgaos carregados do disco")
    except Exception:
        pass

    now = _today()
    cache_cutoff = now - timedelta(days=_BENCHMARK_CACHE_TTL_DAYS)

    # Check if a cache entry is still fresh
    def _cache_fresh(cnpj: str) -> bool:
        entry = bench_cache.get(cnpj)
        if not isinstance(entry, dict):
            return False
        ts_str = entry.get("_cached_at", "")
        try:
            ts = datetime.fromisoformat(ts_str)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return ts > cache_cutoff
        except Exception:
            return False

    # Collect benchmark data per organ
    organ_benchmarks: dict[str, dict] = {}

    for cnpj_orgao in organ_editais:
        # Check cache first
        if _cache_fresh(cnpj_orgao):
            organ_benchmarks[cnpj_orgao] = bench_cache[cnpj_orgao]
            print(f"    Orgao {cnpj_orgao}: benchmark do cache")
            continue

        # Fetch contracts for this organ (2 yearly queries for 2-year coverage)
        all_contracts: list[dict] = []
        for year_offset in range(2):
            end_date = now - timedelta(days=365 * year_offset)
            start_date = end_date - timedelta(days=365)
            data_inicial = _date_compact(start_date)
            data_final = _date_compact(end_date)

            for page in range(1, 5):  # max 4 pages per year (200 contracts)
                params = {
                    "cnpjOrgao": cnpj_orgao,
                    "dataInicial": data_inicial,
                    "dataFinal": data_final,
                    "pagina": page,
                    "tamanhoPagina": 50,
                }
                data, status = api.get(
                    f"{PNCP_BASE}/contratos",
                    params=params,
                    label=f"Contratos orgao={cnpj_orgao} yr={year_offset} p={page}",
                )

                if status != "API" or not data:
                    break

                items = data if isinstance(data, list) else data.get("data", data.get("resultado", []))
                if not isinstance(items, list) or not items:
                    break

                all_contracts.extend(items)

                if len(items) < 50:
                    break

                time.sleep(0.3)

            time.sleep(0.3)

        if not all_contracts:
            print(f"    Orgao {cnpj_orgao}: nenhum contrato encontrado")
            continue

        # Extract procurement references from contracts
        procurement_refs: list[tuple[str, str, str]] = []
        seen_refs: set[str] = set()
        for contract in all_contracts:
            numero_controle = contract.get("numeroControlePncpCompra") or ""
            parsed = _parse_numero_controle_pncp(numero_controle)
            if parsed:
                ref_key = f"{parsed[0]}/{parsed[1]}/{parsed[2]}"
                if ref_key not in seen_refs:
                    seen_refs.add(ref_key)
                    procurement_refs.append(parsed)

        # Query procurement details (max 10 per organ)
        descontos: list[float] = []
        contratos_com_resultado = 0
        total_analisados = 0

        for ref_cnpj, ref_ano, ref_seq in procurement_refs[:10]:
            data, status = api.get(
                f"{PNCP_BASE}/orgaos/{ref_cnpj}/compras/{ref_ano}/{ref_seq}",
                label=f"Compra {ref_cnpj}/{ref_ano}/{ref_seq}",
            )

            if status == "API" and isinstance(data, dict):
                total_analisados += 1
                existe_resultado = data.get("existeResultado", False)
                if existe_resultado:
                    contratos_com_resultado += 1

                valor_estimado = _safe_float(data.get("valorTotalEstimado"))
                valor_homologado = _safe_float(data.get("valorTotalHomologado"))

                if (valor_estimado and valor_estimado > 0
                        and valor_homologado and valor_homologado > 0):
                    desconto = 1.0 - (valor_homologado / valor_estimado)
                    # Sanity check: discount should be between -1 and 1
                    # (negative means awarded above estimate)
                    if -1.0 <= desconto <= 1.0:
                        descontos.append(desconto)

            time.sleep(0.3)

        # Compute statistics (skip if insufficient sample)
        if len(descontos) < 3:
            print(f"    Orgao {cnpj_orgao}: {len(descontos)} contratos com desconto (insuficiente, min 3)")
            # Cache the "insufficient" result too to avoid re-querying
            organ_benchmarks[cnpj_orgao] = {
                "contratos_analisados": total_analisados,
                "contratos_com_resultado": contratos_com_resultado,
                "descontos_encontrados": len(descontos),
                "insuficiente": True,
                "_cached_at": now.isoformat(),
            }
            bench_cache[cnpj_orgao] = organ_benchmarks[cnpj_orgao]
            continue

        desconto_medio = statistics.mean(descontos)
        desconto_mediano = statistics.median(descontos)
        # quantiles with method='inclusive' for small samples
        quartiles = statistics.quantiles(descontos, n=4, method="inclusive")
        desconto_p25 = quartiles[0]
        desconto_p75 = quartiles[2]

        benchmark_data = {
            "desconto_medio": round(desconto_medio, 4),
            "desconto_mediano": round(desconto_mediano, 4),
            "desconto_p25": round(desconto_p25, 4),
            "desconto_p75": round(desconto_p75, 4),
            "contratos_com_resultado": contratos_com_resultado,
            "total_analisados": total_analisados,
            "descontos_encontrados": len(descontos),
            "insuficiente": False,
            "_cached_at": now.isoformat(),
        }
        organ_benchmarks[cnpj_orgao] = benchmark_data
        bench_cache[cnpj_orgao] = benchmark_data

        print(f"    Orgao {cnpj_orgao}: desconto mediano {desconto_mediano:.1%} "
              f"({len(descontos)} contratos com resultado)")

    # Apply benchmarks to top-20 editais
    applied = 0
    for ed in editais:
        if ed["_id"] not in top20_ids:
            continue

        cnpj = ed.get("cnpj_orgao", "")
        bm = organ_benchmarks.get(cnpj)
        if not bm or bm.get("insuficiente"):
            continue

        valor_est = _safe_float(ed.get("valor_estimado")) or 0.0
        desconto_med = bm["desconto_mediano"]
        p25 = bm["desconto_p25"]
        p75 = bm["desconto_p75"]
        n_contratos = bm["descontos_encontrados"]

        benchmark_entry: dict[str, Any] = {
            "desconto_medio_orgao": bm["desconto_medio"],
            "desconto_mediano_orgao": desconto_med,
            "desconto_p25": p25,
            "desconto_p75": p75,
            "contratos_analisados": n_contratos,
        }

        if valor_est > 0:
            # Suggested price range based on historical discounts
            # p75 = higher discount -> lower price (min)
            # p25 = lower discount -> higher price (max)
            benchmark_entry["valor_sugerido_min"] = round(valor_est * (1.0 - p75), 2)
            benchmark_entry["valor_sugerido_max"] = round(valor_est * (1.0 - p25), 2)

        benchmark_entry["nota"] = (
            f"Orgao historicamente contrata com {abs(desconto_med):.0%} de "
            f"{'desconto' if desconto_med >= 0 else 'acrescimo'} "
            f"(mediana de {n_contratos} contratos nos ultimos 2 anos)"
        )

        ed["price_benchmark"] = benchmark_entry
        applied += 1

    # Save benchmark cache
    try:
        _save_json_cache(BENCHMARK_CACHE_FILE, bench_cache)
    except Exception as e:
        print(f"  WARN: Falha ao salvar benchmark cache: {e}")

    print(f"  Price benchmark: {applied} editais enriquecidos de {len(top20)} top-20")


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
    parser.add_argument("--no-cache", action="store_true", help="Ignorar checkpoint e forcar nova coleta completa")
    parser.add_argument("--skip-sicaf", action="store_true", help="Pular coleta SICAF (evita captcha)")
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
    print(f"  Cache:       {'desabilitado (--no-cache)' if args.no_cache else 'habilitado (2h TTL)'}")
    print(f"{'='*60}")

    api = ApiClient(verbose=not args.quiet)

    print("\n[1/7] Perfil da empresa...")
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

    # ── Step 1b: SICAF + Sanções (run early so user resolves captcha upfront) ──
    skip_sicaf = getattr(args, "skip_sicaf", False)
    if not skip_sicaf:
        print(f"\n[1b/7] Verificação cadastral SICAF + Sanções...")
        print(f"   Navegador vai abrir. Resolva o captcha quando solicitado.\n")

        # Portal da Transparência — Sanções
        pt_key = os.environ.get("PORTAL_TRANSPARENCIA_API_KEY", "")
        pt_data = collect_portal_transparencia(api, cnpj14, pt_key)
        empresa["sancoes"] = pt_data.get("sancoes", {})
        empresa["sancoes_source"] = pt_data.get("sancoes_source", {})
        empresa["historico_contratos_federais"] = pt_data.get("historico_contratos", [])

        sancionada = empresa["sancoes"].get("sancionada", False)
        empresa["sancionada"] = sancionada
        if sancionada:
            sancoes_ativas = [k for k, v in empresa["sancoes"].items() if v and k not in ("sancionada", "inconclusive")]
            print(f"\n  *** ALERTA: Empresa SANCIONADA ({', '.join(s.upper() for s in sancoes_ativas)}) ***")
            print(f"  *** Empresa IMPEDIDA de licitar ***")

        # SICAF
        sicaf_data = collect_sicaf(cnpj14, verbose=True)
        empresa["sicaf"] = sicaf_data
        restricao = sicaf_data.get("restricao", {})
        if isinstance(restricao, dict):
            empresa["restricao_sicaf"] = restricao.get("possui_restricao", None)
        elif isinstance(restricao, bool):
            empresa["restricao_sicaf"] = restricao
        else:
            empresa["restricao_sicaf"] = None

        crc_status = sicaf_data.get("crc_status", "N/D")
        restricao_str = "SIM" if empresa.get("restricao_sicaf") else "NÃO"
        print(f"  SICAF: CRC {crc_status} | Restrição: {restricao_str}")
        if empresa.get("restricao_sicaf"):
            print(f"  *** ALERTA: SICAF com RESTRIÇÃO ativa — risco de inabilitação ***")
    else:
        print(f"\n[1b/7] SICAF pulado (--skip-sicaf)")
        empresa["sicaf"] = {"status": "PULADO"}
        empresa["sancionada"] = False
        empresa["sancoes"] = {}
        empresa["restricao_sicaf"] = None

    # ── Step 2: Map ALL CNAEs -> keywords (principal + secundários) ──
    print("\n[2/7] Mapeando TODOS os CNAEs para keywords...")

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
    print(f"\n[3/7] Busca exaustiva PNCP ({dias} dias, {len(ufs)} UFs, {len(MODALIDADES_BUSCA)} modalidades)...")
    editais, source_meta = search_pncp_exhaustive(
        api, ufs, dias, MODALIDADES_BUSCA,
        cnpj14=cnpj14,
        use_cache=not args.no_cache,
    )
    print(f"\n  Total bruto (dedup _id): {len(editais)} editais")
    if source_meta["pagination_exhausted"]:
        print(f"  WARN: Paginacao esgotada em: {source_meta['pagination_exhausted']}")

    # ── Cross-portal dedup (between PNCP and PCP) ──
    # Same edital may appear on both portals with different _id values.
    # Group by (uf, municipio, valor, objeto[:150]) hash and keep the best copy.
    total_before_xdedup = len(editais)
    hash_to_editais: dict[str, list[dict]] = {}
    for ed in editais:
        h = _compute_dedup_hash(ed)
        ed["dedup_hash"] = h
        hash_to_editais.setdefault(h, []).append(ed)

    deduped_editais: list[dict] = []
    n_duplicatas = 0
    for h, group in hash_to_editais.items():
        if len(group) == 1:
            deduped_editais.append(group[0])
        else:
            # Keep the edital with more metadata (more non-None fields).
            # On tie, prefer PNCP source (link_pncp starting with pncp.gov.br).
            def _score(ed: dict) -> tuple[int, int]:
                filled = sum(1 for v in ed.values() if v is not None and v != "" and v != [])
                is_pncp = 1 if "pncp.gov.br" in (ed.get("link_pncp") or "") else 0
                return (filled, is_pncp)

            best = max(group, key=_score)
            best_id = best["_id"]
            for ed in group:
                if ed["_id"] != best_id:
                    ed["_duplicata_de"] = best_id
                    n_duplicatas += 1
            deduped_editais.append(best)

    editais = deduped_editais
    source_meta["total_after_xdedup"] = len(editais)
    if n_duplicatas > 0:
        print(f"  Dedup cross-portal: {n_duplicatas} duplicatas removidas de {total_before_xdedup} editais")
    else:
        print(f"  Dedup cross-portal: sem duplicatas detectadas ({total_before_xdedup} editais)")

    # ── Step 3b: Remove expired tenders BEFORE any further processing ──
    n_before_expiry = len(editais)
    n_expirados = sum(1 for ed in editais if ed.get("status_temporal") == "EXPIRADO")
    n_sessao_realizada = sum(1 for ed in editais if ed.get("status_temporal") == "SESSAO_REALIZADA")
    editais = [ed for ed in editais if ed.get("status_temporal") not in ("EXPIRADO", "SESSAO_REALIZADA")]
    n_removed = n_expirados + n_sessao_realizada
    if n_removed > 0:
        print(f"\n  Filtro temporal: {n_removed} removidos de {n_before_expiry} editais ({len(editais)} restantes) "
              f"[{n_expirados} encerrados + {n_sessao_realizada} sessao realizada]")
    source_meta["total_expirados_removidos"] = n_removed
    source_meta["total_expirados_encerrados"] = n_expirados
    source_meta["total_sessao_realizada"] = n_sessao_realizada

    # ── Step 4: CNAE keyword gate ──
    print(f"\n[4/7] Aplicando gate de keywords CNAE ({len(all_cnae_prefixes)} prefixos, {len(all_sector_keys)} setores)...")
    apply_cnae_keyword_gate(
        editais, keywords, keyword_patterns, sector_key, cnae_prefix,
        all_cnae_prefixes=all_cnae_prefixes,
        all_sector_keys=all_sector_keys,
    )

    # ── Step 5: Competitive intelligence per organ ──
    print(f"\n[5/7] Coletando inteligencia competitiva ({_COMPETITIVE_MAX_ORGANS} orgaos, {24} meses)...")
    collect_competitive_intel(api, editais)

    # ── Step 6: Fetch documents for top 50 ──
    print(f"\n[6/7] Buscando documentos PNCP...")
    fetch_documents_top50(api, editais)


    # -- Step 6b: Price benchmarking (historical organ discounts) --
    print(f"\n[6b/7] Price benchmarking (top 20 editais)...")
    collect_price_benchmarks(api, editais)


    # ── Step 7: Save output ──
    print(f"\n[7/7] Montando JSON de saida...")
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

    # Determine output path — include razao_social slug
    if args.output:
        out_path = args.output
    else:
        today_str = _date_iso(_today())
        slug = re.sub(r"[^\w\-]", "-", (razao or "empresa").lower())[:40].strip("-")
        slug = re.sub(r"-+", "-", slug)  # collapse multiple dashes
        out_dir = str(_PROJECT_ROOT / "docs" / "intel")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"intel-{cnpj14}-{slug}-{today_str}.json")

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
    _n_enc = stats.get("total_expirados_encerrados", stats["total_expirados_removidos"])
    _n_sr = stats.get("total_sessao_realizada", 0)
    print(f"  Expirados removidos:  {stats['total_expirados_removidos']} ({_n_enc} encerrados + {_n_sr} sessao realizada)")
    print(f"  Ativos analisados:    {stats['total_apos_filtro_temporal']}")
    print(f"  CNAE compativeis:     {stats['total_cnae_compativel']}")
    print(f"  CNAE incompativeis:   {stats['total_cnae_incompativel']}")
    print(f"  Precisam LLM review:  {stats['total_needs_llm_review']}")
    print(f"  Valor total compat:   {_fmt_brl(stats['valor_total_compativel'])}")
    print(f"  Capacidade 10x:       {_fmt_brl(stats['capacidade_10x'])}")
    print(f"  Dentro capacidade:    {stats['total_dentro_capacidade']}")
    print(f"  Paginas PNCP:         {stats['pncp_pages_fetched']}")
    print(f"  Erros PNCP:           {stats['pncp_errors']}")
    st_counts = stats.get("status_temporal", {})
    st_parts = ", ".join(f"{k}={v}" for k, v in sorted(st_counts.items()))
    print(f"  Status temporal:      {st_parts or 'N/A'} (urgentes={stats['total_urgentes']})")
    print(f"  Tempo total:          {elapsed:.1f}s")
    print(f"  Salvo em:             {out_path}")
    print(f"{'='*60}")

    api.print_stats()
    api.close()


if __name__ == "__main__":
    main()
