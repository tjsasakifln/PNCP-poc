# GTM-FIX-030 — Correção de Falhas de Pipeline em Produção

| Campo | Valor |
|-------|-------|
| **Prioridade** | P0 — Busca nacional retorna 0 resultados em 100% dos casos |
| **Severidade** | Crítica — Funcionalidade core completamente quebrada em produção |
| **Estimativa** | 3-5 horas (5 tracks paralelizáveis) |
| **Dependências** | GTM-FIX-029 (timeout chain, commit `e6e2ec9`) |
| **Autor** | @pm (Morgan) |
| **Data** | 2026-02-17 |

---

## Contexto

GTM-FIX-029 recalibrou a cadeia de timeouts internos do pipeline, mas em produção a busca nacional (27 UFs) ainda falha com HTTP 500 após ~120s. Uma busca menor (3 UFs) chega até o stage 4 (avaliação LLM) e morre na mesma barreira. Os dados do PNCP **estão chegando** (logs mostram UFs com 144-749 items fetched), mas o resultado final nunca é entregue ao usuário.

**Evidência de produção (2026-02-17T22:50 UTC):**

```
Fetched 144 items for UF=RR
Fetched 231 items for UF=AC
Fetched 531 items for UF=AM
Fetched 614 items for UF=TO
Fetched 709 items for UF=AL
Fetched 749 items for UF=SE
Fetched 151 items for UF=AP
Fetched 531 items for UF=RO
PNCP 422 for UF=AM mod=4 — "Data Inicial deve ser anterior ou igual à Data Final". Retrying once...
```

**Frontend observou:**
- Busca nacional: stages 1-3 completam, stage 4 (LLM) stall → 500 após ~180s
- Busca 3 UFs: stages 1-3 completam, stage 4 stall → "0 oportunidades" após 72 filtrados por `status_mismatch`

---

## Root Cause Analysis

### BUG 1 — Gunicorn Worker Timeout (P0, FATAL)

**Arquivo:** `backend/Dockerfile` linha 43

```dockerfile
CMD gunicorn main:app -k uvicorn.workers.UvicornWorker --timeout 120
```

O gunicorn mata qualquer worker que não responde em 120s. O pipeline de busca precisa de até 360s (FETCH_TIMEOUT). **Toda busca que demora >120s é silenciosamente abortada pelo gunicorn**, retornando 500 ao frontend.

**Cadeia de timeouts (GTM-FIX-029) vs gunicorn:**
```
Frontend proxy:  480s  ✅
Pipeline:        360s  ✅
Consolidation:   300s  ✅
GUNICORN:        120s  ❌ ← MATA O WORKER AQUI
Per-Source:      180s  (nunca alcançado)
Per-UF:           90s  (nunca alcançado)
```

### BUG 2 — Variáveis de Timeout Ausentes no Railway (P0)

**Ambiente Railway atual:**
- `GUNICORN_TIMEOUT` → **NÃO EXISTE** (usa default do Dockerfile: 120)
- `CONSOLIDATION_TIMEOUT_GLOBAL` → **NÃO EXISTE** (usa default: 300)
- `CONSOLIDATION_TIMEOUT_PER_SOURCE` → **NÃO EXISTE** (usa default: 180)
- `SEARCH_FETCH_TIMEOUT` → **NÃO EXISTE** (usa default: 360)
- `PNCP_TIMEOUT_PER_UF` → **NÃO EXISTE** (usa default: 90)
- `WEB_CONCURRENCY` → **NÃO EXISTE** (usa default: 4 workers)

O GTM-FIX-029 AC11 exigia configurar estas variáveis no Railway mas isso não foi feito.

### BUG 3 — Filtro status_mismatch Rejeitando 100% (P1)

Na busca de 3 UFs, o pipeline fetchou 72 bids mas o filtro `status_mismatch` rejeitou **todos**. GTM-FIX-027 T2 reduziu a janela de status filter de 180→60 dias, o que pode estar filtrando agressivamente demais quando combinado com o período de busca de 180 dias.

**Hipótese:** O filtro verifica se `data_abertura` está dentro de 60 dias do presente, mas bids com `data_abertura` entre 60-180 dias atrás são rejeitados como "status_mismatch" mesmo que ainda estejam abertos.

### BUG 4 — PNCP 422 "Data Inicial deve ser anterior ou igual à Data Final" (P2)

Alguns UF+mod retornam 422 com mensagem de erro de datas. Possíveis causas:
- Timezone mismatch (UTC vs BRT) causando data_inicial > data_final no boundary
- Bug no cálculo de datas para status filter que inverte início/fim

### BUG 5 — UX de Loading Inadequada (P2)

- Progress bar fica presa em 93-94% por minutos sem feedback
- Mensagem "Search not found" aparece durante loading (confuso)
- Estimativa de tempo (~105s) muito abaixo do real (~180s+)
- Nenhum feedback sobre quantos items foram encontrados antes do filtro
- Quando a busca falha, o usuário vê "Erro interno do servidor" sem detalhes acionáveis
- Spinner de "Avaliando oportunidades" não indica se é LLM ou outro processamento
- Botão "Cancelar" aparece tarde demais (só após ~60s)

---

## Acceptance Criteria

### Track 1 — Gunicorn Timeout (P0, Dockerfile + Railway)

- [ ] AC1: `GUNICORN_TIMEOUT` no Dockerfile default alterado de `120` para `600` (10 min, > FETCH_TIMEOUT + margem)
- [ ] AC2: `--graceful-timeout` alterado de `30` para `60` (tempo para cleanup)
- [ ] AC3: `GUNICORN_TIMEOUT` configurável via env var: `--timeout ${GUNICORN_TIMEOUT:-600}`
- [ ] AC4: Variável `GUNICORN_TIMEOUT=600` adicionada no Railway

