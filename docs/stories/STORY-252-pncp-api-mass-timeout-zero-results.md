# STORY-252: Zero Results em Produção — Multi-Source Activation & PNCP Resilience

## Metadata
| Field | Value |
|-------|-------|
| **ID** | STORY-252 |
| **Priority** | P0 (Production broken) |
| **Sprint** | Sprint 1 |
| **Estimate** | 13h |
| **Depends on** | Nenhuma |
| **Blocks** | Toda busca em produção |

## Contexto & Root Cause Analysis

Busca por setor "Alimentos e Merenda" em produção retornou **zero resultados** em 27 estados. A análise dos logs Railway (2026-02-14T17:11–17:13) revelou:

```
UF=MT timed out after 90s — skipping
UF=MS timed out after 90s — skipping
... (todas as 27 UFs)
Parallel fetch complete: 0 items from 27 UFs in 90.02s (0 errors)
```

### Root Cause 1: Single Point of Failure — PNCP como Fonte Única (P0)

O sistema em produção opera com `ENABLE_MULTI_SOURCE=false` (default). **Toda a busca depende exclusivamente do PNCP.** Se o PNCP não responde, o produto inteiro para.

**O absurdo:** O backend JÁ POSSUI infraestrutura multi-source pronta:
- `backend/clients/compras_gov_client.py` — ComprasGov (federal, **sem auth, gratuito**)
- `backend/clients/portal_compras_client.py` — Portal de Compras Públicas
- `backend/consolidation.py` — Orquestração paralela com dedup
- `backend/source_config/sources.py` — 6 fontes configuradas, 4 habilitadas por default

Tudo isso está **desativado em produção** porque `ENABLE_MULTI_SOURCE` não foi setado. Um `railway variables set ENABLE_MULTI_SOURCE=true` pode ser a mitigação imediata.

### Root Cause 2: Timeout Architecture Frágil (P0)

O timeout per-UF de 90s é **global** — cobre TODAS as modalidades (4,5,6,7) e todas as páginas sequencialmente. Se a modalidade 4 trava na primeira página, o UF inteiro é descartado sem tentar modalidades 5,6,7.

Não há circuit breaker explícito: se o PNCP está lento para UF=AC (primeira UF), o sistema ainda tenta todas as outras 26 UFs com o mesmo timeout, desperdiçando até 90s × 27 = 40+ minutos de tempo de rede.

### Root Cause 3: Error Opacity (P1)

O response da API não distingue entre:
- "PNCP retornou 0 itens" (setor sem licitações — improvável mas possível)
- "PNCP deu timeout em 27/27 UFs" (API fora do ar)
- "PNCP retornou 100 itens, todos filtrados" (filtros muito restritivos)

O usuário vê "0 resultados" em todos os casos. Impossível diagnosticar sem ler logs.

### Root Cause 4: Endpoint `/setores` 404 (P1)

```
GET /v1/setores -> 404 (1ms)  (repetido 3x)
```

O frontend proxy chama `/api/setores` → backend `/v1/setores`, mas a rota pode ter conflito de prefixo. Frontend SEMPRE usa fallback hardcoded.

### Problema Secundário: JWT Token Expired (P2) → STORY-253

```
JWT token expired (múltiplas ocorrências)
GET /v1/api/messages/unread-count -> 401
```

**Extraído para STORY-253** — não é causa raiz do zero-results e não deve poluir esta story P0.

## Evidência

| Campo | Valor |
|-------|-------|
| **Timestamp** | 2026-02-14T17:11:48 — 2026-02-14T17:13:18 (90s) |
| **Request ID** | afbdba36-71a0-45a3-b673-bf5f2b03bf3e |
| **Setor** | alimentos (reconhecido como "Alimentos e Merenda", 85 keywords) |
| **UFs** | 27 (todas) |
| **Resultado** | 0 raw bids, 0 filtered, 27/27 UFs timeout |
| **Multi-source** | DESATIVADO (`ENABLE_MULTI_SOURCE=false`) |
| **Erro adicional** | `UF=AP, modalidade=4: API returned non-retryable status 422` |

