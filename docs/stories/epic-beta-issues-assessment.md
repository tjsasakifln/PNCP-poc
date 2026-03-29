# Technical Assessment — Beta Issues (Brownfield Discovery)

**Data:** 2026-03-28
**Workflow:** `brownfield-discovery.yaml` (Fases 1-8 consolidadas)
**Agentes:** @architect, @data-engineer, @ux-design-expert, @qa
**Escopo:** Soluções DEFINITIVAS para 15 issues abertas do beta-team

---

## Executive Summary

| Métrica | Valor |
|---------|-------|
| Issues totais abertas | 15 |
| P0 (Blocker) | 1 |
| P1 (Critical) | 1 |
| P2 (Important) | 5 |
| P3 (Minor) | 8 |
| Esforço total estimado | ~24h |
| GTM Readiness atual | NO-GO (P0+P1 abertos) |

---

## ISSUE-029 (P0) — Busca Vestuário retorna 75% irrelevantes

### Sintoma
Setor "Vestuário e Uniformes" com SP+RJ retorna biodescontaminação, diesel, poços artesianos, ambulâncias. "Termos Específicos" com mesmas keywords retorna 100% relevância.

### Root Cause
**Funnel design flaw no LLM zero-match.** Para buscas por setor:
1. `filter_llm.py:79` — quando `setor` está definido, `classify_zero_match_pool()` é invocado para TODOS os bids com 0% keyword density
2. `filter_llm.py:84-92` — pool = complemento dos keyword matches. Para Vestuário em SP+RJ: ~20 keyword matches vs ~480 bids sem nenhuma keyword → pool enorme de lixo
3. `llm_arbiter.py:475` — prompt usa `sorted(config.keywords)[:5]` (ordem alfabética: "agasalho", "avental", "bermuda"...) — keywords genéricas, não discriminativas
4. GPT-4.1-nano com YES/NO binário tem ~15-25% false positive rate → 70-120 falsos positivos que swampam os 20 legítimos
5. "Termos Específicos" funciona porque `setor` é `None` (line 79) → `classify_zero_match_pool()` retorna imediatamente sem invocar LLM

### Solução Definitiva (3 camadas)

**Camada 1 — Pre-filter semântico** (`filter_llm.py:84-92`):
- Adicionar `negative_keywords` por setor em `sectors_data.yaml`
- Antes de enviar ao LLM, rejeitar bids cujo `objetoCompra` contém termos negativos do setor
- Ex. Vestuário: rejeitar se contém "combustível", "diesel", "ambulância", "pavimentação", "software", "obras civis"

**Camada 2 — Prompt mais discriminativo** (`llm_arbiter.py:475`):
- Substituir `sorted(config.keywords)[:5]` por seleção curada dos termos MAIS discriminativos (primários)
- Adicionar `max_contract_value` do setor como reasonableness check no prompt
- Ex: "Contratos de vestuário raramente excedem R$5M"

**Camada 3 — Circuit breaker de aceitação** (`filter_llm.py:260-277`):
- Se LLM aceita >30% do pool, está alucinando
- Demover todos os zero-match accepts para `pending_review` em vez de hard accept
- Métrica: `smartlic_zero_match_acceptance_ratio` counter

### Effort: 4-6h | Files: `filter_llm.py`, `llm_arbiter.py`, `sectors_data.yaml`
### Testes: mock LLM false positives, benchmark 15 setores, regressão recall

---

## ISSUE-033 (P1) — Status filter não afeta resultados

### Sintoma
Filtro "Em Julgamento" e "Encerradas" retornam mesmos 20 itens que "Abertas" (R$319M, mesma ordem).

### Root Cause
**Auto-relaxation silenciosa.** Confirmado em `filter_stage.py:280-373`:
1. Status flui corretamente end-to-end: frontend → `BuscaRequest.status` → `filter_stage.py:37` → `pncp_client.py:1650` (param `situacaoCompra`) → `filter_basic.py:63` (post-fetch filter)
2. PNCP retorna majoritariamente bids "Publicada"/"Divulgada" que inferem para `recebendo_proposta`
3. Quando status != "todos" produz 0 resultados, **ISSUE-025 auto-relaxation** entra:
   - Level 2A (line 308): remove keywords, mantém status → ainda 0
   - Level 2B (line 333-336): **define `status="todos"`** → retorna top 20 por valor
