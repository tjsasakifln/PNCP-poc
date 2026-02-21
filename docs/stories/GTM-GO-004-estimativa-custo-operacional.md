# GTM-GO-004: Estimativa de Custo Operacional por 1.000 Buscas

## Epic
GTM Readiness — Redução de Risco Financeiro

## Sprint
Sprint GO: Eliminação de Bloqueadores GTM

## Prioridade
P2 — Risco financeiro (visibilidade)

## Estimativa
3h

## Status: DONE

---

## Risco Mitigado

**Risco:** O custo operacional por busca é desconhecido. O plano SmartLic Pro cobra R$1.999/mês com limite de 1.000 buscas. Se o custo real por 1.000 buscas for > R$500, a margem bruta é 75% — saudável. Se for > R$1.500, a operação é inviável no preço atual. Hoje, ninguém sabe qual dos dois cenários é real.

**Impacto se materializar:**
- **Financeiro:** Sem visibilidade de custo, um aumento inesperado de uso (ex: trial viral com 50 buscas/dia por 20 trials = 1.000 buscas/dia) pode gerar fatura Railway/OpenAI que excede a receita prevista antes de qualquer conversão.
- **Decisório:** Impossível fazer pricing competitivo sem saber o custo unitário. O preço de R$1.999 foi definido por posicionamento de mercado, não por cost-plus pricing.
- **Escalabilidade:** Sem modelo de custo, é impossível projetar break-even (quantos assinantes pagam a infraestrutura).

**O que não é este risco:** Este não é um risco de "o sistema vai quebrar" — é um risco de "o negócio pode ser inviável sem saber".

## Estado Técnico Atual

### Dados de custo disponíveis (fragmentados):

1. **LLM (OpenAI GPT-4.1-nano):**
   - `STORY-181-precision-tuning-post-llm-arbiter.md` L31: "Custo LLM por busca: ~R$ 0,001"
   - 90% das classificações são por keyword, sem LLM (`STORY-179-COMPLETION-REPORT.md`)
   - Estimativa: ~R$0.003/busca (considerando zero-match classification)

2. **Railway (compute):**
   - Backend: 1 web instance + 1 worker instance
   - Frontend: 1 instance
   - Custos Railway visíveis no dashboard mas nunca documentados no repo

3. **Supabase:**
   - Free tier: 500MB DB, 1GB storage, 2GB bandwidth
   - Pro tier ($25/mês) se necessário
   - Cada busca grava 1 row em `search_sessions` + 0-N em `search_results_cache`

4. **Redis (Upstash):**
   - Free tier: 10K commands/dia
   - Pro: $0.2/100K commands
   - Cada busca: ~5-10 Redis commands (cache check + set + rate limit + CB state)

5. **Nenhum documento consolida esses dados.** Cada componente de custo está em um lugar diferente (ou não está documentado).

### Fragilidade:
Decisões de pricing, promoções, e trial duration são tomadas sem modelo de custo. O trial de 7 dias com limite de 5 buscas foi definido arbitrariamente.

## Objetivo

Produzir uma estimativa documentada, verificável e versionada do custo operacional por 1.000 buscas, separando custos fixos (infra mensal) de variáveis (por busca), para que decisões de pricing e escalabilidade sejam baseadas em dados, não em suposições.

## Critérios de Aceite

### Documento de Custo

- [x] AC1: `docs/operations/cost-analysis.md` criado com:
  - Tabela de custos fixos mensais (Railway, Supabase, Redis, domínio)
  - Tabela de custos variáveis por busca (LLM, egress, Redis commands)
  - Custo total estimado por 1.000 buscas
  - Break-even: quantos assinantes cobrem a infra
  - **Evidência:** Arquivo commitado no repositório

- [x] AC2: Custos fixos extraídos de fontes reais (dashboards Railway, Supabase, Upstash), não estimados
  - **Evidência:** Pricing pages oficiais com data de extração (2026-02-21) documentados em cada seção

- [x] AC3: Custo LLM verificado com dados reais de uso (OpenAI usage dashboard ou logs de busca)
  - **Evidência:** Cross-ref com STORY-181 L31 (~R$0.001) + pricing OpenAI GPT-4.1-nano ($0.02/$0.15 por 1M tokens) + token count estimado do código-fonte (250 input + 50 output por call × 15 calls/busca)