## Impacto

- **Busca completamente inoperante** — produto não funciona
- Afeta TODOS os setores, não apenas alimentos
- Usuário espera ~90s e recebe zero resultados sem explicação
- **Fontes alternativas já implementadas estão desligadas**
- Zero visibilidade sobre saúde das fontes de dados

---

## Acceptance Criteria

### Track 1: IMMEDIATE MITIGATION — Ativar Multi-Source (1h) ⚡

Ação imediata para restaurar funcionalidade em produção. Não requer mudança de código.

- [ ] **AC1:** `ENABLE_MULTI_SOURCE=true` configurado nas env vars do Railway.
- [ ] **AC2:** `ENABLE_SOURCE_COMPRAS_GOV=true` confirmado (fallback gratuito, sem API key).
- [ ] **AC3:** Busca em produção retorna resultados de pelo menos 1 fonte quando PNCP está indisponível.
- [ ] **AC4:** Deduplicação funcional: mesmo item de PNCP + ComprasGov aparece apenas 1x no resultado.
- [ ] **AC5:** Teste manual: busca "alimentos" retorna >0 resultados em produção após ativação.

**Validação:** `railway variables set ENABLE_MULTI_SOURCE=true` → busca em produção → resultados > 0.

### Track 2: PNCP Client Hardening (3h) 🛡️

Tornar o client PNCP resiliente a instabilidades sem derrubar a busca inteira.

- [ ] **AC6:** Timeout per-MODALIDADE de 15s (configurável via `PNCP_TIMEOUT_PER_MODALITY`). Se modalidade 4 trava, modalidades 5,6,7 ainda executam independentemente.
- [ ] **AC7:** Timeout per-UF reduzido de 90s para 30s. Com timeout per-modalidade de 15s e 4 modalidades, 30s é suficiente para execução paralela.
- [ ] **AC8:** Circuit breaker explícito: após 5 timeouts consecutivos (qualquer combinação UF+modalidade), marcar PNCP como `degraded` por 5 minutos. Durante degradação, skip PNCP e usar fontes alternativas.
- [ ] **AC9:** Retry on timeout: 1 retry com 3s de backoff antes de desistir de uma modalidade. Hoje é skip direto (zero retries em timeout).
- [ ] **AC10:** PNCP health canary: antes de lançar busca completa (27 UFs × 4 modalidades), testar 1 request leve (`SP`, modalidade 6, 1 página). Se falha em <5s, pular PNCP inteiro e ir direto para fontes alternativas. Economia: evita 90s de espera inútil.
- [ ] **AC11:** Se PNCP health canary falha, log `WARNING: PNCP health check failed — skipping PNCP for this search, using alternative sources`.

**Testes unitários obrigatórios:**
- Test: timeout per-modalidade não cancela outras modalidades
- Test: circuit breaker ativa após N timeouts
- Test: health canary failure → PNCP skipped
- Test: retry acontece 1x antes de skip

### Track 3: MULTI-SOURCE ORCHESTRATION & FAILOVER (3h) 🔄

Garantir que a infraestrutura multi-source existente funcione como safety net robusta.

- [ ] **AC12:** Source health registry: cada fonte mantém status (`healthy` | `degraded` | `down`) com TTL de 5 minutos. Status persiste entre requests (in-memory, sem Redis).
- [ ] **AC13:** Failover automático: se PNCP está `degraded`/`down`, aumentar `timeout_per_source` das alternativas de 25s para 40s para dar mais tempo às fontes secundárias.
- [ ] **AC14:** Modo degradado: se ≥1 fonte retorna dados, retornar resultados parciais com metadata. Se 0 fontes retornam dados, retornar erro explícito (não "0 resultados").
- [ ] **AC15:** ComprasGov sempre habilitado como minimum fallback — mesmo se `ENABLE_SOURCE_COMPRAS_GOV=false` no env, se TODAS as outras fontes falharem, tentar ComprasGov como last resort (free, no auth, no key needed).
- [ ] **AC16:** Response do `/buscar` inclui campo `sources_status: Array<{source: string, status: "ok"|"timeout"|"error"|"skipped", records: number, duration_ms: number}>`.
- [ ] **AC17:** Consolidation timeout global aumentado de 60s para 90s quando PNCP está `degraded` (dar tempo para alternativas compensarem).