4. Resultado: TODAS as opções de status convergem para `status="todos"` via relaxation

### Solução Definitiva

**Fix 1 — Condicionar relaxation ao tipo de filtro** (`filter_stage.py:285`):
```python
# ANTES:
if (not ctx.custom_terms and ctx.request.setor_id and len(ctx.licitacoes_filtradas) == 0 ...)

# DEPOIS — NÃO relaxar se usuário selecionou status explícito:
user_selected_status = request.status and request.status.value != "todos"
if (not ctx.custom_terms and ctx.request.setor_id
    and len(ctx.licitacoes_filtradas) == 0
    and not user_selected_status ...):
```

**Fix 2 — Retornar distribuição de status** (response metadata):
- Quando 0 resultados com status filtrado, incluir `status_distribution` no response
- Ex: `{"recebendo_proposta": 18, "em_julgamento": 0, "encerrada": 2}`

**Fix 3 — Frontend count badges** (`StatusFilter.tsx`):
- Após busca, mostrar badges com contagem por status: "Abertas (18) | Em Julgamento (0) | Encerradas (2)"
- Quando selecionado retorna 0: "Nenhuma licitação com status 'Em Julgamento' no período. 18 estão 'Abertas'."

### Effort: 3-4h | Files: `filter_stage.py`, `schemas/search.py`, `StatusFilter.tsx`
### Testes: unit test relaxation NÃO override status; integration test distribuição

---

## ISSUE-034 (P2) — Link "Criar alerta" retém keywords antigas

### Sintoma
Ao trocar de "Termos Específicos" para "Buscar por setor", link "Criar alerta" mantém keywords da busca anterior e setor vazio.

### Root Cause
`ResultsFooter.tsx:61` — `termosArray` não é scoped ao `searchMode`. Quando muda de termos para setor, o array de keywords da busca anterior persiste no state e é usado para montar o URL do alerta.

### Solução Definitiva
Limpar `termosArray` quando `searchMode` muda. Na construção do URL do alerta, usar `searchMode` para decidir quais params incluir:
- Se `searchMode === "setor"`: usar `setor_id`, ignorar `keywords`
- Se `searchMode === "termos"`: usar `keywords`, ignorar `setor_id`

### Effort: 0.5h | Files: `ResultsFooter.tsx`

---

## ISSUE-035 (P2) — Texto filtro não reflete status selecionado

### Sintoma
"Mostrando licitações abertas para proposta" aparece mesmo quando "Encerradas" está selecionado.

### Root Cause
`useSearchFilters.ts:557-558` — `dateLabel` ignora o filtro `status`, só checa `modoBusca`. O texto é hardcoded para "abertas para proposta".

### Solução Definitiva
Tornar o label dinâmico baseado no `status` selecionado:
- `recebendo_proposta` → "licitações abertas para proposta"
- `em_julgamento` → "licitações em julgamento"
- `encerrada` → "licitações encerradas"
- `todos` → "licitações"

### Effort: 0.5h | Files: `useSearchFilters.ts`

---

## ISSUE-027 (P2) — Resultados duplicados

### Sintoma
"Resíduos exumações Itaboraí" (000039 vs 000037), "Elevadores Osasco" (000048 vs 000046).

### Root Cause
**Dedup by design para editais diferentes.** `consolidation.py:767-830` usa dedup key `{cnpj}:{numero_edital}:{ano}`. Editais com números diferentes = keys diferentes = não deduplicados. Fuzzy dedup (`consolidation.py:906-993`) requer Jaccard ≥ 0.70 E valores dentro de 5% — lotes diferentes do mesmo órgão têm valores distintos, bloqueando fuzzy match.

Porém: muitos desses "duplicados" são **lotes diferentes da mesma licitação** (legítimos, oportunidades distintas para o licitante).

### Solução Definitiva (2 camadas)

**Camada 1 — Detecção de lotes** (`consolidation.py`):
- Parsear `objetoCompra` para indicadores de lote ("lote 1", "item 1", "grupo 1")
- Se dois bids do mesmo CNPJ têm Jaccard ≥ 0.85 e lotes diferentes → NÃO deduplicar (são legítimos)
- Se mesmo CNPJ, Jaccard ≥ 0.85, sem indicador de lote → relaxar threshold de valor de 5% → 20%

