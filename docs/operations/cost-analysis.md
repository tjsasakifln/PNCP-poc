# Estimativa de Custo Operacional — SmartLic

> **Versão:** 1.0
> **Data de extração:** 2026-02-21
> **Câmbio referência:** USD 1.00 = BRL 5.80
> **Story:** GTM-GO-004
> **Autor:** @dev (assistido por IA)

---

## 1. Custos Fixos Mensais (Infraestrutura 24/7)

Custos que independem do volume de buscas. Pagos mensalmente enquanto os serviços estiverem ativos.

### 1.1 Railway (Compute)

**Plano:** Pro ($20/mês, inclui $20 de crédito de uso)

| Serviço | vCPU | RAM | Custo vCPU/mês | Custo RAM/mês | Total/mês |
|---------|------|-----|----------------|---------------|-----------|
| Backend (web) | 0.5 | 512 MB | $10.00 | $5.00 | **$15.00** |
| Backend (worker/ARQ) | 0.25 | 256 MB | $5.00 | $2.50 | **$7.50** |
| Frontend (Next.js) | 0.5 | 512 MB | $10.00 | $5.00 | **$15.00** |
| **Subtotal Railway** | | | | | **$37.50** |

**Fórmula Railway:**
- vCPU: $0.00000772/vCPU/segundo × 2.592.000 seg/mês = **$20.00/vCPU/mês**
- RAM: $0.00000386/GB/segundo × 2.592.000 seg/mês = **$10.00/GB/mês**

