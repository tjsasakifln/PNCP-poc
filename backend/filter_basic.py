"""DEBT-118 AC10: Basic filter phases for the filter pipeline.

Contains the Phase 1 (basic filters), Phase 2 (keyword matching),
density decision, item inspection, and deadline safety net logic
extracted from aplicar_todos_filtros() in filter.py.

These are the deterministic, non-LLM phases of the filter pipeline.
"""

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Dict, List

from filter_keywords import (
    KEYWORDS_UNIFORMES,
    KEYWORDS_EXCLUSAO,
    GLOBAL_EXCLUSIONS_NORMALIZED,
    GLOBAL_EXCLUSION_OVERRIDES,
    RED_FLAGS_MEDICAL,
    RED_FLAGS_ADMINISTRATIVE,
    RED_FLAGS_INFRASTRUCTURE,
    has_sector_red_flags,
    has_red_flags,
    match_keywords,
    normalize_text,
    _strip_org_context,
    _get_tracker,
)
from filter_density import check_proximity_context, check_co_occurrence
from filter_status import filtrar_por_prazo_aberto

logger = logging.getLogger(__name__)


def apply_basic_filters(
    licitacoes, ufs_selecionadas, status, modalidades, valor_min,
    valor_max, esferas, municipios, orgaos, setor, modo_busca,
    custom_terms, stats,
) -> List[dict]:
    """Phase 1: UF, Status, Esfera, Modalidade, Municipio, Orgao, Valor, Prazo, Sector Ceiling."""

    # Etapa 1: UF filter
    resultado_uf: List[dict] = []
    for lic in licitacoes:
        uf = lic.get("uf", "")
        if uf in ufs_selecionadas:
            resultado_uf.append(lic)
        else:
            stats["rejeitadas_uf"] += 1
            try:
                _get_tracker().record_rejection(
                    "uf_mismatch", sector=setor,
                    description_preview=lic.get("objetoCompra", "")[:100],
                )
            except Exception:
                pass

    logger.debug(f"  Após filtro UF: {len(resultado_uf)} (rejeitadas: {stats['rejeitadas_uf']})")

    # Etapa 2: Status filter
    if status and status != "todos":
        resultado_status = _filter_status_inline(resultado_uf, status, setor, stats)
    else:
        resultado_status = resultado_uf

    # Etapa 3: Esfera filter
    esferas_efetivas = esferas
    if esferas and set(e.upper() for e in esferas) == {"F", "E", "M"}:
        esferas_efetivas = None

    if esferas_efetivas:
        resultado_esfera = _filter_esfera_inline(resultado_status, esferas_efetivas, stats)
    else:
        resultado_esfera = resultado_status

    # Etapa 4: Modalidade filter
    if modalidades:
        resultado_modalidade: List[dict] = []
        for lic in resultado_esfera:
            mod_id = lic.get("modalidadeId") or lic.get("codigoModalidadeContratacao")
            try:
                mod_id = int(mod_id) if mod_id is not None else None
            except (ValueError, TypeError):
                mod_id = None
            if mod_id in modalidades:
                resultado_modalidade.append(lic)
            else:
                stats["rejeitadas_modalidade"] += 1
        logger.debug(f"  Após filtro Modalidade: {len(resultado_modalidade)} (rejeitadas: {stats['rejeitadas_modalidade']})")
    else:
        resultado_modalidade = resultado_esfera

    # Etapa 5: Municipio filter
    if municipios:
        resultado_municipio: List[dict] = []
        municipios_str = [str(m).strip() for m in municipios]
        for lic in resultado_modalidade:
            codigo = str(lic.get("codigoMunicipioIbge") or lic.get("municipioId") or "").strip()
            if codigo in municipios_str:
                resultado_municipio.append(lic)
            else:
                stats["rejeitadas_municipio"] += 1
        logger.debug(f"  Após filtro Município: {len(resultado_municipio)} (rejeitadas: {stats['rejeitadas_municipio']})")
    else:
        resultado_municipio = resultado_modalidade

    # Etapa 6: Orgao filter
    if orgaos:
        resultado_orgao: List[dict] = []
        orgaos_norm = [normalize_text(o) for o in orgaos if o]
        for lic in resultado_municipio:
            nome_orgao = (lic.get("nomeOrgao", "") or lic.get("orgao", "") or lic.get("nomeUnidade", "") or "")
            nome_orgao_norm = normalize_text(nome_orgao)
            matched = any(termo in nome_orgao_norm for termo in orgaos_norm)
            if matched:
                resultado_orgao.append(lic)
            else:
                stats["rejeitadas_orgao"] += 1
        logger.debug(f"  Após filtro Órgão: {len(resultado_orgao)} (rejeitadas: {stats['rejeitadas_orgao']})")
    else:
        resultado_orgao = resultado_municipio

    # Etapa 7: Valor filter
    if valor_min is not None or valor_max is not None:
        resultado_valor: List[dict] = []
        for lic in resultado_orgao:
            valor = lic.get("valorTotalEstimado") or lic.get("valorEstimado") or 0
            if isinstance(valor, str):
                try:
                    valor = float(valor.replace(".", "").replace(",", "."))
                except ValueError:
                    valor = 0.0
            else:
                valor = float(valor) if valor else 0.0
            if valor_min is not None and valor < valor_min:
                stats["rejeitadas_valor"] += 1
                continue
            if valor_max is not None and valor > valor_max:
                stats["rejeitadas_valor"] += 1
                continue
            resultado_valor.append(lic)
        logger.debug(f"  Após filtro Valor: {len(resultado_valor)} (rejeitadas: {stats['rejeitadas_valor']})")
    else:
        resultado_valor = resultado_orgao

    # Etapa 7.5: Prazo Aberto (STORY-240 AC4)
    if modo_busca == "abertas":
        resultado_valor, rejeitadas_prazo = filtrar_por_prazo_aberto(resultado_valor)
        stats["rejeitadas_prazo_aberto"] = rejeitadas_prazo
        logger.debug(f"  Após filtro Prazo Aberto: {len(resultado_valor)} (rejeitadas: {rejeitadas_prazo})")

    # STORY-179 AC1.3: Sector ceiling
    _skip_sector_ceiling = False
    if custom_terms:
        from config import get_feature_flag as _gff_ac12
        if _gff_ac12("TERM_SEARCH_FILTER_CONTEXT"):
            _skip_sector_ceiling = True

    if setor and not _skip_sector_ceiling:
        from sectors import get_sector
        try:
            setor_config = get_sector(setor)
            max_value = setor_config.max_contract_value
            if max_value is not None:
                resultado_valor_teto: List[dict] = []
                for lic in resultado_valor:
                    valor = lic.get("valorTotalEstimado") or lic.get("valorEstimado") or 0
                    if isinstance(valor, str):
                        try:
                            valor = float(valor.replace(".", "").replace(",", "."))
                        except ValueError:
                            valor = 0.0
                    else:
                        valor = float(valor) if valor else 0.0
                    if valor > max_value:
                        stats["rejeitadas_valor_alto"] += 1
                        logger.debug(
                            f"  Rejeitada por Camada 1A (valor > R$ {max_value:,.2f}): "
                            f"valor=R$ {valor:,.2f} setor={setor} "
                            f"objeto={lic.get('objetoCompra', '')[:80]}"
                        )
                        try:
                            _get_tracker().record_rejection(
                                "value_exceed", sector=setor,
                                description_preview=lic.get("objetoCompra", "")[:100],
                            )
                        except Exception:
                            pass
                        continue
                    resultado_valor_teto.append(lic)
                logger.debug(
                    f"  Após Camada 1A (Value Threshold): {len(resultado_valor_teto)} "
                    f"(rejeitadas_valor_alto: {stats['rejeitadas_valor_alto']})"
                )
                resultado_valor = resultado_valor_teto
        except KeyError:
            logger.warning(f"Setor '{setor}' não encontrado - pulando Camada 1A")

    return resultado_valor


