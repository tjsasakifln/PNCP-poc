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

    # 1c. Habilitação — se >80% dos editais são PARCIALMENTE_APTA, algo está errado
    hab_statuses = [e.get("habilitacao_analysis", {}).get("status", "") for e in editais]
    parcial = hab_statuses.count("PARCIALMENTE_APTA")
    inapta = hab_statuses.count("INAPTA")
    total_avaliados = len([h for h in hab_statuses if h])
    if total_avaliados > 5:
        pct_parcial = 100 * parcial / total_avaliados
        if pct_parcial > 90:
            warnings.append(
                f"HABILITACAO_UNIVERSAL_PARCIAL: {parcial}/{total_avaliados} editais "
                f"({pct_parcial:.0f}%) com habilitação PARCIALMENTE_APTA. Isso sugere que "
                f"a empresa não tem acervo técnico no setor buscado. Rebaixar recomendações."
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
        cluster_keys = {c.get("category_key", "") for c in clusters}
        # Se o cluster dominante é "saude" mas editais são de "engenharia", há incoerência
        top_cluster = clusters[0] if clusters else {}
        top_key = top_cluster.get("category_key", "")
        # Simple heuristic: check if any edital objects match top cluster keywords
        top_kws = [kw.lower() for kw in top_cluster.get("keywords", [])]
        if top_kws:
            match_count = sum(
                1 for e in editais
                if any(kw in (e.get("objeto", "") or "").lower() for kw in top_kws[:3])
            )
            match_pct = 100 * match_count / len(editais) if editais else 0
            if match_pct < 10 and len(editais) > 5:
                blocks.append(
                    f"CLUSTER_EDITAL_MISMATCH: Cluster dominante é '{top_cluster.get('label', '?')}' "
                    f"({top_cluster.get('share_pct', 0)}% dos contratos) mas apenas {match_count}/{len(editais)} "
                    f"editais ({match_pct:.0f}%) contêm keywords deste cluster. "
                    f"Os editais foram buscados no setor ERRADO."
                )

    # ================================================================
    # GATE 2: Completude de dados
    # ================================================================

    # 2a. Fontes obrigatórias
    sources = metadata.get("sources", {})
    for src_name, expected_status in [
        ("opencnpj", "API"),
        ("portal_transparencia_sancoes", "API"),
        ("pncp", "API"),
    ]:
        src = sources.get(src_name, {})
        status = src.get("status", "MISSING")
        if status in ("API_FAILED", "MISSING"):
            blocks.append(
                f"SOURCE_FAILED_{src_name.upper()}: Fonte obrigatória '{src_name}' "
                f"com status '{status}'. Dados incompletos."
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
    participar = [e for e in non_disp_non_vetoed if e.get("risk_score", {}).get("total", 0) >= 60]
    avaliar = [e for e in non_disp_non_vetoed if 30 <= e.get("risk_score", {}).get("total", 0) < 60]
    nr = [e for e in non_disp_non_vetoed if e.get("risk_score", {}).get("total", 0) < 30]
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
        print(f"  ❌ VERDICT: BLOCKED — NÃO gerar relatório. Corrigir dados primeiro.")
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
