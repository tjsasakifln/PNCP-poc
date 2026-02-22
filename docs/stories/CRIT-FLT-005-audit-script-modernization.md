# CRIT-FLT-005 — Modernização do Script de Auditoria (15 Setores + LLM + Densidade)

**Prioridade:** P0 — Infraestrutura de Qualidade
**Estimativa:** 6h
**Origem:** Auditoria de Pipeline 2026-02-22
**Track:** Backend

## Problema

Os scripts de auditoria existentes (`audit_filter.py` e `audit_all_sectors.py`) têm lacunas críticas:

1. **`audit_filter.py`** — Só testa setor `vestuario` (hardcoded `KEYWORDS_UNIFORMES`)
2. **`audit_all_sectors.py`** — Testa os 15 setores mas:
   - NÃO testa o LLM arbiter (zona cinza 1-5%)
   - NÃO testa o LLM zero-match (0% density)
   - NÃO testa co-occurrence rules
   - NÃO testa proximity context filter
   - NÃO testa red flags
   - NÃO testa synonym matching
   - NÃO calcula density distribution
   - NÃO identifica false negatives por setor-específico
3. **Nenhum script** gera métricas quantitativas de precision/recall estimados
4. **Nenhum script** testa a PCP v2 ou ComprasGov v3 (apenas PNCP)

## Acceptance Criteria

- [x] **AC1:** Novo script `backend/scripts/audit_pipeline_complete.py` que executa o pipeline COMPLETO (8 etapas + LLM + viability) para cada um dos **15 setores**
- [x] **AC2:** Para cada setor, o script deve:
  - Buscar 100+ itens reais do PNCP (5 UFs, 10 dias)
  - Aplicar `aplicar_todos_filtros()` com sector keywords, exclusions, context_required
  - Calcular distribuição de density zones: >5%, 2-5%, 1-2%, <1%, 0%
  - Classificar itens aprovados em: keyword_high_density, llm_standard, llm_conservative, llm_zero_match, synonym_match
  - Identificar potenciais falsos positivos (itens aprovados com keywords ambíguas)
  - Identificar potenciais falsos negativos (itens rejeitados com hints setoriais)
- [x] **AC3:** Gerar relatório markdown com:
  - Tabela resumo: 15 setores x [aprovados, rejeitados_kw, rejeitados_density, rejeitados_exclusao, llm_calls, falsos_positivos_suspeitos, falsos_negativos_suspeitos]
  - Precision estimada (% de aprovados que são realmente relevantes, via amostragem manual)
  - Recall estimado (% de relevantes que foram aprovados, via heurísticas de falso negativo)
- [x] **AC4:** Incluir análise cross-setor expandida:
  - Quantos itens matcham em 2+ setores
  - Quais pares de setores têm mais colisões
  - Para cada colisão: qual setor é o "correto" (heurística por tipo de órgão)
- [x] **AC5:** Incluir análise de dados PCP v2 (buscar 50 itens, comparar com PNCP):
  - PCP v2 tem `valor_estimado=0` sempre → validar que isso não gera problemas
  - PCP v2 tem descrições mais curtas → validar que density calculation funciona
- [x] **AC6:** Output em 3 formatos:
  - `audit_pipeline_report.md` — relatório legível
  - `audit_pipeline_data.json` — dados brutos para análise
  - `audit_pipeline_metrics.json` — métricas sumarizadas (para CI/CD threshold)
- [x] **AC7:** Adicionar ao CI/CD (opcional): `pytest scripts/test_audit_pipeline.py` que valida métricas mínimas
- [x] **AC8:** Script deve ser executável via `python scripts/audit_pipeline_complete.py --sectors all --ufs SP,MG,RJ --days 10`
- [x] **AC9:** Modo `--dry-run` que usa dados salvos em vez de chamar API (para testes rápidos)
- [x] **AC10:** Modo `--sector vestuario` para auditar um setor específico

## Heurísticas de Detecção

### Falso Positivo (aprovado erroneamente)
- Keyword matched mas objeto descreve item de OUTRO setor
- Density > 5% mas keyword é genérica ("material", "serviço")
- LLM aprovou com confidence < 60

### Falso Negativo (rejeitado erroneamente)
- Objeto contém termos sinônimos não cobertos pelas keywords
- Objeto menciona produtos do setor mas com terminologia não-padrão
- Exclusion keyword bloqueou um item que era genuinamente do setor

### Hints por Setor (para detecção de falsos negativos)

| Setor | Hints Adicionais (não são keywords mas indicam relevância) |
|-------|-----------------------------------------------------------|
| vestuario | "tecido", "algodão", "poliester", "bordado", "serigrafia", "tinturaria" |
| alimentos | "merenda", "refeição", "cozinha", "nutricional", "dieta" |
| informatica | "processador", "memória", "hard disk", "ssd", "placa-mãe" |
| software | "licença", "SaaS", "cloud", "hospedagem", "API" |
| engenharia | "projeto executivo", "ART", "CREA", "topografia" |
| facilities | "limpeza", "conservação", "jardinagem", "portaria" |
| saude | "medicamento", "insumo hospitalar", "ambulância", "prótese" |
| vigilancia | "vigilante", "CFTV", "alarme", "cerca elétrica" |
| transporte | "veículo", "ônibus", "frete", "combustível" |
| mobiliario | "cadeira", "mesa", "estante", "armário" |
| papelaria | "papel A4", "caneta", "toner", "cartucho" |
| manutencao_predial | "pintura", "hidráulica", "elétrica predial", "telhado" |
| engenharia_rodoviaria | "asfalto", "sinalização viária", "guard rail", "pavimento" |
| materiais_eletricos | "cabo", "disjuntor", "quadro elétrico", "luminária" |
| materiais_hidraulicos | "tubo PVC", "registro", "válvula", "caixa d'água" |

## Impacto

- **Cobertura:** Todos os 15 setores com métricas quantitativas
- **Investimento:** Alto (~6h) mas é infraestrutura de qualidade reutilizável
- **Bloqueante para:** CRIT-FLT-001 (validação), CRIT-FLT-004 (validação cross-setor)

## Arquivos

- `backend/scripts/audit_pipeline_complete.py` (NOVO)
- `backend/scripts/audit_pipeline_data.json` (gerado)
- `backend/scripts/audit_pipeline_report.md` (gerado)