def _filter_status_inline(resultado_uf, status, setor, stats):
    """Inline status filter with inferred status support."""
    resultado_status: List[dict] = []
    status_lower = status.lower()
    _status_distribution: Dict[str, int] = {}

    for lic in resultado_uf:
        status_inferido = lic.get("_status_inferido", "")
        if status_inferido:
            _status_distribution[status_inferido] = _status_distribution.get(status_inferido, 0) + 1
            if status_inferido == status_lower:
                resultado_status.append(lic)
            elif status_inferido in ("desconhecido", "todos") and lic.get("_source") == "PORTAL_COMPRAS":
                lic["_status_unconfirmed"] = True
                resultado_status.append(lic)
                try:
                    from metrics import FILTER_PASSTHROUGH_TOTAL
                    FILTER_PASSTHROUGH_TOTAL.labels(reason="unknown_status").inc()
                except Exception:
                    pass
            else:
                stats["rejeitadas_status"] += 1
                try:
                    _get_tracker().record_rejection(
                        "status_mismatch", sector=setor,
                        description_preview=lic.get("objetoCompra", "")[:100],
                    )
                except Exception:
                    pass
        else:
            situacao = (
                lic.get("situacaoCompraNome", "") or lic.get("situacaoCompra", "")
                or lic.get("situacao", "") or lic.get("statusCompra", "") or ""
            ).lower()
            status_map = {
                "recebendo_proposta": [
                    "recebendo propostas", "aberta", "publicada",
                    "divulgada", "vigente", "ativa", "em andamento"
                ],
                "em_julgamento": [
                    "propostas encerradas", "em julgamento", "julgamento",
                    "análise", "analise", "classificação", "classificacao"
                ],
                "encerrada": [
                    "encerrada", "finalizada", "homologada", "adjudicada",
                    "anulada", "revogada", "cancelada", "fracassada",
                    "deserta", "suspensa", "concluída", "concluida"
                ],
            }
            termos = status_map.get(status_lower, [])
            if any(t in situacao for t in termos):
                resultado_status.append(lic)
            else:
                stats["rejeitadas_status"] += 1
                try:
                    _get_tracker().record_rejection(
                        "status_mismatch", sector=setor,
                        description_preview=lic.get("objetoCompra", "")[:100],
                    )
                except Exception:
                    pass

    logger.debug(
        f"  Status filter: wanted='{status_lower}', "
        f"distribution={_status_distribution}, "
        f"passed={len(resultado_status)}, rejected={stats['rejeitadas_status']}"
    )
    logger.debug(f"  Após filtro Status: {len(resultado_status)} (rejeitadas: {stats['rejeitadas_status']})")
    return resultado_status