**Testes unitários obrigatórios:**
- Test: health registry persiste status entre chamadas
- Test: failover aumenta timeout de alternativas
- Test: ComprasGov como last resort funciona
- Test: ConsolidationResult inclui source_results detalhado

### Track 4: ERROR TRANSPARENCY & UX (2h) 🎯

Nunca mais mostrar "0 resultados" quando a causa real é falha de API.

- [ ] **AC18:** `BuscaResponse` inclui campo `is_partial: bool` — `true` quando nem todas as fontes responderam.
- [ ] **AC19:** `BuscaResponse` inclui campo `data_sources: Array<{source, status, records}>` para o frontend consumir.
- [ ] **AC20:** `BuscaResponse` inclui campo `degradation_reason: Optional[str]` — ex: "PNCP indisponível, resultados de fontes alternativas".
- [ ] **AC21:** Frontend mostra banner amarelo "⚠ Resultados parciais — algumas fontes não responderam" quando `is_partial=true` e `total_filtrado > 0`.
- [ ] **AC22:** Frontend mostra tela de erro vermelha "Nenhuma fonte de dados respondeu. O PNCP e fontes alternativas estão indisponíveis. Tente novamente em alguns minutos." quando `total_filtrado=0` E `is_partial=true`.
- [ ] **AC23:** Frontend NUNCA mostra "Nenhum resultado encontrado" (mensagem de zero legítimo) quando a causa real é falha de API. Distinção via `is_partial` + `total_raw`.

**Matriz de cenários:**

| `total_raw` | `total_filtrado` | `is_partial` | UX |
|-------------|------------------|--------------|----|
| >0 | >0 | false | Resultados normais |
| >0 | >0 | true | Banner amarelo "resultados parciais" + resultados |
| >0 | 0 | false | "Nenhum resultado após filtros" (legítimo) |
| >0 | 0 | true | "Resultados parciais, nenhum passou nos filtros" |
| 0 | 0 | false | "Nenhuma licitação encontrada para este setor" |
| 0 | 0 | true | **ERRO**: "Fontes indisponíveis, tente novamente" |

### Track 5: ENDPOINT `/setores` FIX (1h) 🔧

- [ ] **AC24:** Endpoint `/setores` retorna 200 com lista completa de setores em produção. Diagnosticar se é conflito de prefix `/v1/` vs root mount.
- [ ] **AC25:** Frontend carrega setores da API em produção (verificar via Network tab, não mais fallback).

### Track 6: OBSERVABILITY (2h) 📊

- [ ] **AC26:** Log estruturado por busca: `{search_id, sources_attempted: [], sources_responded: [], sources_timed_out: [], total_raw_per_source: {}, elapsed_ms}`.
- [ ] **AC27:** Endpoint `/health` inclui status de cada fonte de dados (último check, latência média, taxa de sucesso nas últimas 10 requests).
- [ ] **AC28:** Eventos de degradação logados com severity `WARNING`: `"Source PNCP degraded: 5 consecutive timeouts, will skip for 300s"`.

---

## Estratégia de Redução de Dependência do PNCP

### Situação Atual (Pré-STORY-252)

```
[PNCP] ──── 100% ────→ [SmartLic] → Usuário
                         (single point of failure)
```

### Meta Pós-STORY-252

```
[PNCP]       ──┐
[ComprasGov]  ──┼──→ [Consolidation] → [SmartLic] → Usuário
[Portal]      ──┤    (dedup, merge,     (partial results OK)
[Licitar]     ──┘     health-aware)
```

### Fontes Disponíveis — Análise Comparativa

