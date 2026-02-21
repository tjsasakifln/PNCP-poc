# GTM-GO-004: Estimativa de Custo Operacional por 1.000 Buscas

## Epic
GTM Readiness — Redução de Risco Financeiro

## Sprint
Sprint GO: Eliminação de Bloqueadores GTM

## Prioridade
P2 — Risco financeiro (visibilidade)

## Estimativa
3h

## Status: PENDING

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

- [ ] AC1: `docs/operations/cost-analysis.md` criado com:
  - Tabela de custos fixos mensais (Railway, Supabase, Redis, domínio)
  - Tabela de custos variáveis por busca (LLM, egress, Redis commands)
  - Custo total estimado por 1.000 buscas
  - Break-even: quantos assinantes cobrem a infra
  - **Evidência:** Arquivo commitado no repositório

- [ ] AC2: Custos fixos extraídos de fontes reais (dashboards Railway, Supabase, Upstash), não estimados
  - **Evidência:** Screenshots ou valores copiados com data de extração

- [ ] AC3: Custo LLM verificado com dados reais de uso (OpenAI usage dashboard ou logs de busca)
  - **Evidência:** Última fatura OpenAI ou token count de N buscas reais

### Modelo de Projeção

- [ ] AC4: Cálculo de custo variável por volume de buscas: **100, 1.000 e 10.000 buscas/mês**
  - **Evidência:** Tabela com 3 linhas (100/1000/10k), colunas: LLM, Redis, Supabase I/O, Railway compute, total
  - **Aceite:** Custo por busca individual e custo total por faixa

- [ ] AC5: Projeção de margem por plano: SmartLic Pro (R$1.999/mês, 1.000 buscas) com margem bruta calculada
  - **Evidência:** `Margem = (Receita - Custo fixo - Custo variável) / Receita × 100`
  - **Aceite:** Margem bruta expressa em percentual com breakdown

- [ ] AC6: Cenários de escala: 10, 50, 100 assinantes ativos (custo infra total, receita, margem operacional)
  - **Evidência:** Tabela no documento com cálculos explícitos
  - **Aceite:** Break-even identificado (quantos assinantes cobrem infraestrutura)

- [ ] AC7: Drivers de custo ranqueados (top 3 maiores custos por busca)
  - **Evidência:** Lista ordenada com percentual do custo total

### Alertas de Custo

- [ ] AC8: Thresholds de alerta documentados: "Se custo Railway ultrapassa $X/mês, investigar"
  - **Evidência:** Seção no documento com valores definidos

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
| Custo por busca documentado | Não | Sim (R$ X.XX) | docs/operations/cost-analysis.md |
| Custo por 1.000 buscas | Desconhecido | Conhecido (R$ X) | Tabela AC4 |
| Margem bruta SmartLic Pro | Desconhecida | Calculada (X%) | AC5 |
| Break-even calculado | Não | Sim (N assinantes) | AC6 |
| Top drivers identificados | Não | Sim (top 3) | AC7 |
| Projeção para 100 assinantes | Não | Sim (R$ X/mês) | AC6 |

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
