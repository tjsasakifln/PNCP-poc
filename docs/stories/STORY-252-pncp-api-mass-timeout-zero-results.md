# STORY-252: PNCP API Mass Timeout — Zero Results em 27 UFs

## Metadata
| Field | Value |
|-------|-------|
| **ID** | STORY-252 |
| **Priority** | P0 (Production broken) |
| **Sprint** | Sprint 1 |
| **Estimate** | 5h |
| **Depends on** | Nenhuma |
| **Blocks** | Toda busca em produção |

## Problema

Busca por setor "Alimentos e Merenda" em produção retornou **zero resultados** em 27 estados. Isso é absurdo — centenas de licitações de alimentos existem no PNCP a qualquer momento. A análise dos logs Railway revelou **dois problemas distintos**:

### Problema 1: PNCP API Mass Timeout (P0 — Crítico)

Todas as 27 UFs deram timeout após 90s e foram skipadas:

```
UF=MT timed out after 90s — skipping
UF=MS timed out after 90s — skipping
UF=MG timed out after 90s — skipping
UF=PA timed out after 90s — skipping
... (todas as 27 UFs)
```

**Resultado:** `Parallel fetch complete: 0 items from 27 UFs in 90.02s (0 errors)`

O pipeline processou corretamente o setor:
- `Using sector: Alimentos e Merenda (85 keywords)` ✓
- `Using parallel fetch for 27 UFs (max_concurrent=10)` ✓

Mas o PNCP simplesmente não respondeu a tempo. O timeout per-UF de 90s cobre TODAS as modalidades (4,5,6,7) e todas as páginas — se a primeira requisição travar, o UF inteiro é descartado.

Também observado: `Error fetching UF=AP, modalidade=4: API returned non-retryable status 422` — possível mudança na API do PNCP.

### Problema 2: Endpoint `/setores` retorna 404 (P1 — Alto)

```
GET /v1/setores -> 404 (1ms)
GET /v1/setores -> 404 (0ms)
GET /v1/setores -> 404 (0ms)
```

O frontend proxy chama `/api/setores` que é roteado para o backend como `/v1/setores`, mas o endpoint não existe no backend deployed. **Resultado:** Frontend SEMPRE usa fallback hardcoded, nunca carrega setores dinâmicos.

### Problema 3: JWT Token Expired repetido (P2)

```
JWT token expired (múltiplas ocorrências a cada ~60s)
GET /v1/api/messages/unread-count -> 401
```

O token do Supabase está expirando e o refresh não está acontecendo corretamente durante a sessão do Playwright. Pode afetar usuários reais também.

## Impacto

- **Busca completamente inoperante** em produção
- Afeta TODOS os setores (não apenas alimentos)
- Usuário espera ~90s e recebe zero resultados
- Experiência catastrófica — produto não funciona

## Investigação Necessária

1. A PNCP API mudou algo? Está fora do ar? Responde a requisições manuais via curl?
2. O timeout de 90s per-UF é compartilhado entre modalidades? Pode ser que modalidade 4 trave e consuma o timeout todo.
3. O erro 422 em AP indica mudança no schema da API PNCP?
4. O `/setores` endpoint existe no backend local mas não no deployed? Verificar routing.
5. O refresh do JWT está funcionando corretamente no frontend?

## Acceptance Criteria

### Track 1: PNCP API Resilience
- [ ] **AC1:** Diagnosticar se PNCP API está down ou se há rate limiting. Testar com `curl` direto para `https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao`.
- [ ] **AC2:** Implementar timeout PER-MODALIDADE em vez de per-UF global. Se modalidade 4 trava, modalidades 5,6,7 ainda tentam.
- [ ] **AC3:** Implementar retry com backoff quando timeout acontece (hoje é skip direto).
- [ ] **AC4:** Se PNCP timeout em >50% das UFs, retornar erro explícito ao usuário ("PNCP indisponível no momento") em vez de "0 resultados".
- [ ] **AC5:** Adicionar circuit breaker: se N timeouts consecutivos, parar de chamar PNCP e retornar erro rápido.
- [ ] **AC6:** Log estruturado com UFs que responderam vs. timeout para monitoring.

### Track 2: Endpoint `/setores` Missing
- [ ] **AC7:** Verificar se rota `/setores` existe no backend (sem prefix `/v1`).
- [ ] **AC8:** Se necessário, adicionar rota `/v1/setores` ao backend ou ajustar proxy frontend.
- [ ] **AC9:** Frontend carrega setores do backend em produção (não mais fallback).

### Track 3: UX de Falha
- [ ] **AC10:** Se busca retorna 0 resultados por timeout, mostrar mensagem distinta de "Nenhum resultado encontrado" — ex: "PNCP não respondeu a tempo. Tente novamente em alguns minutos."
- [ ] **AC11:** Distinguir no response: `total_raw=0 + all_timeouts=true` vs `total_raw=100 + filtered=0`.

### Track 4: JWT Refresh
- [ ] **AC12:** Investigar se o JWT refresh do Supabase está funcionando corretamente.
- [ ] **AC13:** Garantir que token é refreshed antes de expirar (não depois do 401).

## Evidência

**Timestamp:** 2026-02-14T17:11:48 — 2026-02-14T17:13:18 (90s de busca)
**Request ID:** afbdba36-71a0-45a3-b673-bf5f2b03bf3e
**Setor:** alimentos (reconhecido corretamente como "Alimentos e Merenda")
**UFs:** 27 (todas)
**Resultado:** 0 raw bids, 0 filtered, 27/27 UFs em timeout

## Arquivos Prováveis

| Arquivo | Mudança |
|---------|---------|
| `backend/pncp_client.py` | Timeout per-modalidade, retry on timeout, circuit breaker |
| `backend/search_pipeline.py` | Detecção de mass timeout, response metadata |
| `backend/main.py` | Rota `/v1/setores` ou ajuste de prefix |
| `frontend/app/api/setores/route.ts` | Proxy para backend correto |
| `frontend/app/buscar/hooks/useSearchFilters.ts` | Fallback messaging |
| `frontend/app/buscar/page.tsx` | UX de falha por timeout vs. sem resultados |

## Definition of Done
- Busca retorna resultados em pelo menos 50% das UFs
- Se PNCP está down, usuário recebe mensagem clara em <10s
- `/setores` endpoint funciona em produção
- Sem JWT expired errors repetidos