def _filter_esfera_inline(resultado_status, esferas_efetivas, stats):
    """Inline esfera filter with fail-open for unknown sphere."""
    resultado_esfera: List[dict] = []
    esferas_upper = [e.upper() for e in esferas_efetivas]

    for lic in resultado_status:
        esfera_id = (lic.get("esferaId", "") or lic.get("esfera", "") or "").upper()
        if esfera_id in esferas_upper:
            resultado_esfera.append(lic)
        elif esfera_id:
            stats["rejeitadas_esfera"] += 1
        else:
            tipo_orgao = (lic.get("tipoOrgao", "") or lic.get("nomeOrgao", "")).lower()
            matched = False
            for esf in esferas_upper:
                if esf == "F" and any(k in tipo_orgao for k in ["federal", "ministério", "ministerio"]):
                    matched = True
                elif esf == "E" and any(k in tipo_orgao for k in ["estadual", "estado"]):
                    matched = True
                elif esf == "M" and any(k in tipo_orgao for k in ["municipal", "prefeitura"]):
                    matched = True
            if matched:
                resultado_esfera.append(lic)
            else:
                lic["_esfera_inferred"] = False
                resultado_esfera.append(lic)
                stats["esfera_indeterminada"] += 1

    logger.debug(
        f"  Após filtro Esfera: {len(resultado_esfera)} "
        f"(rejeitadas: {stats['rejeitadas_esfera']}, "
        f"indeterminadas: {stats['esfera_indeterminada']})"
    )
    return resultado_esfera


