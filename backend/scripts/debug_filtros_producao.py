#!/usr/bin/env python3
"""
Script de diagnóstico para investigar problema de filtros rejeitando 100% das licitações.

PROBLEMA: "32 licitações encontradas, mas nenhuma atende os critérios"

Este script:
1. Executa busca real na API PNCP
2. Aplica cada filtro individualmente
3. Mostra quantas licitações cada filtro rejeita
4. Identifica o "filtro matador"
5. Exibe amostras das licitações rejeitadas

Uso:
    python backend/scripts/debug_filtros_producao.py
"""

import sys
import os
from datetime import date, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pncp_client import PNCPClient
from filter import (
    aplicar_todos_filtros,
    filtrar_por_status,
    match_keywords,
    KEYWORDS_UNIFORMES,
    KEYWORDS_EXCLUSAO,
)

def main():
    print("=" * 80)
    print("DIAGNÓSTICO: Filtros Rejeitando 100% das Licitações")
    print("=" * 80)

    # 1. Buscar licitações reais do PNCP
    print("\n[1/5] Buscando licitações na API PNCP...")
    client = PNCPClient()

    # Últimos 30 dias, SP apenas (para reduzir volume)
    data_final = date.today()
    data_inicial = data_final - timedelta(days=30)

    print(f"  - Período: {data_inicial} a {data_final}")
    print("  - UF: SP")

    licitacoes_raw = []
    try:
        # Busca SEM filtro de UF (API não aceita esse parâmetro)
        # Vamos filtrar por UF manualmente depois
        for lic in client.fetch_all(
            data_inicial=data_inicial.isoformat(),
            data_final=data_final.isoformat()
        ):
            # Filtra por SP manualmente
            if lic.get("uf") == "SP":
                licitacoes_raw.append(lic)
                if len(licitacoes_raw) >= 100:  # Limita a 100 para debug
                    break
    except Exception as e:
        print("  [ERRO] ao buscar PNCP:", str(e))
        return

    print(f"  ✅ {len(licitacoes_raw)} licitações brutas obtidas")

    if len(licitacoes_raw) == 0:
        print("  ⚠️  Nenhuma licitação encontrada. Abortando diagnóstico.")
        return

    # 2. Teste filtro de Keywords (o mais suspeito)
    print("\n[2/5] Testando filtro de KEYWORDS...")
    keywords_aprovadas = []
    keywords_rejeitadas = []

    for lic in licitacoes_raw:
        objeto = lic.get("objetoCompra", "")
        match, keywords_found = match_keywords(objeto, KEYWORDS_UNIFORMES, KEYWORDS_EXCLUSAO)

        if match:
            keywords_aprovadas.append(lic)
        else:
            keywords_rejeitadas.append(lic)

    print(f"  - Aprovadas (keywords match): {len(keywords_aprovadas)}")
    print(f"  - Rejeitadas (keywords miss): {len(keywords_rejeitadas)}")
    print(f"  - Taxa de aprovação: {len(keywords_aprovadas)/len(licitacoes_raw)*100:.1f}%")

    # Amostras rejeitadas
    if keywords_rejeitadas:
        print("\n  📋 Amostra de objetos REJEITADOS por keywords (primeiros 5):")
        for i, lic in enumerate(keywords_rejeitadas[:5]):
            obj = lic.get("objetoCompra", "")[:150]
            print(f"    {i+1}. {obj}")

    # 3. Teste filtro de Status
    print("\n[3/5] Testando filtro de STATUS...")
    for status_value in ["todos", "recebendo_proposta", "em_julgamento", "encerrada"]:
        resultado = filtrar_por_status(licitacoes_raw, status=status_value)
        print(f"  - status='{status_value}': {len(resultado)}/{len(licitacoes_raw)} aprovadas ({len(resultado)/len(licitacoes_raw)*100:.1f}%)")

    # 4. Teste filtro de Valor
    print("\n[4/5] Testando filtro de VALOR...")

    # Primeiro: estatísticas dos valores
    valores = []
    for lic in licitacoes_raw:
        valor = lic.get("valorTotalEstimado") or lic.get("valorEstimado") or 0
        if isinstance(valor, (int, float)):
            valores.append(float(valor))

    if valores:
        valores_ordenados = sorted(valores)
        print(f"  - Menor valor: R$ {min(valores):,.2f}")
        print(f"  - Maior valor: R$ {max(valores):,.2f}")
        print(f"  - Mediana: R$ {valores_ordenados[len(valores_ordenados)//2]:,.2f}")

        # Testa diferentes faixas
        for (vmin, vmax, label) in [
            (None, None, "Sem limite"),
            (10_000, 10_000_000, "R$ 10k - R$ 10M"),
            (50_000, 5_000_000, "R$ 50k - R$ 5M"),
            (100_000, 1_000_000, "R$ 100k - R$ 1M"),
        ]:
            from filter import filtrar_por_valor
            resultado = filtrar_por_valor(licitacoes_raw, valor_min=vmin, valor_max=vmax)
            print(f"  - {label}: {len(resultado)}/{len(licitacoes_raw)} aprovadas ({len(resultado)/len(licitacoes_raw)*100:.1f}%)")

    # 5. Teste COMPLETO (todos os filtros como produção)
    print("\n[5/5] Testando TODOS OS FILTROS (simulação produção)...")

    licitacoes_filtradas, stats = aplicar_todos_filtros(
        licitacoes_raw,
        ufs_selecionadas={"SP"},
        status="todos",  # Sem filtro de status
        modalidades=None,  # Sem filtro de modalidade
        valor_min=None,  # Sem filtro de valor
        valor_max=None,
        esferas=None,  # Sem filtro de esfera
        municipios=None,  # Sem filtro de município
        keywords=KEYWORDS_UNIFORMES,
        exclusions=KEYWORDS_EXCLUSAO,
    )

    print("\n  📊 RESULTADO FINAL:")
    print(f"    Total: {stats['total']}")
    print(f"    ✅ Aprovadas: {stats['aprovadas']} ({stats['aprovadas']/stats['total']*100:.1f}%)")
    print("    ❌ Rejeitadas:")
    print(f"       - UF: {stats['rejeitadas_uf']}")
    print(f"       - Status: {stats['rejeitadas_status']}")
    print(f"       - Esfera: {stats['rejeitadas_esfera']}")
    print(f"       - Modalidade: {stats['rejeitadas_modalidade']}")
    print(f"       - Município: {stats['rejeitadas_municipio']}")
    print(f"       - Órgão: {stats['rejeitadas_orgao']}")
    print(f"       - Valor: {stats['rejeitadas_valor']}")
    print(f"       - Keyword: {stats['rejeitadas_keyword']} ⚠️  (SUSPEITO)")
    print(f"       - Outros: {stats['rejeitadas_outros']}")

    # Identificar o filtro matador
    rejeicoes = {
        "UF": stats['rejeitadas_uf'],
        "Status": stats['rejeitadas_status'],
        "Esfera": stats['rejeitadas_esfera'],
        "Modalidade": stats['rejeitadas_modalidade'],
        "Município": stats['rejeitadas_municipio'],
        "Órgão": stats['rejeitadas_orgao'],
        "Valor": stats['rejeitadas_valor'],
        "Keyword": stats['rejeitadas_keyword'],
    }

    filtro_matador = max(rejeicoes, key=rejeicoes.get)
    print(f"\n  🎯 FILTRO MATADOR: {filtro_matador} ({rejeicoes[filtro_matador]} rejeições)")

    # Conclusão
    print("\n" + "=" * 80)
    print("CONCLUSÃO:")
    if stats['aprovadas'] == 0:
        print("  ❌ PROBLEMA CONFIRMADO: 100% das licitações estão sendo rejeitadas")
        print(f"  🔍 CAUSA RAIZ PROVÁVEL: Filtro de {filtro_matador}")

        if filtro_matador == "Keyword":
            print("\n  💡 RECOMENDAÇÃO:")
            print("     - Revisar KEYWORDS_UNIFORMES (filter.py linha 72)")
            print("     - Revisar KEYWORDS_EXCLUSAO (filter.py linha 182)")
            print("     - Considerar adicionar mais termos ou relaxar exclusões")
    else:
        taxa = stats['aprovadas'] / stats['total'] * 100
        print(f"  ✅ Filtros estão funcionando ({taxa:.1f}% aprovação)")
        print("  🤔 Problema pode estar nos parâmetros da requisição do usuário")

    print("=" * 80)


if __name__ == "__main__":
    main()