**Camada 2 — Agrupamento visual no frontend** (`SearchResults`):
- Agrupar bids do mesmo CNPJ + objeto similar (Jaccard ≥ 0.80) sob um "card pai"
- Mostrar "2 lotes do mesmo órgão" com expand para ver detalhes de cada lote
- Reduz poluição visual sem perder informação

### Effort: 4h | Files: `consolidation.py`, `SearchResults.tsx`
### Testes: unit test lot detection, regressão cross-source dedup

---

## ISSUE-022 (P2) — Valor total com outliers absurdos

### Sintoma
Valor total R$10 trilhões por dados absurdos (metrô linha 22 = R$10 bi/lote).

### Root Cause (Parcialmente resolvido)
`utils/value_sanitizer.py` JÁ implementa:
- Hard cap R$10B (`VALUE_HARD_CAP = 10_000_000_000.0`) — valores > R$10B são zerados
- TCU IQR outlier detection via `compute_robust_total()` em `pipeline/stages/generate.py:293-311`

**Gaps remanescentes:**
1. **Excel export** (`excel.py:240`) usa `sum()` naive SEM `compute_robust_total()` → inconsistência com o card
2. **Frontend** não exibe informação sobre outliers excluídos
3. Hard cap de R$10B pode ser alto demais para certos setores (vestuário: max R$5M realista)

### Solução Definitiva

**Fix 1** — Usar `compute_robust_total()` no Excel (`excel.py:240`)
**Fix 2** — Adicionar `outlier_count` e `used_sanitized` ao `ResumoLicitacoes` schema
**Fix 3** — Frontend: quando `outlier_count > 0`, mostrar nota: "Valor excl. N outlier(s)"
**Fix 4** — `sectors_data.yaml`: adicionar `max_reasonable_value` por setor para cap setor-específico

### Effort: 2-3h | Files: `excel.py`, `schemas/search.py`, `value_sanitizer.py`, `ResultCard.tsx`

---

## ISSUE-026 (P2) — Resumo IA genérico em modo setor

### Sintoma
Em modo "por setor", resumo diz "serviços de coleta, uniformes e obras" (genérico). "Termos Específicos" diz "uniformes e EPIs" (preciso).

### Root Cause
Modo setor envia bids filtrados ao LLM sem termos específicos de busca. O LLM gera resumo baseado apenas nos `objetoCompra` dos resultados. Se resultados incluem lixo do zero-match (ISSUE-029), resumo reflete esse lixo.

### Solução Definitiva
**Resolvido indiretamente pelo fix da ISSUE-029.** Com menos false positives no pool, o resumo será naturalmente mais preciso. Adicionalmente:
- Passar `setor_name` e `sector_keywords[:10]` como contexto no prompt do LLM summary
- Instruir LLM: "Foque o resumo nos itens mais relevantes para o setor {setor_name}"

### Effort: 1h | Files: `llm.py` (prompt de resumo)

---

## ISSUE-005 (P3) — Inputs signup sem autocomplete

### Root Cause
`SignupForm.tsx:341-352` — campo `confirmPassword` não tem `autoComplete="new-password"`.

### Solução
Adicionar `autoComplete` em todos os 4 inputs: `name` → `"name"`, `email` → `"email"`, `password` → `"new-password"`, `confirmPassword` → `"new-password"`.

### Effort: 0.25h

---

## ISSUE-007 (P3) — Conta/Perfil ~8s para carregar

### Root Cause
Waterfall: redirect check → auth verification → profile API (cold backend). Layout shift: sidebar desaparece durante auth check.

### Solução
- Skeleton loading para sidebar (manter layout estável)
- Fetch profile em paralelo com auth check (não sequencial)
- Considerar SSR com `getServerSideProps` para profile data

### Effort: 2h

---

## ISSUE-009 (P3) — Title tag duplicado /status

### Root Cause
`status/page.tsx` metadata + layout template ambos adicionam "SmartLic".

### Solução
Usar `title: { absolute: "Status do Sistema | SmartLic" }` no metadata do page.

### Effort: 0.25h