def apply_keyword_filters(
    resultado_valor, keywords, exclusions, context_required, setor,
    custom_terms, on_progress, stats,
) -> List[dict]:
    """Phase 2: Keyword matching + org context stripping + proximity + co-occurrence."""
    kw = keywords if keywords else set()
    exc = exclusions if exclusions else set()

    # Pre-compile regex patterns
    compiled_patterns: Dict[str, re.Pattern] = {}
    for keyword in kw:
        try:
            escaped = re.escape(keyword)
            compiled_patterns[keyword] = re.compile(
                rf'\b{escaped}\b', re.IGNORECASE | re.UNICODE
            )
        except re.error:
            logger.warning(f"Failed to compile regex for keyword: {keyword}")

    # STORY-328: Effective global exclusions
    _effective_global_exc: set = set()
    if setor:
        _sector_overrides = GLOBAL_EXCLUSION_OVERRIDES.get(setor, set())
        _effective_global_exc = GLOBAL_EXCLUSIONS_NORMALIZED - _sector_overrides

    # Progress tracking
    _kw_total = len(resultado_valor)
    _kw_progress_step = min(50, max(1, int(_kw_total * 0.05))) if on_progress and _kw_total > 0 else 0

    resultado_keyword: List[dict] = []
    for _kw_idx, lic in enumerate(resultado_valor):
        if _kw_progress_step > 0 and (_kw_idx + 1) % _kw_progress_step == 0:
            on_progress(_kw_idx + 1, _kw_total, "filter")

        objeto = lic.get("objetoCompra", "")
        objeto_for_matching = _strip_org_context(objeto)

        if objeto_for_matching != objeto.strip():
            lic["_org_context_stripped"] = True
            removed_clause = objeto[len(objeto_for_matching):].strip() if len(objeto_for_matching) < len(objeto) else ""
            logger.debug(
                f"STORY-328: Stripped org context from bid "
                f"{lic.get('pncpId', lic.get('id', '?'))}: '{removed_clause[:120]}'"
            )
            try:
                from metrics import ORG_CONTEXT_STRIPPED
                ORG_CONTEXT_STRIPPED.labels(sector=setor or "unknown").inc()
            except Exception:
                pass
        else:
            lic["_org_context_stripped"] = False

        # Global exclusions
        if _effective_global_exc:
            objeto_norm_ge = normalize_text(objeto_for_matching)
            _hit_global_exc = any(ge in objeto_norm_ge for ge in _effective_global_exc)
            if _hit_global_exc:
                stats["rejeitadas_keyword"] = stats.get("rejeitadas_keyword", 0) + 1
                try:
                    _get_tracker().record_rejection(
                        "global_exclusion", sector=setor, description_preview=objeto[:100],
                    )
                except Exception:
                    pass
                continue

        # STORY-328 AC6: Cross-validate with nomeOrgao
        nome_orgao = lic.get("nomeOrgao", "") or lic.get("orgaoEntidade", {}).get("razaoSocial", "") or ""
        nome_orgao_norm = normalize_text(nome_orgao) if nome_orgao else ""

        match, matched_terms = match_keywords(
            objeto_for_matching, kw, exc, context_required,
            compiled_patterns=compiled_patterns,
        )

        # AC6: Discount keywords that appear ONLY in the org name
        if match and nome_orgao_norm and matched_terms:
            objeto_stripped_norm = normalize_text(objeto_for_matching)
            real_terms = [t for t in matched_terms if normalize_text(t) in objeto_stripped_norm]
            if not real_terms:
                match = False
            else:
                matched_terms = real_terms

        if match:
            lic["_matched_terms"] = matched_terms
            objeto_norm = normalize_text(objeto_for_matching)
            total_words = len(objeto_norm.split())
            term_count = sum(objeto_norm.count(normalize_text(t)) for t in matched_terms)
            lic["_term_density"] = term_count / total_words if total_words > 0 else 0
            resultado_keyword.append(lic)
        else:
            stats["rejeitadas_keyword"] += 1
            try:
                _get_tracker().record_rejection(
                    "keyword_miss", sector=setor, description_preview=objeto[:100],
                )
            except Exception:
                pass

    # Proximity Context Filter (Camada 1B.3)
    from config import get_feature_flag
    stats["proximity_rejections"] = 0
    _skip_proximity = bool(custom_terms) and get_feature_flag("TERM_SEARCH_FILTER_CONTEXT")
    if get_feature_flag("PROXIMITY_CONTEXT_ENABLED") and setor and not _skip_proximity:
        resultado_keyword = _apply_proximity_filter(resultado_keyword, setor, stats)

    # Co-occurrence (Camada 1B.5)
    stats["co_occurrence_rejections"] = 0
    stats["co_occurrence_rejections_by_sector"] = {}
    _skip_co_occurrence = bool(custom_terms) and get_feature_flag("TERM_SEARCH_FILTER_CONTEXT")
    if get_feature_flag("CO_OCCURRENCE_RULES_ENABLED") and setor and not _skip_co_occurrence:
        resultado_keyword = _apply_co_occurrence_filter(resultado_keyword, setor, stats)

    return resultado_keyword