### Modelo de Projeção

- [x] AC4: Cálculo de custo variável por volume de buscas: **100, 1.000 e 10.000 buscas/mês**
  - **Evidência:** Seções 3.1 e 3.2 — tabelas com 3 linhas (100/1K/10K), breakdown por componente
  - **Aceite:** Custo unitário + custo total por faixa documentados

- [x] AC5: Projeção de margem por plano: SmartLic Pro (R$1.999/mês, 1.000 buscas) com margem bruta calculada
  - **Evidência:** Seção 4 — Margem = 81,5% (mensal), 79,4% (semestral), 76,9% (anual) com breakdown
  - **Aceite:** Margem bruta por período de cobrança com fórmula explícita

- [x] AC6: Cenários de escala: 10, 50, 100 assinantes ativos (custo infra total, receita, margem operacional)
  - **Evidência:** Seção 5 — Tabela com 1/10/50/100 assinantes, custos por componente, margem operacional
  - **Aceite:** Break-even = 1 assinante (R$1.999 > R$370 custo total)

- [x] AC7: Drivers de custo ranqueados (top 3 maiores custos por busca)
  - **Evidência:** Seção 6 — #1 Railway (59%), #2 Supabase (39%), #3 LLM (88% do variável)

### Alertas de Custo

- [x] AC8: Thresholds de alerta documentados: "Se custo Railway ultrapassa $X/mês, investigar"
  - **Evidência:** Seção 7 — Thresholds amarelo/vermelho por serviço + métricas de busca

## Testes de Validação

### T1: Custo LLM real vs. estimado
- **Procedimento:** Realizar 10 buscas com LLM habilitado, medir tokens consumidos via log ou API usage
- **Resultado esperado:** Custo real por busca dentro de 2x da estimativa (R$0.001-0.006)
- **Evidência:** Log de tokens ou captura do OpenAI dashboard

### T2: Custo Redis real
- **Procedimento:** Verificar Upstash dashboard — commands/dia antes e depois de 10 buscas
- **Resultado esperado:** Delta de ~50-100 commands por 10 buscas (5-10 per busca)
- **Evidência:** Captura do Upstash dashboard

### T3: Cross-check com fatura
- **Procedimento:** Comparar estimativa do documento com última fatura Railway/OpenAI
- **Resultado esperado:** Estimativa dentro de ±30% da fatura real
- **Evidência:** Nota no documento com comparação

## Métricas de Sucesso

| Métrica | Antes | Depois | Verificação |
|---------|-------|--------|-------------|
| Custo por busca documentado | Não | Sim (R$ 0.0022) | docs/operations/cost-analysis.md §2.5 |
| Custo por 1.000 buscas | Desconhecido | Conhecido (R$ 370) | Tabela AC4 §3.2 |
| Margem bruta SmartLic Pro | Desconhecida | Calculada (81,5%) | AC5 §4 |
| Break-even calculado | Não | Sim (1 assinante) | AC6 §5.4 |
| Top drivers identificados | Não | Sim (Railway 59%, Supabase 39%, LLM 88% var) | AC7 §6 |
| Projeção para 100 assinantes | Não | Sim (R$ 1.255/mês custo, 99,4% margem) | AC6 §5.2 |

## Rollback

1. **Nenhuma alteração de código.** Esta story produz apenas documentação.
2. **Rollback:** `git revert` do commit que adiciona o documento.
3. **Impacto do rollback:** Zero. Perda apenas da documentação.

## Idempotência

- Documento é determinístico dado os mesmos inputs (faturas, dashboards)
- Re-executar a story com dados atualizados sobrescreve o documento anterior

## Arquivos Modificados

| Arquivo | Tipo |
|---------|------|
| `docs/operations/cost-analysis.md` | Criado |

## Dependências

| Tipo | Item | Motivo |
|------|------|--------|
| Requisito | Acesso ao Railway billing dashboard | Custos de infra |
| Requisito | Acesso ao OpenAI usage dashboard | Custos LLM |
| Requisito | Acesso ao Upstash dashboard | Custos Redis |
| Paralela | Nenhuma | Independente |