---

## ISSUE-010 (P3) — "Fontes de Dados" em /status vazio

### Root Cause
`StatusContent.tsx:162-180` — sem fallback quando `sources` é vazio.

### Solução
Adicionar empty-state: "Informação de fontes indisponível no momento."

### Effort: 0.25h

---

## ISSUE-023 (P3) — Flash estado botão /planos (~3s)

### Root Cause
`PlanProCard.tsx:96-115` — `userStatus` default = "trial" enquanto `planInfo` carrega via SWR (~1-3s).

### Solução
Adicionar loading state ao botão CTA: skeleton/spinner enquanto `planLoading=true`.

### Effort: 0.5h

---

## ISSUE-018 (P3) — Admin dropdown planos duplicados

### Root Cause
`lib/plans.ts` — 4 entries ("smartlic_pro", "consultor_agil", "maquina", "sala_guerra") todas com label "SmartLic Pro" + variações. Legacy plans confundem.

### Solução
Labels distintos: "Consultor Ágil (legacy)", "Máquina (legacy)", "Sala de Guerra (legacy)". Filtrar legacy do dropdown a menos que user já tenha o plano.

### Effort: 1h

---

## ISSUE-019 (P3) — Admin Uptime/Fontes indisponíveis

### Root Cause
`/api/status` endpoint pode não retornar `uptime_pct_30d` e `sources` quando health checks não rodaram.

### Solução
Esconder widgets quando dados indisponíveis (em vez de "Não disponível"). Adicionar retry no fetch.

### Effort: 1.5h

---

## Matriz de Priorização Final

| # | Issue | P | Área | Effort | Dependências | Sprint |
|---|-------|---|------|--------|--------------|--------|
| 1 | ISSUE-029 | P0 | Backend | 4-6h | Nenhuma | Sprint 1 |
| 2 | ISSUE-033 | P1 | Full-stack | 3-4h | Nenhuma | Sprint 1 |
| 3 | ISSUE-035 | P2 | Frontend | 0.5h | Nenhuma | Sprint 1 |
| 4 | ISSUE-034 | P2 | Frontend | 0.5h | Nenhuma | Sprint 1 |
| 5 | ISSUE-022 | P2 | Full-stack | 2-3h | Nenhuma | Sprint 1 |
| 6 | ISSUE-026 | P2 | Backend | 1h | ISSUE-029 | Sprint 1 |
| 7 | ISSUE-027 | P2 | Full-stack | 4h | Nenhuma | Sprint 2 |
| 8 | ISSUE-005 | P3 | Frontend | 0.25h | Nenhuma | Sprint 2 |
| 9 | ISSUE-009 | P3 | Frontend | 0.25h | Nenhuma | Sprint 2 |
| 10 | ISSUE-010 | P3 | Frontend | 0.25h | Nenhuma | Sprint 2 |
| 11 | ISSUE-023 | P3 | Frontend | 0.5h | Nenhuma | Sprint 2 |
| 12 | ISSUE-007 | P3 | Frontend | 2h | Nenhuma | Sprint 2 |
| 13 | ISSUE-018 | P3 | Frontend | 1h | Nenhuma | Sprint 2 |
| 14 | ISSUE-019 | P3 | Full-stack | 1.5h | Nenhuma | Sprint 2 |

**Sprint 1 (GTM Blocker):** ~12h — Issues 029, 033, 034, 035, 022, 026
**Sprint 2 (Polish):** ~10h — Issues 027, 005, 007, 009, 010, 018, 019, 023

---

## Critérios de Sucesso

| Issue | Critério de Aceite |
|-------|-------------------|
| 029 | Busca Vestuário SP+RJ: ≥80% resultados relevantes (vs ~25% atual) |
| 033 | "Encerradas" retorna resultados DIFERENTES de "Abertas" (ou 0 com mensagem) |
| 034 | Link "Criar alerta" sem keywords residuais ao trocar modo |
| 035 | Texto dinâmico: "encerradas" quando Encerradas selecionado |
| 022 | Valor total card = Valor total Excel (ambos com outlier detection) |
| 026 | Resumo menciona setor + keywords relevantes, não "serviços diversos" |
| 027 | Bids do mesmo órgão + objeto similar agrupados visualmente |