def _apply_proximity_filter(resultado_keyword, setor, stats):
    """Apply proximity context filter (Camada 1B.3)."""
    from config import PROXIMITY_WINDOW_SIZE
    from sectors import SECTORS as _SECTORS_PROX

    other_sigs: Dict[str, set] = {}
    for sid, scfg in _SECTORS_PROX.items():
        if sid != setor and scfg.signature_terms:
            other_sigs[sid] = scfg.signature_terms
    if not other_sigs:
        return resultado_keyword

    resultado_after_prox: List[dict] = []
    for lic in resultado_keyword:
        matched = lic.get("_matched_terms", [])
        if not matched:
            resultado_after_prox.append(lic)
            continue
        objeto = lic.get("objetoCompra", "")
        should_reject, rejection_detail = check_proximity_context(
            objeto, matched, setor, other_sigs, PROXIMITY_WINDOW_SIZE
        )
        if should_reject:
            stats["proximity_rejections"] += 1
            lic["_rejection_reason"] = "proximity_context"
            lic["_rejection_detail"] = rejection_detail
            logger.debug(f"Camada 1B.3: REJECT (proximity) detail={rejection_detail} objeto={objeto[:80]}")
            try:
                _get_tracker().record_rejection(
                    "proximity_context", sector=setor, description_preview=objeto[:100],
                )
            except Exception:
                pass
        else:
            resultado_after_prox.append(lic)
    if stats["proximity_rejections"] > 0:
        logger.info(f"Camada 1B.3 (Proximity): rejected {stats['proximity_rejections']} bids in sector '{setor}'")
    return resultado_after_prox


def _apply_co_occurrence_filter(resultado_keyword, setor, stats):
    """Apply co-occurrence negative patterns (Camada 1B.5)."""
    from sectors import get_sector as _get_sector_co
    try:
        setor_config_co = _get_sector_co(setor)
        co_rules = setor_config_co.co_occurrence_rules
        if not co_rules:
            return resultado_keyword
    except KeyError:
        return resultado_keyword

    resultado_after_co: List[dict] = []
    for lic in resultado_keyword:
        objeto = lic.get("objetoCompra", "")
        should_reject, rejection_detail = check_co_occurrence(objeto, co_rules, setor)
        if should_reject:
            stats["co_occurrence_rejections"] += 1
            stats["co_occurrence_rejections_by_sector"][setor] = (
                stats["co_occurrence_rejections_by_sector"].get(setor, 0) + 1
            )
            lic["_rejection_reason"] = "co_occurrence"
            lic["_rejection_detail"] = rejection_detail
            logger.debug(f"Camada 1B.5: REJECT (co-occurrence) detail={rejection_detail} objeto={objeto[:80]}")
            try:
                _get_tracker().record_rejection(
                    "co_occurrence", sector=setor, description_preview=objeto[:100],
                )
            except Exception:
                pass
        else:
            resultado_after_co.append(lic)
    if stats["co_occurrence_rejections"] > 0:
        logger.info(f"Camada 1B.5 (Co-occurrence): rejected {stats['co_occurrence_rejections']} bids in sector '{setor}'")
    return resultado_after_co


