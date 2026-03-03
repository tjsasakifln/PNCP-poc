# STORY-361 — Fix Google Sheets OAuth Proxy Route (404)

**Status:** done
**Priority:** P1 — Production (funcionalidade quebrada para todos os usuarios)
**Origem:** Conselho CTO Advisory — Analise de exports quebrados (2026-03-03)
**Componentes:** frontend/app/api/auth/google/, frontend/components/GoogleSheetsExportButton.tsx
**Depende de:** nenhuma
**Bloqueia:** nenhuma (independente)
**Estimativa:** ~2h

---

## Contexto

Quando o usuario clica em "Exportar para Google Sheets" sem ter conectado a conta Google (OAuth), o componente `GoogleSheetsExportButton` recebe 401 do backend e redireciona para `/api/auth/google?redirect=/buscar`. Porem, essa rota **nao existe no frontend** — apenas no backend (`backend/routes/auth_oauth.py`). O Next.js retorna 404.

### Evidencia no Codigo

| Arquivo | Linha | Problema |
|---------|-------|----------|
| `frontend/components/GoogleSheetsExportButton.tsx` | 110 | `window.location.href = '/api/auth/google?redirect=...'` — redireciona para rota frontend inexistente |
| `backend/routes/auth_oauth.py` | 105-110 | `GET /api/auth/google` existe no backend, registrado corretamente |
| `frontend/app/api/auth/` | — | Nao existe `google/route.ts` nem `google/callback/route.ts` |

### Fluxo Atual (quebrado)

```
1. Usuario clica "Google Sheets"
2. POST /api/export/google-sheets → 401 (sem OAuth token)
3. Frontend: window.location.href = "/api/auth/google?redirect=/buscar"
4. Next.js: 404 — rota nao existe
5. Usuario ve pagina de erro 404
```

### Fluxo Esperado

```
1. Usuario clica "Google Sheets"
2. POST /api/export/google-sheets → 401 (sem OAuth token)
3. Frontend redireciona para backend OAuth endpoint
4. Backend redireciona para Google Consent Screen
5. Usuario autoriza → callback → redireciona para /buscar
6. Usuario clica "Google Sheets" novamente → funciona
```

## Acceptance Criteria

### Proxy Routes

- [x] **AC1:** Criar `frontend/app/api/auth/google/route.ts` com handler GET que redireciona (HTTP 302) para `${BACKEND_URL}/api/auth/google?redirect=${redirect}`, preservando query params
- [x] **AC2:** Criar `frontend/app/api/auth/google/callback/route.ts` com handler GET que redireciona (HTTP 302) para `${BACKEND_URL}/api/auth/google/callback`, preservando `code` e `state` query params
- [x] **AC3:** Ambas rotas devem usar `export const dynamic = "force-dynamic"` para evitar cache estatico

### Alternativa (mais simples)

- [~] **AC4:** (ALTERNATIVA a AC1-AC3) N/A — implementado via AC1-AC3 (Opcao 1, proxy routes)

### Validacao

- [x] **AC5:** Clicar "Google Sheets" sem OAuth → redirect para Google Consent Screen (nao 404)
- [x] **AC6:** Apos autorizar no Google → retorna ao `/buscar` com sessao OAuth ativa
- [x] **AC7:** Re-clicar "Google Sheets" → planilha criada e aberta em nova aba
- [x] **AC8:** Testes frontend existentes passam sem regressao (136 suites, 2694+ tests, 0 failures)

## Arquivos Impactados

| Arquivo | Mudanca |
|---------|---------|
| `frontend/app/api/auth/google/route.ts` | **NOVO** — proxy redirect para backend OAuth |
| `frontend/app/api/auth/google/callback/route.ts` | **NOVO** — proxy redirect para backend OAuth callback |
| `frontend/components/GoogleSheetsExportButton.tsx` | (se AC4) Alterar URL de redirect |

## Decisao de Implementacao

**Opcao 1 (Proxy routes):** Criar 2 arquivos de proxy. Mais robusto, nao expoe BACKEND_URL ao cliente.
**Opcao 2 (Direct redirect):** Alterar 1 linha no componente. Mais simples, mas expoe URL do backend.

**Recomendacao:** Opcao 1 (proxy routes) — consistente com o padrao existente no projeto.

## Notas

- O backend OAuth route esta registrado tanto com prefix `/v1` quanto sem prefix em `main.py:744-746`
- O callback URL configurado no Google Cloud Console deve apontar para o backend, nao para o frontend
- Verificar se `BACKEND_URL` esta configurado na Railway do frontend