| Fonte | Auth | Rate Limit | Cobertura | Status no Codebase | Ação |
|-------|------|------------|-----------|-------------------|------|
| **PNCP** | Nenhuma | ~10 req/s (429s) | Federal+Estadual+Municipal | ✅ Implementado, ativo | Manter como primário |
| **ComprasGov** | Nenhuma | ~2 req/s | Federal apenas | ✅ Implementado, **INATIVO** | **ATIVAR AGORA** |
| **Portal de Compras** | API key | ~6.7 req/s | Municipal+Estadual | ✅ Implementado, **INATIVO** | Ativar se API key disponível |
| **Licitar Digital** | API key | ~5 req/s | Municipal+Estadual | ✅ Implementado, **INATIVO** | Ativar se API key disponível |
| **Portal Transparência** | API key gratuita | 90/min (dia) | Federal | ❌ Não implementado | STORY futura |
| **Querido Diário** | Nenhuma | ~60/min | Municipal (parcial) | ❌ Não implementado | STORY futura |
| **BLL Compras** | API key | ~5 req/s | Municipal+Estadual | ✅ Config existe, disabled | Avaliar |
| **BNC** | API secret | ~5 req/s | Municipal+Estadual | ✅ Config existe, disabled | Avaliar |

### Fontes Prioritárias para Futuras Stories

1. **Portal da Transparência** (P2, ~5h) — API key gratuita via cadastro, 90 req/min, dados federais complementares com informações de pagamento e sanções. Excelente para enriquecimento.
2. **Querido Diário** (P3, ~8h) — API gratuita sem auth, diários oficiais municipais. Requer text parsing/NLP para extrair dados de licitação. Cobre municípios que publicam no DOU antes do PNCP.
3. **TCU Certidões** (P3, ~3h) — Verificação de sanções e inabilitação de fornecedores. Complementar ao pipeline de leads (STORY-184).

---

## Arquivos a Modificar

| Arquivo | Track | Mudança |
|---------|-------|---------|
| `backend/pncp_client.py` | T2 | Timeout per-modalidade, circuit breaker, health canary, retry on timeout |
| `backend/search_pipeline.py` | T3,T4 | Multi-source orchestration, degraded mode, response metadata |
| `backend/consolidation.py` | T3 | Source health registry, failover logic, ComprasGov last resort |
| `backend/source_config/sources.py` | T3 | Health status tracking, dynamic timeout adjustment |
| `backend/schemas.py` | T4 | `is_partial`, `data_sources`, `degradation_reason` em BuscaResponse |
| `backend/main.py` | T5,T6 | Fix rota `/setores`, health endpoint com source status |
| `frontend/app/buscar/page.tsx` | T4 | Banner degradação, mensagens de erro distintas |
| `frontend/app/api/setores/route.ts` | T5 | Verificar proxy URL |
| Railway env vars | T1 | `ENABLE_MULTI_SOURCE=true`, `ENABLE_SOURCE_COMPRAS_GOV=true` |

## Definition of Done

- [ ] Busca retorna resultados mesmo com PNCP offline (via fontes alternativas)
- [ ] Se NENHUMA fonte responde, erro claro em <10s (não 90s de espera)
- [ ] Se fontes parciais respondem, resultados parciais com banner informativo
- [ ] `/setores` retorna 200 em produção
- [ ] PNCP timeout não bloqueia mais a busca inteira (circuit breaker + canary)
- [ ] Dashboard de saúde das fontes via `/health`
- [ ] Todos os testes unitários novos passando
- [ ] Zero regressão em testes existentes
- [ ] TypeScript clean (`npx tsc --noEmit`)

## Out of Scope (Stories Futuras)

- **STORY-253:** JWT Token Refresh — investigar expiração repetida do token Supabase
- **STORY-254:** Portal da Transparência adapter — nova fonte federal gratuita
- **STORY-255:** Querido Diário adapter — fonte municipal open-source
- **STORY-256:** TCU Certidões integration — verificação de sanções para leads