def apply_item_inspection(resultado_keyword, setor, keywords, stats) -> List[dict]:
    """Phase 2C: Item inspection for gray zone bids (Camada 1C)."""
    from config import TERM_DENSITY_HIGH_THRESHOLD, get_feature_flag

    stats["item_inspections_performed"] = 0
    stats["item_inspections_accepted"] = 0
    resultado_item_accepted: List[dict] = []

    if not (setor and get_feature_flag("ITEM_INSPECTION_ENABLED")):
        return resultado_item_accepted

    gray_zone = [
        lic for lic in resultado_keyword
        if 0 < lic.get("_term_density", 0) <= TERM_DENSITY_HIGH_THRESHOLD
    ]
    if not gray_zone:
        return resultado_item_accepted

    try:
        from item_inspector import inspect_bids_in_filter
        from sectors import get_sector as _get_sector_insp

        kw = keywords if keywords else set()  # noqa: F841
        setor_config_insp = _get_sector_insp(setor)
        ds = setor_config_insp.domain_signals

        item_accepted, item_remaining, item_metrics = inspect_bids_in_filter(
            gray_zone_bids=gray_zone,
            sector_keywords={kw_item.lower() for kw_item in setor_config_insp.keywords},
            ncm_prefixes=ds.ncm_prefixes,
            unit_patterns=ds.unit_patterns,
            size_patterns=ds.size_patterns,
        )

        stats["item_inspections_performed"] = item_metrics.get("item_inspections_performed", 0)
        stats["item_inspections_accepted"] = item_metrics.get("item_inspections_accepted", 0)
        resultado_item_accepted = item_accepted

        gray_zone_ids = {id(lic) for lic in gray_zone}
        remaining_ids = {id(lic) for lic in item_remaining}
        resultado_keyword[:] = [
            lic for lic in resultado_keyword
            if id(lic) not in gray_zone_ids or id(lic) in remaining_ids
        ]
    except Exception as e:
        logger.warning(f"D-01 item inspection failed, continuing with LLM: {e}")

    return resultado_item_accepted


def apply_density_decision(resultado_keyword, setor, stats):
    """Phase 2A: Density decision + red flags. Returns (densidade_approved, llm_candidates)."""
    from config import (
        TERM_DENSITY_HIGH_THRESHOLD, TERM_DENSITY_MEDIUM_THRESHOLD,
        TERM_DENSITY_LOW_THRESHOLD, get_feature_flag,
    )
    from middleware import search_id_var

    resultado_densidade: List[dict] = []
    resultado_llm_standard: List[dict] = []
    resultado_llm_conservative: List[dict] = []
    stats["rejeitadas_red_flags"] = 0
    stats["rejeitadas_red_flags_setorial"] = 0
    _sector_rf_enabled = get_feature_flag("SECTOR_RED_FLAGS_ENABLED")

    for lic in resultado_keyword:
        density = lic.get("_term_density", 0)
        _search_id = search_id_var.get("-")
        trace_id = _search_id[:8] if _search_id != "-" else str(uuid.uuid4())[:8]
        lic["_trace_id"] = trace_id
        obj_preview = lic.get("objetoCompra", "")[:100]

        if density > TERM_DENSITY_HIGH_THRESHOLD:
            stats["aprovadas_alta_densidade"] += 1
            lic["_relevance_source"] = "keyword"
            lic["_confidence_score"] = 95
            lic["_llm_evidence"] = []
            logger.debug(f"[{trace_id}] Camada 2A: ACCEPT (alta densidade) density={density:.1%} objeto={obj_preview}")
            resultado_densidade.append(lic)
        elif density < TERM_DENSITY_LOW_THRESHOLD:
            stats["rejeitadas_baixa_densidade"] += 1
            logger.debug(f"[{trace_id}] Camada 2A: REJECT (baixa densidade) density={density:.1%} objeto={obj_preview}")
            try:
                _get_tracker().record_rejection("density_low", sector=setor, description_preview=obj_preview)
            except Exception:
                pass
        elif density >= TERM_DENSITY_MEDIUM_THRESHOLD:
            if _check_red_flags(lic, setor, _sector_rf_enabled, trace_id, density, obj_preview, stats):
                continue
            stats["duvidosas_llm_arbiter"] += 1
            lic["_llm_prompt_level"] = "standard"
            resultado_llm_standard.append(lic)
        else:
            if _check_red_flags(lic, setor, _sector_rf_enabled, trace_id, density, obj_preview, stats):
                continue
            stats["duvidosas_llm_arbiter"] += 1
            lic["_llm_prompt_level"] = "conservative"
            resultado_llm_conservative.append(lic)

    logger.debug(
        f"  Após Camada 2A (Term Density): "
        f"{len(resultado_densidade)} aprovadas (alta densidade), "
        f"{len(resultado_llm_standard)} duvidosas (LLM standard), "
        f"{len(resultado_llm_conservative)} duvidosas (LLM conservative), "
        f"{stats.get('rejeitadas_red_flags', 0)} rejeitadas (red flags), "
        f"{stats.get('rejeitadas_red_flags_setorial', 0)} rejeitadas (sector red flags), "
        f"{stats['rejeitadas_baixa_densidade']} rejeitadas (baixa densidade)"
    )
    return resultado_densidade, resultado_llm_standard + resultado_llm_conservative


