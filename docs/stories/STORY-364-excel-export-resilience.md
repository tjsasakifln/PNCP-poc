# STORY-364 — Excel Export Resilience (Decouple from SSE Lifecycle)

**Status:** pending
**Priority:** P1 — Production (Excel nao aparece apos buscas abortadas)
**Origem:** Conselho CTO Advisory — Analise de exports quebrados (2026-03-03)
**Componentes:** frontend/app/buscar/components/SearchResults.tsx, frontend/app/buscar/page.tsx, backend/routes/search.py
**Depende de:** STORY-362 (TTL + L3), STORY-363 (Async Pipeline)
**Bloqueia:** nenhuma
**Estimativa:** ~4h

---

## Contexto

O botao de download Excel depende de um SSE event `excel_ready` para receber `download_url` ou `download_id`. Quando o SSE morre (CRIT-048 AbortError), esse event nunca chega ao frontend. Resultado:

1. `result.excel_status` fica em `'processing'` eternamente
2. O botao mostra "Gerando Excel..." com spinner infinito
3. Apos 60 segundos, transiciona para "Gerar novamente" (retry)
4. O retry refaz a busca inteira — desperdicando tempo e quota

Apos STORY-363 (async pipeline), a busca sempre completa no Worker. Mas o Excel ainda precisa de um mecanismo confiavel para o frontend saber quando esta pronto.

### Evidencia no Codigo

| Arquivo | Linha | Problema |
|---------|-------|----------|
| `frontend/app/buscar/components/SearchResults.tsx` | 273-283 | `excelTimedOut` timer de 60s — se SSE morreu, Excel fica em processing |
| `frontend/app/buscar/components/SearchResults.tsx` | 766-767 | Visibilidade do botao depende de `result.download_url \|\| result.download_id` |
| `frontend/app/buscar/components/SearchResults.tsx` | 277 | `excel_status === 'processing' && !download_url && !download_id` → spinner infinito |

### Fluxo Atual (quebrado)

```
POST /buscar → Pipeline (Worker apos STORY-363)
  ├─ Busca + filtros → resultado
  ├─ ARQ job: gerar Excel
  └─ SSE event "excel_ready" com download_url
       ↓
  [SSE morreu] → Frontend nunca recebe download_url
       ↓
  Botao: "Gerando Excel..." → timeout 60s → "Gerar novamente"
```

### Fluxo Proposto (resiliente)

```
POST /buscar → Pipeline (Worker)
  ├─ Busca + filtros → resultado
  ├─ ARQ job: gerar Excel → store URL em Redis + Supabase
  └─ SSE event "excel_ready" (se SSE ativo)

Frontend (paralelo):
  ├─ SSE: recebe excel_ready → mostra botao download     (fast path)
  └─ Polling: GET /search/{id}/status → excel_url ready   (fallback)
```

## Acceptance Criteria

### Backend

- [ ] **AC1:** `GET /v1/search/{search_id}/status` inclui campo `excel_url` quando Excel esta pronto (alem de `status`, `progress`, etc.)
- [ ] **AC2:** `GET /v1/search/{search_id}/results` inclui campos `download_url` e `excel_status` no response
- [ ] **AC3:** Worker persiste `excel_url` no Redis junto com os resultados da busca (key: `smartlic:results:{search_id}`)

### Frontend — Polling Fallback

- [ ] **AC4:** Apos busca completar, se `excel_status === 'processing'` e SSE nao entregou `download_url`, iniciar polling em `GET /v1/search/{search_id}/status` a cada 5 segundos (max 12 tentativas = 60s)
- [ ] **AC5:** Quando polling retorna `excel_url`, atualizar `result.download_url` e exibir botao de download
- [ ] **AC6:** Se polling esgota 12 tentativas sem Excel, mostrar "Gerar novamente" (comportamento atual preservado)

### Frontend — Regeneracao

- [ ] **AC7:** Botao "Gerar novamente" nao refaz a busca inteira — chama novo endpoint `POST /v1/search/{search_id}/regenerate-excel` que gera Excel a partir dos resultados armazenados (L2/L3)
- [ ] **AC8:** Endpoint `regenerate-excel` retorna 404 se resultados expiraram, 202 se job enfileirado

### Testes

- [ ] **AC9:** Teste: Excel download funciona mesmo quando SSE desconecta (polling fallback)
- [ ] **AC10:** Teste: Botao "Gerar novamente" regenera Excel sem refazer busca
- [ ] **AC11:** Teste: `excelTimedOut` nao dispara se download_url ja esta disponivel
- [ ] **AC12:** Zero regressoes nos testes existentes

## Arquivos Impactados

| Arquivo | Mudanca |
|---------|---------|
| `backend/routes/search.py` | Incluir `excel_url` em `/search/{id}/status` e `/search/{id}/results` |
| `backend/routes/search.py` | Novo endpoint `POST /v1/search/{id}/regenerate-excel` |
| `backend/job_queue.py` | Job `regenerate_excel` que le resultados de L2/L3 |
| `frontend/app/buscar/hooks/useSearch.ts` | Adicionar polling fallback para excel_url |
| `frontend/app/buscar/components/SearchResults.tsx` | Integrar polling result, alterar "Gerar novamente" para usar regenerate |
| `frontend/app/api/buscar-results/[searchId]/route.ts` | (se necessario) Proxy para regenerate-excel |

## Notas Tecnicas

- O polling deve ser iniciado APENAS quando `excel_status === 'processing'` e o SSE nao entregou o URL — evitar polling desnecessario
- O timer de 60s para `excelTimedOut` deve ser mantido como fallback final, mas agora o polling resolve antes na maioria dos casos
- `regenerate-excel` reutiliza `create_excel()` de `excel.py` com os resultados armazenados — sem refazer busca
- Considerar usar `useSWR` com `refreshInterval` para o polling, consistente com o padrao do frontend
