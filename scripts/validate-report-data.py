#!/usr/bin/env python3
"""
Validação determinística de dados do relatório B2G.

Analisa o JSON gerado por collect-report-data.py e emite:
  - BLOCK: Problemas que IMPEDEM a geração do relatório (dados incoerentes)
  - WARN:  Problemas que devem ser mencionados no relatório
  - INFO:  Observações para contexto

Usage:
    python scripts/validate-report-data.py docs/reports/data-CNPJ-DATE.json

Exit codes:
    0 = OK (pode gerar relatório)
    1 = BLOCKED (não gerar — dados incoerentes, corrigir antes)
    2 = WARNINGS (pode gerar, mas relatório deve endereçar cada warning)
"""
from __future__ import annotations

import json
import sys
import io
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def validate(data: dict) -> dict:
    """Validate report data. Returns {blocks: [], warnings: [], info: [], verdict: str}."""
    blocks: list[str] = []
    warnings: list[str] = []
    info: list[str] = []

    empresa = data.get("empresa", {})
    editais = data.get("editais", [])
    metadata = data.get("_metadata", {})
    clusters = data.get("activity_clusters", [])
    kw_source = data.get("_keywords_source", "unknown")

    # ================================================================
    # GATE 1: Coerência semântica (dados fazem sentido?)
    # ================================================================

    # 1a. Keywords source — se fallback CNAE, os editais podem estar no setor errado
    if kw_source == "cnae_fallback":
        historico = empresa.get("historico_contratos", [])
        if len(historico) >= 10:
            blocks.append(
                f"KEYWORDS_CNAE_FALLBACK: Empresa tem {len(historico)} contratos históricos "
                f"mas keywords vieram do CNAE (fallback), não do histórico real. "
                f"Os editais encontrados podem estar no setor ERRADO. "
                f"Ação: re-executar collect-report-data.py com versão corrigida do clustering."
            )
        elif len(historico) > 0:
            warnings.append(
                f"KEYWORDS_CNAE_MIXED: Empresa tem {len(historico)} contratos — poucos para "
                f"clustering robusto. Keywords vieram parcialmente do CNAE. Verificar aderência."
            )
    elif kw_source == "unknown":
        warnings.append(
            "KEYWORDS_SOURCE_UNKNOWN: Campo _keywords_source ausente no JSON. "
            "Não é possível verificar se a busca usou histórico real ou CNAE fallback. "
            "Re-executar collect-report-data.py versão >= d12b03be."
        )

    # 1b. Sector divergence — CNAE não bate com contratos reais
    divergence = empresa.get("_sector_divergence")
    if divergence:
        total = divergence.get("total_contracts", 0)
        sector = divergence.get("sector_contracts", 0)
        pct = divergence.get("pct", 0)
        if sector == 0 and total >= 10:
            blocks.append(
                f"SECTOR_DIVERGENCE_TOTAL: Empresa tem {total} contratos mas ZERO no setor "
                f"dos editais encontrados. O relatório inteiro está baseado em premissa errada. "
                f"Ação: usar clusters de atividade real (activity_clusters) para nortear a busca."
            )
        elif pct < 5 and total >= 10:
            warnings.append(
                f"SECTOR_DIVERGENCE_HIGH: Apenas {sector}/{total} contratos ({pct}%) no setor. "
                f"Relatório deve alertar proeminentemente que acervo técnico é insuficiente."
            )

    # 1c. Habilitação — se >90% dos editais são PARCIALMENTE_APTA, pode indicar setor errado
    # BLOCK somente quando COMBINADO com evidência de divergência setorial (clusters).
    # PARCIALMENTE_APTA sozinho é normal em engenharia (requisitos detalhados exigem análise do edital).
    hab_statuses = [e.get("habilitacao_analysis", {}).get("status", "") for e in editais]
    parcial = hab_statuses.count("PARCIALMENTE_APTA")
    inapta = hab_statuses.count("INAPTA")
    total_avaliados = len([h for h in hab_statuses if h])
    has_sector_divergence = bool(empresa.get("_sector_divergence"))
    if total_avaliados > 5:
        pct_parcial = 100 * parcial / total_avaliados
        historico = empresa.get("historico_contratos", [])
        if pct_parcial >= 90 and len(historico) >= 10 and has_sector_divergence:
            # BLOCK only when BOTH mass-partial AND sector divergence confirmed
            blocks.append(
                f"HABILITACAO_MASS_PARTIAL: {pct_parcial:.0f}% dos editais ({parcial}/{total_avaliados}) "
                f"com habilitação PARCIALMENTE_APTA + divergência setorial confirmada. "
                f"Empresa tem {len(historico)} contratos históricos em setor distinto dos editais. "
                f"AÇÃO OBRIGATÓRIA: Re-executar coleta com keywords do setor real da empresa."
            )
        elif pct_parcial > 90:
            # For materials/supplies companies, high partial habilitacao is EXPECTED
            # (they don't have specific technical qualifications for each edital type).
            # Only warn for specialized fields where qualifications are critical.
            _MATERIALS_CLUSTERS = {
                "saude", "materiais hospitalares", "saneantes", "produtos de limpeza",
                "alimentacao", "generos alimenticios", "material de expediente",
                "expediente e escolar", "moveis", "eletrodomesticos", "vestuario",
                "uniformes", "eventos", "locacao",
            }
            _SPECIALIZED_CLUSTERS = {
                "engenharia", "obras", "consultoria", "assessoria", "informatica",
                "tecnologia", "vigilancia", "seguranca",
            }
            dominant_cluster_label = ""
            if clusters:
                dominant_cluster_label = (clusters[0].get("label") or "").lower()

            is_materials_company = any(
                mat in dominant_cluster_label for mat in _MATERIALS_CLUSTERS
            )
            is_specialized_company = any(
                spec in dominant_cluster_label for spec in _SPECIALIZED_CLUSTERS
            )

            if is_materials_company and not is_specialized_company:
                info.append(
                    f"HABILITACAO_UNIVERSAL_PARCIAL: {parcial}/{total_avaliados} editais "
                    f"({pct_parcial:.0f}%) com habilitação PARCIALMENTE_APTA. "
                    f"Esperado para empresas de materiais/suprimentos (cluster: "
                    f"'{clusters[0].get('label', 'N/A')}') — qualificações técnicas "
                    f"específicas não são o diferencial competitivo."
                )
            else:
                warnings.append(
                    f"HABILITACAO_UNIVERSAL_PARCIAL: {parcial}/{total_avaliados} editais "
                    f"({pct_parcial:.0f}%) com habilitação PARCIALMENTE_APTA. Isso sugere que "
                    f"a empresa não tem acervo técnico completo no setor buscado. Rebaixar recomendações "
                    f"se os editais não corresponderem ao perfil."
                )
        elif pct_parcial >= 70:
            warnings.append(
                f"HABILITACAO_HIGH_PARTIAL: {pct_parcial:.0f}% dos editais com habilitação parcial "
                f"({parcial}/{total_avaliados}). Considerar se editais correspondem ao perfil."
            )

    # 1d. Win probability — se TODAS são <5%, a empresa não é competitiva neste setor
    probs = [e.get("win_probability", {}).get("probability", 0) for e in editais
             if not e.get("risk_score", {}).get("vetoed", False)
             and "Dispensa" not in e.get("modalidade", "")]
    if probs and max(probs) < 0.05 and len(probs) > 10:
        warnings.append(
            f"WIN_PROBABILITY_ALL_LOW: Todas as {len(probs)} probabilidades de vitória "
            f"são <5% (max={max(probs):.1%}). Empresa não é competitiva neste mercado. "
            f"Relatório deve ser transparente sobre perspectivas reais."
        )

    # 1e. ROI — se TODOS são negativos, toda participação é investimento (sem retorno direto)
    rois = [e.get("roi_potential", {}).get("roi_max", 0) for e in editais
            if not e.get("risk_score", {}).get("vetoed", False)
            and "Dispensa" not in e.get("modalidade", "")]
    positive_roi = [r for r in rois if r > 0]
    if rois and not positive_roi and len(rois) > 5:
        warnings.append(
            f"ROI_ALL_NEGATIVE: Todos os {len(rois)} editais têm ROI máximo negativo. "
            f"Nenhuma participação gera retorno financeiro direto positivo. "
            f"Relatório deve classificar TODOS como investimento estratégico, não oportunidade."
        )

    # 1f. Activity clusters — verificar se editais encontrados correspondem aos clusters
    if clusters and editais:
        dominant_clusters = [c for c in clusters if c.get("share_pct", 0) >= 25]
        for dc in dominant_clusters:
            dc_label = dc.get("label", "").lower()
            dc_keywords = [k.lower() for k in dc.get("keywords", [])[:5]]

            # Skip catch-all cluster — it contains miscellaneous items that
            # by definition don't match specific edital keywords.
            if dc_label == "_outros" or not dc_keywords:
                continue

            # Count editais that match this cluster — by origin tag OR by keyword in objeto
            matching = 0
            for ed in editais:
                # Primary: check _cluster_origin (set by collector during multi-cluster search)
                cluster_origin = (ed.get("_cluster_origin") or "").lower()
                if dc_label and dc_label in cluster_origin:
                    matching += 1
                    continue
                # Fallback: check keywords in objeto
                obj = (ed.get("objeto") or "").lower()
                if any(kw in obj for kw in dc_keywords):
                    matching += 1

            match_pct = (matching / len(editais) * 100) if editais else 0
            share_pct = dc.get("share_pct", 0)

            if match_pct < 10 and share_pct >= 25:
                blocks.append(
                    f"CLUSTER_EDITAL_MISMATCH: Cluster dominante '{dc.get('label')}' "
                    f"({share_pct:.0f}% da atividade) está representado em apenas "
                    f"{match_pct:.0f}% dos editais ({matching}/{len(editais)}). "
                    f"Os editais buscados NÃO correspondem ao perfil real da empresa. "
                    f"AÇÃO OBRIGATÓRIA: Re-executar collect-report-data.py — a busca "
                    f"precisa incluir modalidades e keywords adequadas ao cluster dominante. "
                    f"Este bloqueio é IRREVOGÁVEL — não contornar manualmente."
                )
            elif match_pct < 30 and share_pct >= 25:
                warnings.append(
                    f"CLUSTER_EDITAL_LOW_MATCH: Cluster '{dc.get('label')}' "
                    f"({share_pct:.0f}% da atividade) sub-representado nos editais "
                    f"({match_pct:.0f}% de match). Relatório pode estar enviesado para "
                    f"outro setor. Considerar re-executar com busca focada."
                )

    # 2b. Strategic thesis coherence
    strategic_thesis = data.get("strategic_thesis", {})
    if strategic_thesis:
        thesis = strategic_thesis.get("thesis")
        market_trend = strategic_thesis.get("signals", {}).get("trend", {})
        if isinstance(market_trend, str):
            # trend is just the label (e.g. "EXPANSAO"), not a dict
            growth = 0
        else:
            growth = market_trend.get("growth_rate_pct", 0) if isinstance(market_trend, dict) else 0
        if growth < -20:
            warnings.append(
                f"MARKET_CONTRACTION: Mercado do setor mostra contração de {abs(growth):.0f}% "
                f"— relatório deve alertar proeminentemente sobre cenário adverso."
            )

    # 2c. Nature profile coherence
    nature_profile = data.get("nature_profile", {})
    if nature_profile and editais:
        nature_mismatches = 0
        for ed in editais:
            ed_nature = ed.get("_nature", "")
            if ed_nature and ed_nature != "INDEFINIDO":
                share = nature_profile.get(ed_nature, 0)
                if share < 5.0:
                    nature_mismatches += 1
        if nature_mismatches > 0 and len(editais) > 0:
            mismatch_pct = 100.0 * nature_mismatches / len(editais)
            if mismatch_pct > 50:
                warnings.append(
                    f"NATURE_MISMATCH: {nature_mismatches}/{len(editais)} editais ({mismatch_pct:.0f}%) "
                    f"têm natureza incompatível com o perfil histórico da empresa. "
                    f"Perfil: {', '.join(f'{k}({v:.0f}%)' for k, v in nature_profile.items() if v >= 5)}. "
                    f"Considerar re-executar coleta com filtro de natureza ativo."
                )

    # 2e. Portfolio optimization coherence
    portfolio = data.get("portfolio", {})
    optimal_set = portfolio.get("optimal_set", [])
    if isinstance(optimal_set, list) and len(optimal_set) == 0:
        editais_participar = [e for e in data.get("editais", [])
                             if e.get("recomendacao") in ["PARTICIPAR", "AVALIAR COM CAUTELA"]]
        if editais_participar:
            warnings.append(
                f"PORTFOLIO_EMPTY_OPTIMAL: {len(editais_participar)} editais com recomendação "
                f"positiva mas portfólio ótimo está vazio — nenhum edital tem retorno esperado "
                f"positivo após custos de participação."
            )

    # 2d. Scenario analysis
    if editais:
        fragile_count = sum(1 for e in editais
                           if e.get("sensitivity", {}).get("stability") == "FRAGIL"
                           and e.get("recomendacao") in ["PARTICIPAR", "AVALIAR COM CAUTELA"])
        total_relevant = sum(1 for e in editais
                            if e.get("recomendacao") in ["PARTICIPAR", "AVALIAR COM CAUTELA"])
        if total_relevant > 0 and fragile_count / total_relevant > 0.5:
            warnings.append(
                f"HIGH_FRAGILITY: {fragile_count}/{total_relevant} editais relevantes têm "
                f"recomendação FRÁGIL (sensível a perturbação de pesos). "
                f"Relatório deve alertar sobre incerteza nas recomendações."
            )

        # Check if all optimistic scenarios are still negative ROI
        all_optimistic_negative = all(
            e.get("scenarios", {}).get("optimistic", {}).get("roi_max", 0) < 0
            for e in editais
            if e.get("recomendacao") in ["PARTICIPAR", "AVALIAR COM CAUTELA"]
            and e.get("scenarios")
        )
        if all_optimistic_negative and total_relevant > 0:
            warnings.append(
                "ALL_OPTIMISTIC_NEGATIVE: Mesmo no cenário otimista, TODOS os editais "
                "relevantes têm ROI negativo. Participação é investimento estratégico, "
                "não geração de receita. Relatório DEVE comunicar isso explicitamente."
            )

    # INFO items for new fields
    if strategic_thesis:
        info.append(f"THESIS: Posicionamento recomendado = {strategic_thesis.get('thesis', 'N/A')}")

    correlation = portfolio.get("correlation", {})
    if correlation:
        div_score = correlation.get("diversification_score", 0)
        info.append(f"DIVERSIFICATION: Score de diversificação do portfólio = {div_score:.2f}")

    if any(e.get("sensitivity") for e in editais):
        robust = sum(1 for e in editais if e.get("sensitivity", {}).get("stability") == "ROBUSTA")
        fragile = sum(1 for e in editais if e.get("sensitivity", {}).get("stability") == "FRAGIL")
        info.append(f"SENSITIVITY: {robust} recomendações ROBUSTAS, {fragile} FRÁGEIS")

    # ================================================================
    # GATE 2: Completude de dados
    # ================================================================

    # 2a. Fontes obrigatórias
    sources = metadata.get("sources", {})
    for src_name, expected_status in [
        ("opencnpj", "API"),
        ("pncp", "API"),
    ]:
        src = sources.get(src_name, {})
        status = src.get("status", "MISSING")
        if status in ("API_FAILED", "MISSING"):
            blocks.append(
                f"SOURCE_FAILED_{src_name.upper()}: Fonte obrigatória '{src_name}' "
                f"com status '{status}'. Dados incompletos."
            )

    # 2a-sanctions. Portal da Transparência sanctions — nuanced check.
    # The API may return generic results; what matters is whether we could determine
    # the sanctions status for this specific company.
    sancoes_src = sources.get("portal_transparencia_sancoes", {})
    sancoes_status = sancoes_src.get("status", "MISSING")
    sancoes = empresa.get("sancoes", {})
    has_sancoes_data = bool(sancoes) and any(k in sancoes for k in ["ceis", "cnep", "cepim", "ceaf"])
    is_sancionada = sancoes.get("sancionada", any(sancoes.get(k) for k in ["ceis", "cnep", "cepim", "ceaf"]))

    if is_sancionada:
        # Sanctions found — always pass (report must include them regardless of source quality)
        pass
    elif sancoes_status in ("API", "API_PARTIAL") and has_sancoes_data and not is_sancionada:
        # API returned data, we filtered it, company is clean — OK
        if sancoes_status == "API_PARTIAL":
            warnings.append(
                "SANCOES_PARTIAL_VERIFY: Portal da Transparência retornou dados parciais "
                "(API_PARTIAL). Sanções não detectadas, mas verificação pode estar incompleta."
            )
    elif sancoes_status in ("API_FAILED", "MISSING") and not has_sancoes_data:
        # Genuinely failed — we don't know sanctions status at all
        blocks.append(
            f"SOURCE_FAILED_PORTAL_TRANSPARENCIA_SANCOES: Fonte obrigatória "
            f"'portal_transparencia_sancoes' com status '{sancoes_status}'. "
            f"Não é possível verificar sanções (CEIS/CNEP/CEPIM/CEAF)."
        )
    elif sancoes_status in ("API_FAILED", "MISSING") and has_sancoes_data:
        # Source failed but we have cached/partial data — warn, don't block
        warnings.append(
            f"SANCOES_STALE_DATA: Fonte 'portal_transparencia_sancoes' com status "
            f"'{sancoes_status}' mas dados de sanções presentes (possivelmente stale). "
            f"Verificar manualmente se dados estão atualizados."
        )

    # 2b. Editais vazios
    non_dispensa = [e for e in editais if "Dispensa" not in e.get("modalidade", "")]
    if not non_dispensa:
        warnings.append(
            "ZERO_EDITAIS: Nenhum edital relevante encontrado (excluindo dispensas). "
            "Relatório será vazio. Considerar ampliar --dias ou --ufs."
        )

    # 2c. Campos obrigatórios por edital
    missing_scores = sum(1 for e in editais if not e.get("risk_score"))
    if missing_scores > 0 and editais:
        pct = 100 * missing_scores / len(editais)
        if pct > 50:
            warnings.append(
                f"MISSING_RISK_SCORES: {missing_scores}/{len(editais)} editais ({pct:.0f}%) "
                f"sem risk_score. Execute --re-enrich."
            )

    # ================================================================
    # GATE 3: Formato e apresentação
    # ================================================================

    # 3a. Capital social presente
    capital = empresa.get("capital_social", 0)
    if not capital:
        warnings.append("CAPITAL_MISSING: Capital social ausente — impossível avaliar vetos.")

    # 3b. SICAF
    sicaf = data.get("sicaf", {})
    crc = sicaf.get("crc", {})
    if not crc.get("status_cadastral"):
        info.append("SICAF_MISSING: Dados SICAF não disponíveis.")

    # ================================================================
    # GATE 4: Métricas resumo (para o relatório usar)
    # ================================================================

    non_disp_non_vetoed = [
        e for e in editais
        if "Dispensa" not in e.get("modalidade", "")
        and not e.get("risk_score", {}).get("vetoed", False)
    ]
    participar = [e for e in non_disp_non_vetoed if e.get("risk_score", {}).get("total", 0) >= 70]
    avaliar = [e for e in non_disp_non_vetoed if 40 <= e.get("risk_score", {}).get("total", 0) < 70]
    nr = [e for e in non_disp_non_vetoed if e.get("risk_score", {}).get("total", 0) < 40]
    vetoed = [e for e in editais if e.get("risk_score", {}).get("vetoed", False)]

    summary = {
        "total_editais": len(editais),
        "dispensas": len(editais) - len(non_dispensa),
        "participar": len(participar),
        "avaliar": len(avaliar),
        "nao_recomendado": len(nr),
        "vetados": len(vetoed),
        "keywords_source": kw_source,
        "activity_clusters": len(clusters),
        "top_cluster": clusters[0].get("label", "N/A") if clusters else "N/A",
        "sector_divergence": empresa.get("_sector_divergence") is not None,
    }

    # ================================================================
    # VERDICT
    # ================================================================

    if blocks:
        verdict = "BLOCKED"
    elif warnings:
        verdict = "WARNINGS"
    else:
        verdict = "OK"

    return {
        "blocks": blocks,
        "warnings": warnings,
        "info": info,
        "verdict": verdict,
        "summary": summary,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate-report-data.py <path-to-data.json>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"ERROR: File not found: {path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = validate(data)

    print(f"\n{'='*60}")
    print(f"📋 Validação de Dados — {path.name}")
    print(f"{'='*60}")

    # Summary
    s = result["summary"]
    print(f"\n  Editais: {s['total_editais']} total | {s['participar']} PARTICIPAR | "
          f"{s['avaliar']} AVALIAR | {s['nao_recomendado']} NR | {s['vetados']} vetados")
    print(f"  Keywords: {s['keywords_source']} | Clusters: {s['activity_clusters']} "
          f"(top: {s['top_cluster']})")
    print(f"  Divergência setorial: {'SIM ⚠' if s['sector_divergence'] else 'NÃO'}")

    # Blocks
    if result["blocks"]:
        print(f"\n🔴 BLOQUEIOS ({len(result['blocks'])}):")
        for b in result["blocks"]:
            print(f"  ✗ {b}")

    # Warnings
    if result["warnings"]:
        print(f"\n🟡 ALERTAS ({len(result['warnings'])}):")
        for w in result["warnings"]:
            print(f"  ⚠ {w}")

    # Info
    if result["info"]:
        print(f"\n🔵 INFO ({len(result['info'])}):")
        for i in result["info"]:
            print(f"  ℹ {i}")

    # Verdict
    v = result["verdict"]
    print(f"\n{'='*60}")
    if v == "BLOCKED":
        print(f"  🛑 VERDICT: BLOCKED — Relatório NÃO pode ser gerado.")
        print(f"     Corrija os problemas abaixo ANTES de prosseguir.")
        print(f"     NÃO contorne este bloqueio manualmente.")
        print(f"{'='*60}")
        sys.exit(1)
    elif v == "WARNINGS":
        print(f"  ⚠️  VERDICT: WARNINGS — Pode gerar, mas relatório DEVE endereçar cada alerta.")
        print(f"{'='*60}")
        sys.exit(2)
    else:
        print(f"  ✅ VERDICT: OK — Dados coerentes, pode gerar relatório.")
        print(f"{'='*60}")
        sys.exit(0)


if __name__ == "__main__":
    main()