def _check_red_flags(lic, setor, sector_rf_enabled, trace_id, density, obj_preview, stats) -> bool:
    """Check sector + generic red flags. Returns True if bid should be rejected."""
    objeto_norm = normalize_text(lic.get("objetoCompra", ""))

    if sector_rf_enabled and setor:
        s_flagged, s_flags = has_sector_red_flags(objeto_norm, setor)
        if s_flagged:
            stats["rejeitadas_red_flags_setorial"] += 1
            logger.debug(f"[{trace_id}] Camada 2A: REJECT (sector red flags: {s_flags}) density={density:.1%} objeto={obj_preview}")
            try:
                _get_tracker().record_rejection("red_flags_sector", sector=setor, description_preview=obj_preview)
            except Exception:
                pass
            return True

    flagged, flag_terms = has_red_flags(
        objeto_norm,
        [RED_FLAGS_MEDICAL, RED_FLAGS_ADMINISTRATIVE, RED_FLAGS_INFRASTRUCTURE],
        setor=setor,
    )
    if flagged:
        stats["rejeitadas_red_flags"] += 1
        logger.debug(f"[{trace_id}] Camada 2A: REJECT (red flags: {flag_terms}) density={density:.1%} objeto={obj_preview}")
        return True
    return False


def apply_deadline_safety_net(resultado_keyword, status, stats) -> List[dict]:
    """Etapa 9: Deadline safety net for recebendo_proposta status."""
    if not (status and status.lower() == "recebendo_proposta"):
        return resultado_keyword

    aprovadas: List[dict] = []
    agora = datetime.now(timezone.utc)

    for lic in resultado_keyword:
        data_enc_str = lic.get("dataEncerramentoProposta")

        if data_enc_str:
            try:
                data_enc = datetime.fromisoformat(data_enc_str.replace("Z", "+00:00"))
                if data_enc.tzinfo is None:
                    data_enc = data_enc.replace(tzinfo=timezone.utc)
                if data_enc < agora:
                    stats["rejeitadas_prazo"] += 1
                    logger.debug(f"  Rejeitada por prazo: encerramento={data_enc.date()} objeto={lic.get('objetoCompra', '')[:80]}")
                    continue
            except (ValueError, AttributeError):
                logger.warning(f"Data de encerramento invalida no safety net: '{data_enc_str}'")
            aprovadas.append(lic)
            continue

        data_ab_str = lic.get("dataAberturaProposta")
        if data_ab_str:
            try:
                data_ab = datetime.fromisoformat(data_ab_str.replace("Z", "+00:00"))
                if data_ab.tzinfo is None:
                    data_ab = data_ab.replace(tzinfo=timezone.utc)
                dias = (agora - data_ab).days
                if dias <= 15:
                    aprovadas.append(lic)
                    continue
                elif dias <= 30:
                    sit = (lic.get("situacaoCompraNome", "") or lic.get("situacao", "") or "").lower()
                    if "recebendo" in sit:
                        aprovadas.append(lic)
                        continue
                    else:
                        stats["rejeitadas_prazo"] += 1
                        continue
                else:
                    stats["rejeitadas_prazo"] += 1
                    continue
            except (ValueError, AttributeError):
                pass

        data_pub_str = lic.get("dataPublicacaoPncp") or lic.get("dataPublicacao")
        if data_pub_str:
            try:
                data_pub = datetime.fromisoformat(data_pub_str.replace("Z", "+00:00"))
                if data_pub.tzinfo is None:
                    data_pub = data_pub.replace(tzinfo=timezone.utc)
                if (agora - data_pub).days <= 15:
                    aprovadas.append(lic)
                    continue
                else:
                    stats["rejeitadas_prazo"] += 1
                    continue
            except (ValueError, AttributeError):
                pass

        stats["rejeitadas_prazo"] += 1

    logger.debug(
        f"  Após filtro Prazo (safety net + heurísticas): {len(aprovadas)} "
        f"(rejeitadas: {stats['rejeitadas_prazo']})"
    )
    return aprovadas