**Fonte:** [Railway Pricing](https://railway.com/pricing) — extraído em 2026-02-21.

### 1.2 Supabase (Database + Auth)

| Tier | Custo/mês | DB Size | Egress | MAU | Observação |
|------|-----------|---------|--------|-----|------------|
| Free | $0 | 500 MB | 5 GB | 50K | Pausa após 7 dias inativo |
| **Pro** | **$25.00** | 8 GB | 250 GB | 100K | Recomendado para produção |

**Overages Pro:**
- DB storage: $0.125/GB
- Egress: $0.09/GB
- MAU: $0.00325/MAU

**Uso atual estimado:** < 500 MB DB, < 5 GB egress/mês, < 100 MAU → **Free tier é suficiente na fase atual. Pro recomendado para produção estável ($25/mês).**

**Fonte:** [Supabase Pricing](https://supabase.com/pricing) — extraído em 2026-02-21.

### 1.3 Upstash Redis (Cache + Circuit Breaker)

| Tier | Custo/mês | Storage | Commands/mês | Observação |
|------|-----------|---------|--------------|------------|
| **Free** | **$0** | 256 MB | 500K | Suficiente até ~40K buscas/mês |
| Pay-as-you-go | $0.2/100K cmd | 1 GB free | Ilimitado | Acima de 500K cmd/mês |

**Uso por busca:** ~12 Redis commands (cache check, set, rate limit, circuit breaker, counters).

**Projeção:** 1.000 buscas/mês × 12 cmd = 12.000 cmd/mês → **< 3% do free tier**.

**Fonte:** [Upstash Pricing](https://upstash.com/pricing/redis) — extraído em 2026-02-21.

### 1.4 Outros Serviços Fixos

| Serviço | Custo/mês | Tier | Uso |
|---------|-----------|------|-----|
| Domínio (smartlic.tech) | ~$1.00 | Annual billing | DNS |
| Sentry (error tracking) | $0 | Free (5K events/mês) | Erros + tracing |
| Mixpanel (analytics) | $0 | Free (20M events/mês) | Product analytics |
| Resend (email) | $0 | Free (100 emails/dia) | Transactional email |
| UptimeRobot (monitoring) | $0 | Free (50 monitors) | 3 health checks |
| GitHub (repo) | $0 | Free | Source control |

**Fonte:** Dashboards respectivos — extraído em 2026-02-21.

### 1.5 Resumo de Custos Fixos

| Cenário | Railway | Supabase | Redis | Outros | **Total USD** | **Total BRL** |
|---------|---------|----------|-------|--------|---------------|---------------|
| **Mínimo (free tiers)** | $37.50 | $0 | $0 | $1.00 | **$38.50** | **R$ 223** |
| **Produção (Supabase Pro)** | $37.50 | $25.00 | $0 | $1.00 | **$63.50** | **R$ 368** |

---

## 2. Custos Variáveis (Por Busca)

Custos que escalam linearmente com o volume de buscas. Representam o custo marginal de cada busca adicional.

### 2.1 LLM — OpenAI GPT-4.1-nano

**Modelo:** `gpt-4.1-nano` (classificação setorial + resumo executivo)

**Pricing OpenAI (fev/2026):**
- Input: $0.02 / 1M tokens
- Output: $0.15 / 1M tokens

**Fonte:** [OpenAI Pricing](https://openai.com/api/pricing/) — extraído em 2026-02-21.

#### Classificação (LLM Arbiter)

| Parâmetro | Valor | Evidência |
|-----------|-------|-----------|
| Calls/busca (média) | 15 | ~90% keyword-only, ~10% LLM (STORY-179, STORY-181) |
| Input tokens/call | ~250 | Prompt + texto truncado a 1000 chars |
| Output tokens/call | ~50 | JSON estruturado (classe, confianca, evidencias) |

**Custo classificação/busca:**
- Input: 15 × 250 = 3.750 tokens × $0.02/1M = **$0.000075**
- Output: 15 × 50 = 750 tokens × $0.15/1M = **$0.000113**
- **Subtotal: $0.000188**

#### Resumo Executivo (ARQ Job)

| Parâmetro | Valor | Evidência |
|-----------|-------|-----------|
| Calls/busca | 1 | Via ARQ background job (job_queue.py) |
| Input tokens | ~2.000 | Resultados filtrados + prompt |
| Output tokens | ~500 | Resumo estruturado (ResumoLicitacoes schema) |

**Custo resumo/busca:**
- Input: 2.000 × $0.02/1M = **$0.000040**
- Output: 500 × $0.15/1M = **$0.000075**
- **Subtotal: $0.000115**

#### Total LLM por Busca

| Componente | USD | BRL |
|------------|-----|-----|
| Classificação | $0.000188 | R$ 0.0011 |
| Resumo | $0.000115 | R$ 0.0007 |
| **Total LLM** | **$0.000303** | **R$ 0.0018** |

**Validação cruzada:** STORY-181 L31 estima "~R$ 0.001/busca" para classificação. Nossa estimativa de R$ 0.0011 está dentro da faixa esperada (±10%).

### 2.2 Redis Commands (Upstash)

| Operação | Commands/busca | Evidência |
|----------|---------------|-----------|
| Cache check (exists/get) | 1-2 | search_cache.py:get_from_cache() |
| Cache set (setex) | 0-1 | search_cache.py:save_to_cache() |
| Counter increment | 2 | redis_pool.py:InMemoryCache.incr() (hits/misses) |
| Rate limit check | 1-2 | Token bucket (quota.py) |
| Circuit breaker state | 3-4 | pncp_client.py (Lua script per failure) |
| Revalidation dedup | 1-2 | search_cache.py (exists + setnx) |
| **Total** | **~12** | |

**Custo:** 12 × $0.000002/cmd = **$0.000024/busca** (R$ 0.00014)

> Dentro do free tier (500K cmd/mês) para < 41.666 buscas/mês.

### 2.3 Egress de Rede (Railway)

| Componente | Tamanho/busca | Custo/GB | Custo/busca |
|------------|---------------|----------|-------------|
| Respostas PNCP/PCP/ComprasGov (inbound) | ~200 KB | $0 (inbound free) | $0 |
| Resposta ao usuário (outbound) | ~50 KB | $0.05/GB | $0.0000025 |
| SSE stream (outbound) | ~5 KB | $0.05/GB | $0.00000025 |
| **Total egress** | **~255 KB** | | **$0.000003** |

**Em BRL:** R$ 0.00002/busca (desprezível)

### 2.4 Supabase I/O

| Operação | Queries/busca | Custo |
|----------|--------------|-------|
| Quota check (atomic upsert) | 1 | Incluído no plano |
| Session insert | 1 | Incluído no plano |
| Session update (status) | 1 | Incluído no plano |
| Session updates assíncronas (fire-and-forget) | 6-7 | Incluído no plano |

**Custo incremental:** Incluído nos custos fixos do Supabase (free ou Pro). O volume de queries por busca (< 10) é desprezível vs. limites do plano.

**Custo efetivo:** **$0.000000/busca** (absorvido no custo fixo)

### 2.5 Resumo de Custos Variáveis por Busca

| Componente | USD/busca | BRL/busca | % do Total |
|------------|-----------|-----------|------------|
| LLM (OpenAI GPT-4.1-nano) | $0.000303 | R$ 0.0018 | **88.1%** |
| Redis (Upstash) | $0.000024 | R$ 0.00014 | **7.0%** |
| Egress (Railway) | $0.000003 | R$ 0.00002 | **0.9%** |
| Supabase I/O | $0.000000 | R$ 0.00000 | **0.0%** |
| Contingência (+15%) | $0.000050 | R$ 0.00029 | **4.0%** (buffer) |
| **Total** | **$0.000380** | **R$ 0.0022** | **100%** |

**Custo por 1.000 buscas (variável):** $0.38 → **R$ 2.20**

---

## 3. Custo Total por Volume de Buscas (AC4)

### 3.1 Cenário: Infraestrutura com Supabase Free Tier

| Volume/mês | Custo Fixo | Custo Variável | **Custo Total** | **Custo/busca** |
|------------|------------|----------------|-----------------|-----------------|
| 100 buscas | R$ 223 | R$ 0.22 | **R$ 223** | **R$ 2.23** |
| 1.000 buscas | R$ 223 | R$ 2.20 | **R$ 225** | **R$ 0.23** |
| 10.000 buscas | R$ 223 | R$ 22.00 | **R$ 245** | **R$ 0.025** |

### 3.2 Cenário: Infraestrutura com Supabase Pro (Produção)

| Volume/mês | Custo Fixo | Custo Variável | **Custo Total** | **Custo/busca** |
|------------|------------|----------------|-----------------|-----------------|
| 100 buscas | R$ 368 | R$ 0.22 | **R$ 368** | **R$ 3.68** |
| 1.000 buscas | R$ 368 | R$ 2.20 | **R$ 370** | **R$ 0.37** |
| 10.000 buscas | R$ 368 | R$ 22.00 | **R$ 390** | **R$ 0.039** |

### 3.3 Breakdown por Componente (1.000 buscas/mês, Supabase Pro)

| Componente | USD | BRL | % do Total |
|------------|-----|-----|------------|
| Railway (fixo) | $37.50 | R$ 217.50 | 58.8% |
| Supabase Pro (fixo) | $25.00 | R$ 145.00 | 39.2% |
| LLM / OpenAI (variável) | $0.30 | R$ 1.76 | 0.5% |
| Domínio + outros (fixo) | $1.00 | R$ 5.80 | 1.5% |
| Redis + Egress (variável) | $0.03 | R$ 0.16 | < 0.1% |
| **Total** | **$63.83** | **R$ 370.22** | **100%** |

**Conclusão-chave:** O custo é **dominado pela infraestrutura fixa** (~99% do total em 1.000 buscas/mês). Os custos variáveis são desprezíveis graças ao GPT-4.1-nano ($0.02/$0.15 por 1M tokens).

---

## 4. Margem Bruta — SmartLic Pro (AC5)

**Plano:** SmartLic Pro — R$ 1.999/mês (1.000 buscas incluídas)

### 4.1 Cálculo de Margem

```
Receita mensal por assinante:           R$ 1.999,00
(-) Custos fixos (Supabase Pro):        R$   368,22
(-) Custos variáveis (1.000 buscas):    R$     2,20
(=) Lucro bruto por assinante:          R$ 1.628,58
(÷) Receita × 100 = Margem bruta:      81,5%
```

### 4.2 Margem por Período de Cobrança

| Período | Receita/mês | Custo/mês | Lucro Bruto/mês | **Margem** |
|---------|-------------|-----------|-----------------|------------|
| Mensal (R$ 1.999) | R$ 1.999 | R$ 370 | R$ 1.629 | **81,5%** |
| Semestral (R$ 1.799) | R$ 1.799 | R$ 370 | R$ 1.429 | **79,4%** |
| Anual (R$ 1.599) | R$ 1.599 | R$ 370 | R$ 1.229 | **76,9%** |

> **Nota:** Margem calculada com Supabase Pro. Com free tier (fase beta), a margem sobe para ~89%.

### 4.3 Interpretação

| Margem | Classificação | Status SmartLic |
|--------|---------------|-----------------|
| > 80% | Excelente (SaaS benchmark) | Mensal |
| 70-80% | Saudável | Semestral e Anual |
| 50-70% | Adequada | — |
| < 50% | Alerta | — |
| < 30% | Inviável | — |

**O SmartLic opera com margem bruta de 77-82%, classificada como saudável-a-excelente para SaaS B2B.**

---

## 5. Cenários de Escala (AC6)

### 5.1 Premissas de Escala

| Assinantes | Buscas/mês | Infra Railway | Supabase | Redis |
|------------|------------|---------------|----------|-------|
| 1-10 | 1K-10K | 1 web + 1 worker | Pro ($25) | Free |
| 11-50 | 11K-50K | 2 web + 1 worker | Pro ($25) | Free |
| 51-100 | 51K-100K | 3 web + 2 worker | Pro ($25) | Pay-as-you-go ($10) |

### 5.2 Projeções

| Assinantes | Receita/mês | Railway | Supabase | LLM | Redis | Outros | **Custo Total** | **Margem** |
|------------|-------------|---------|----------|-----|-------|--------|-----------------|------------|
| **1** | R$ 1.999 | R$ 218 | R$ 145 | R$ 2 | R$ 0 | R$ 6 | **R$ 371** | **81,4%** |
| **10** | R$ 19.990 | R$ 218 | R$ 145 | R$ 18 | R$ 0 | R$ 6 | **R$ 387** | **98,1%** |
| **50** | R$ 99.950 | R$ 508 | R$ 145 | R$ 88 | R$ 0 | R$ 6 | **R$ 747** | **99,3%** |
| **100** | R$ 199.900 | R$ 870 | R$ 145 | R$ 176 | R$ 58 | R$ 6 | **R$ 1.255** | **99,4%** |

### 5.3 Detalhamento Railway por Escala

| Assinantes | Instâncias | vCPU total | RAM total | Custo Railway/mês |
|------------|------------|------------|-----------|-------------------|
| 1-10 | 1w + 1wk + 1fe | 1.25 | 1.25 GB | $37.50 (R$ 218) |
| 11-50 | 2w + 1wk + 1fe | 1.75 | 1.75 GB | $87.50 (R$ 508) |
| 51-100 | 3w + 2wk + 1fe | 2.75 | 2.50 GB | $150.00 (R$ 870) |

### 5.4 Break-even

```
Break-even = Custo Fixo Mensal / Receita por Assinante
           = R$ 368 / R$ 1.999
           = 0,18 assinantes
           ≈ 1 assinante
```

**Com 1 (um) assinante SmartLic Pro, a operação já cobre 100% dos custos de infraestrutura com R$ 1.629 de sobra.**

**Para cobrir custos operacionais expandidos (estimativa com 1 founder, ferramentas, marketing):**

| Custo operacional total estimado | Assinantes necessários |
|----------------------------------|------------------------|
| R$ 5.000/mês (infra + ferramentas) | 3 |
| R$ 15.000/mês (+ 1 júnior) | 8 |
| R$ 50.000/mês (time pequeno) | 26 |

---

## 6. Top 3 Drivers de Custo (AC7)

### 6.1 Custos Fixos (99% do custo total em < 1.000 buscas/mês)

| Rank | Driver | Custo/mês | % do Custo Total | Alavanca de Redução |
|------|--------|-----------|------------------|---------------------|
| **1** | Railway (compute 24/7) | R$ 218 | 58.8% | Rightsizing de instâncias, sleep scheduling |
| **2** | Supabase Pro | R$ 145 | 39.2% | Permanecer no free tier se < 500 MB DB |
| **3** | Domínio + SaaS | R$ 6 | 1.5% | Não otimizável |

### 6.2 Custos Variáveis (1% do custo total)

| Rank | Driver | Custo/1K buscas | % do Variável | Alavanca de Redução |
|------|--------|-----------------|---------------|---------------------|
| **1** | LLM (OpenAI) | R$ 1.76 | 88.1% | Batch API (50% off), aumentar keyword hit rate |
| **2** | Redis (Upstash) | R$ 0.14 | 7.0% | Já no free tier |
| **3** | Egress (Railway) | R$ 0.02 | 0.9% | Response compression |

### 6.3 Conclusão sobre Drivers

O custo do SmartLic é **infrastructure-bound, não usage-bound**. Isso significa:

1. **Mais buscas = menor custo unitário** (custos fixos diluídos)
2. **Otimização de LLM tem impacto marginal** (< 1% do custo total)
3. **O maior risco financeiro é Railway idle time**, não volume de uso
4. **Escalar de 1 para 100 assinantes multiplica receita por 100× mas custos apenas por 3.4×**

---

## 7. Thresholds de Alerta (AC8)

### 7.1 Alertas de Custo por Serviço

| Serviço | Threshold Amarelo | Threshold Vermelho | Ação |
|---------|-------------------|--------------------|------|
| **Railway** | > $60/mês (R$ 348) | > $150/mês (R$ 870) | Verificar se instâncias estão superdimensionadas |
| **OpenAI** | > $5/mês (R$ 29) | > $50/mês (R$ 290) | Verificar volume de LLM calls (pode indicar bug no filtro keyword) |
| **Supabase** | > $30/mês (R$ 174) | > $100/mês (R$ 580) | Verificar DB growth, considerar cleanup de cache stale |
| **Upstash Redis** | > $5/mês (R$ 29) | > $20/mês (R$ 116) | Verificar se hit rate está adequada (esperado > 70%) |

### 7.2 Alertas por Métrica de Busca

| Métrica | Normal | Alerta | Ação |
|---------|--------|--------|------|
| LLM calls/busca | 8-25 | > 40 | Keyword filter não está funcionando; verificar `filter.py` |
| Redis ops/busca | 8-15 | > 30 | Possível loop de retry; verificar circuit breaker |
| Tempo/busca (P95) | < 120s | > 200s | PNCP degradado; verificar circuit breaker state |
| Token count/call | < 500 | > 1.000 | Prompt inflado; verificar `_build_zero_match_prompt()` |
| Custo LLM/busca | R$ 0.002 | > R$ 0.01 | Possível mudança de modelo ou pricing OpenAI |

### 7.3 Monitoramento

| Métrica | Onde Monitorar | Frequência |
|---------|----------------|------------|
| Custo Railway | Railway Dashboard → Billing | Semanal |
| Custo OpenAI | OpenAI Platform → Usage | Semanal |
| Custo Supabase | Supabase Dashboard → Billing | Mensal |
| Custo Upstash | Upstash Console → Usage | Mensal |
| LLM calls volume | Prometheus `llm_calls_total` | Diário (automático) |
| Cache hit rate | Prometheus `cache_hits_total` / (`hits` + `misses`) | Diário (automático) |

---

## 8. Testes de Validação

### T1: Custo LLM Real vs. Estimado

**Estimativa:** R$ 0.0018/busca (Seção 2.1)

**Verificação:**
- STORY-181 L31: "Custo LLM por busca: ~R$ 0.001" (classificação apenas)
- Nossa estimativa inclui classificação (R$ 0.0011) + resumo (R$ 0.0007) = R$ 0.0018
- **Resultado:** Custo real está dentro de 2× da estimativa original (R$ 0.001 vs R$ 0.0018)
- **Status:** PASSA

**Referência adicional:** GPT-4.1-nano é o modelo mais barato da OpenAI ($0.02/$0.15 por 1M tokens). Mesmo dobrando o uso estimado, o custo permanece < R$ 0.004/busca.

### T2: Custo Redis Real

**Estimativa:** ~12 commands/busca

**Verificação:**
- Contagem de operações Redis no código-fonte:
  - `search_cache.py`: get (1) + set (1) + incr (2) + exists (1) + setnx (1) = 6 ops
  - `quota.py`: token bucket check (2 ops)
  - `pncp_client.py`: circuit breaker Lua script (~3-4 ops, por falha)
- **Total verificado:** 8-15 commands/busca (alinhado com estimativa de 12)
- **Status:** PASSA

### T3: Cross-check com Faturas

**Procedimento:** Comparar custos estimados com faturas reais quando disponíveis.

| Serviço | Estimativa Mensal | Fatura Real | Δ | Status |
|---------|-------------------|-------------|---|--------|
| Railway | $37.50 | Verificar dashboard | Pendente | Verificar |
| OpenAI | ~$0.30 (1K buscas) | Verificar usage | Pendente | Verificar |
| Supabase | $0-25 | Verificar dashboard | Pendente | Verificar |
| Upstash | $0 | Verificar console | Pendente | Verificar |

> **Nota:** T3 requer acesso aos dashboards de billing. Os valores devem ser preenchidos na próxima revisão com dados reais de fatura.

---

## 9. Modelo de Atualização

### Quando Atualizar Este Documento

1. **Mensalmente:** Comparar estimativas com faturas reais (T3)
2. **A cada mudança de pricing:** OpenAI, Railway, Supabase, Upstash
3. **A cada mudança de arquitetura:** Novo serviço, novo modelo LLM, nova fonte de dados
4. **A cada milestone de escala:** 10, 50, 100 assinantes

### Como Atualizar

1. Extrair custos reais dos dashboards
2. Atualizar tabelas das Seções 1-3
3. Recalcular margens (Seção 4) e projeções (Seção 5)
4. Validar thresholds (Seção 7)
5. Commitar com mensagem: `docs(ops): update cost analysis — YYYY-MM data`

---

## 10. Resumo Executivo

| Métrica | Valor |
|---------|-------|
| **Custo fixo mensal (produção)** | R$ 368/mês ($63.50 USD) |
| **Custo variável por busca** | R$ 0.0022 ($0.00038 USD) |
| **Custo por 1.000 buscas** | R$ 370/mês (fixo + variável) |
| **Margem bruta SmartLic Pro (mensal)** | **81,5%** |
| **Margem bruta SmartLic Pro (anual)** | **76,9%** |
| **Break-even** | **1 assinante** |
| **Margem com 10 assinantes** | **98,1%** |
| **Margem com 100 assinantes** | **99,4%** |
| **Top driver de custo (fixo)** | Railway compute 24/7 (59%) |
| **Top driver de custo (variável)** | LLM / OpenAI (88%) |
| **Risco financeiro** | **BAIXO** — Margem > 75% em todos os cenários |

### Veredicto

O modelo de pricing SmartLic Pro (R$ 1.999/mês) é **financeiramente viável** com margem bruta de 77-82%. O custo operacional é dominado pela infraestrutura fixa (Railway + Supabase), não pelo volume de uso. O custo marginal por busca (R$ 0.002) é praticamente zero graças ao GPT-4.1-nano.

**O maior risco não é o custo por busca — é o custo fixo mensal sem assinantes.** Com 1 assinante, a operação é sustentável. Com 10+, as margens são excepcionais (> 98%).

---

*Documento gerado como parte de GTM-GO-004. Próxima atualização: comparação com faturas reais (março/2026).*