### Track 2 — Railway Env Vars (P0, DevOps)

- [ ] AC5: `CONSOLIDATION_TIMEOUT_GLOBAL=300` configurado no Railway
- [ ] AC6: `CONSOLIDATION_TIMEOUT_PER_SOURCE=180` configurado no Railway
- [ ] AC7: `SEARCH_FETCH_TIMEOUT=360` configurado no Railway
- [ ] AC8: `PNCP_TIMEOUT_PER_UF=90` configurado no Railway
- [ ] AC9: `WEB_CONCURRENCY=2` configurado no Railway (4 workers × 360s request = possível memory exhaustion, reduzir para 2)
- [ ] AC10: Documentar todas env vars de timeout em `docs/deploy/timeout-config.md`

### Track 3 — Filtro status_mismatch (P1, filter.py + search_pipeline.py)

- [ ] AC11: Investigar e documentar a lógica exata do filtro `status_mismatch` no código atual
- [ ] AC12: Se janela de 60 dias está filtrando bids legítimos, aumentar para 90 ou 120 dias
- [ ] AC13: Adicionar log com contagem de bids rejeitados por `status_mismatch` vs total (para diagnóstico)
- [ ] AC14: Teste unitário validando que bids abertos com `data_abertura` há 90 dias passam o filtro
- [ ] AC15: Teste de integração: busca com 3 UFs deve retornar >0 resultados para setor vestuário

### Track 4 — PNCP 422 Data Validation (P2, pncp_client.py)

- [ ] AC16: Investigar se 422 "Data Inicial > Data Final" é causado por timezone (UTC vs BRT -3h)
- [ ] AC17: Se confirmado, normalizar datas para UTC antes de enviar ao PNCP
- [ ] AC18: Se não confirmado, adicionar guard: `if data_inicial > data_final: swap` com warning log
- [ ] AC19: Teste unitário: data boundary no fuso BRT (23:00-01:00 UTC) não causa inversão

### Track 5 — UX do Loading (P2, frontend)

- [ ] AC20: Remover texto "Search not found" do estágio de loading (é placeholder SSE)
- [ ] AC21: Mostrar contador de items brutos encontrados durante stages 1-2 (ex: "347 licitações encontradas, aplicando filtros...")
- [ ] AC22: Recalibrar estimativa de tempo baseado no número de UFs selecionados (3 UFs ~45s, 27 UFs ~180s)
- [ ] AC23: No stage 4 (LLM), mostrar "Analisando relevância por IA..." com sub-progresso
- [ ] AC24: Na falha 500, mostrar mensagem acionável: "A busca demorou mais que o esperado. Tente com menos estados ou um período menor."
- [ ] AC25: Botão "Cancelar" visível desde o início da busca
- [ ] AC26: Progress bar não deve ficar travada em 93-94% — se stage 4 demora >30s, animar suavemente até 98%

---

## Impacted Files

| Track | Arquivo | Mudança |
|-------|---------|---------|
| T1 | `backend/Dockerfile` | `--timeout 120` → `--timeout ${GUNICORN_TIMEOUT:-600}` |
| T2 | Railway env vars | Configurar 6 variáveis de timeout |
| T3 | `backend/filter.py` ou `backend/search_pipeline.py` | Ajustar janela status_mismatch |
| T3 | `backend/tests/test_filter.py` | Novos testes para status_mismatch |
| T4 | `backend/pncp_client.py` | Guard de inversão de datas, timezone handling |
| T5 | `frontend/app/buscar/page.tsx` | Remover "Search not found", recalibrar estimativas |
| T5 | `frontend/hooks/useSearch.ts` | Recalibrar timeEstimate por UF count |
| T5 | `frontend/components/LoadingProgress.tsx` | Sub-progresso stage 4, smooth animation |

---

## Priorização de Execução

```
T1 (Gunicorn) + T2 (Railway vars) ← DEPLOY PRIMEIRO (resolve 500 imediatamente)
    ↓
T3 (status_mismatch)              ← Resolve "0 resultados" para setor vestuário
    ↓
T4 (422 dates) + T5 (UX)         ← Polish, qualidade de experiência
```

**T1+T2 são 10 minutos de trabalho** (editar 1 linha no Dockerfile + configurar env vars) mas resolvem o bloqueio P0.

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Gunicorn 600s causa requests pendurados | Média | Médio | Monitorar Sentry; FETCH_TIMEOUT (360s) já mata antes |
| 2 workers insuficientes | Baixa | Alto | Monitorar latência; pode subir para 3 se needed |
| status_mismatch fix abre flood de bids irrelevantes | Média | Médio | Manter keyword filter como gate principal |
| 422 date fix não resolve (bug no PNCP) | Alta | Baixo | 422 retry já mitiga; apenas diagnóstico adicional |

---

## Validação em Produção

**Antes do fix (baseline):**
- Busca nacional (27 UFs, vestuário): 500 após ~120s ❌
- Busca 3 UFs (SP, RJ, MG): 0 resultados (72 filtrados por status_mismatch) ❌

**Após T1+T2 (gunicorn + env vars):**
- Busca 3 UFs: deve completar stages 1-5 sem 500 ✅
- Busca nacional: deve completar ou retornar resultados parciais ✅

**Após T3 (status_mismatch):**
- Busca 3 UFs vestuário: deve retornar >0 resultados ✅

**Após T5 (UX):**
- Progress bar não fica travada em 93-94% ✅
- "Search not found" não aparece durante loading ✅
