# CRIT-009: Observabilidade do Erro de Busca — Detalhes Tecnicos Uteis

## Epic
Consistencia Estrutural do Sistema (EPIC-CRIT)

## Sprint
Sprint 5: Resiliencia de Producao

## Prioridade
P0

## Estimativa
12h

## Descricao

Os "Detalhes tecnicos" exibidos ao usuario quando a busca falha sao praticamente inuteis. Hoje mostram apenas timestamp e a propria mensagem "Erro no backend", sem nenhuma informacao acionavel para suporte ou debugging.

O problema e uma cadeia de perda de informacao em 4 pontos:

```
Backend HTTPException(detail="...real error...")
         |
    [PERDA 1] Proxy extrai detail mas descarta correlation_id do header
         |
Frontend Proxy retorna { message: "...", status: N }
         |
    [PERDA 2] useSearch faz throw new Error(err.message) — perde metadata
         |
getUserFriendlyError(e) → string amigavel
         |
    [PERDA 3] setError(string) — so armazena string, nao objeto estruturado
         |
ErrorDetail(errorMessage=string, searchId, timestamp)
         |
    [PERDA 4] Componente so tem string + searchId + timestamp cliente
```

### Gap Documentado na Investigacao

| Campo | Backend retorna? | Proxy repassa? | Frontend captura? | ErrorDetail mostra? |
|-------|:---:|:---:|:---:|:---:|
| Error message | Sim (`detail`) | Sim (`message`) | Sim | Sim (mas amigavel) |
| Error code | Nao | Nao | Nao | Nao |
| Correlation ID | Sim (header `X-Correlation-ID`) | Nao extrai | Nao | Nao |
| Request ID | Sim (`X-Request-ID` gerado pelo proxy) | Nao retorna | Nao | Nao |
| HTTP status | Sim | Sim (`status` field) | Sim | Nao passado |
| Timestamp | Nao | Nao | Gerado no client | Sim |
| search_id | Sim (se enviado) | Nao retorna | Sim (estado local) | Sim |

### Relacao com CRIT-004

CRIT-004 trata da propagacao de Correlation ID ponta a ponta nos logs do backend. Esta story foca no **lado oposto**: garantir que o frontend CAPTURE e EXIBA informacoes uteis quando o erro chega ao usuario. Sao complementares.

## Criterios de Aceite

### Backend: Estruturar Respostas de Erro

- [ ] AC1: Todas as `HTTPException` do endpoint `/buscar` devem retornar body estruturado:
  ```json
  {
    "detail": "Mensagem descritiva do erro",
    "error_code": "SOURCE_UNAVAILABLE|TIMEOUT|RATE_LIMIT|VALIDATION_ERROR|INTERNAL_ERROR",
    "search_id": "uuid-se-disponivel",
    "correlation_id": "uuid-do-request",
    "timestamp": "ISO8601"
  }
  ```
  - Arquivo: `backend/routes/search.py` — handler `buscar_licitacoes()`
  - Nao expor stack traces ou informacoes internas (manter sanitizado)

- [ ] AC2: Criar enum `SearchErrorCode` em `backend/schemas.py`:
  ```python
  class SearchErrorCode(str, Enum):
      SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
      ALL_SOURCES_FAILED = "ALL_SOURCES_FAILED"
      TIMEOUT = "TIMEOUT"
      RATE_LIMIT = "RATE_LIMIT"
      QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
      VALIDATION_ERROR = "VALIDATION_ERROR"
      INTERNAL_ERROR = "INTERNAL_ERROR"
  ```

- [ ] AC3: `AllSourcesFailedError`, `PNCPDegradedError`, `asyncio.TimeoutError` e `QuotaExceededError` devem mapear para seus respectivos `error_code` no handler de busca

### Proxy: Preservar Metadata de Erro

- [ ] AC4: `frontend/app/api/buscar/route.ts` deve extrair e repassar campos estruturados do backend:
  ```typescript
  // Ao receber erro do backend:
  const errorBody = await response.json().catch(() => ({}));
  return NextResponse.json({
    message: errorBody.detail || errorBody.message || "Erro no backend",
    error_code: errorBody.error_code || null,
    search_id: errorBody.search_id || null,
    correlation_id: errorBody.correlation_id || response.headers.get("X-Correlation-ID") || null,
    request_id: requestId,  // Gerado pelo proxy
    timestamp: new Date().toISOString(),
    status: response.status,
  }, { status: response.status });
  ```

- [ ] AC5: O proxy deve incluir `X-Request-ID` como header NA RESPOSTA ao browser (alem de no request ao backend)
  - Permite ao usuario copiar o Request ID do DevTools Network tab para suporte

### Frontend Hook: Preservar Erro Estruturado

- [ ] AC6: `useSearch.ts` deve armazenar erro estruturado, nao apenas string:
  ```typescript
  interface SearchError {
    message: string;         // Mensagem amigavel para o usuario
    rawMessage: string;      // Mensagem original do backend
    errorCode: string | null;
    searchId: string | null;
    correlationId: string | null;
    requestId: string | null;
    httpStatus: number | null;
    timestamp: string;
  }
  ```
  - Substituir `setError(string)` por `setError(SearchError | null)`
  - `getUserFriendlyError()` popula `message`; campos raw preservados do response JSON

- [ ] AC7: `SearchResults.tsx` deve passar `SearchError` completo para `ErrorDetail`:
  ```typescript
  <ErrorDetail error={error} />  // error: SearchError
  ```
  - Em vez de `errorMessage={error}` (string)

### Componente ErrorDetail: Exibir Informacoes Uteis

- [ ] AC8: `ErrorDetail.tsx` deve exibir secao expansivel "Detalhes tecnicos" com campos disponiveis:
  ```
  Detalhes tecnicos:
  ├─ ID da busca: {searchId}
  ├─ ID da requisicao: {requestId}
  ├─ ID de correlacao: {correlationId}
  ├─ Codigo do erro: {errorCode}
  ├─ Status HTTP: {httpStatus}
  ├─ Horario: {timestamp}
  └─ Mensagem original: {rawMessage}
  ```
  - Campos ausentes (null) nao devem ser exibidos
  - Minimo: pelo menos `timestamp` + `searchId` sempre presentes

- [ ] AC9: Botao "Copiar detalhes" que copia JSON formatado para clipboard:
  ```json
  {
    "search_id": "...",
    "request_id": "...",
    "correlation_id": "...",
    "error_code": "SOURCE_UNAVAILABLE",
    "http_status": 502,
    "timestamp": "2026-02-20T23:08:29Z",
    "message": "Nossas fontes estao temporariamente indisponiveis"
  }
  ```
  - Toast de confirmacao: "Detalhes copiados para a area de transferencia"
  - Formato pensado para colar em ticket de suporte ou enviar ao time

- [ ] AC10: ErrorDetail deve ter `aria-label` e `role="alert"` para acessibilidade
  - Botao "Copiar detalhes" com aria-label descritivo

### Mapeamento de Error Codes para Mensagens

- [ ] AC11: Atualizar `frontend/lib/error-messages.ts` com mapeamento:
  ```typescript
  const ERROR_CODE_MESSAGES: Record<string, string> = {
    SOURCE_UNAVAILABLE: "Nossas fontes de dados estao temporariamente indisponiveis.",
    ALL_SOURCES_FAILED: "Nenhuma fonte de dados respondeu. Tente novamente em alguns minutos.",
    TIMEOUT: "A busca demorou mais que o esperado. Tente reduzir o numero de estados.",
    RATE_LIMIT: "Limite de requisicoes atingido. Aguarde alguns minutos.",
    QUOTA_EXCEEDED: "Voce atingiu o limite de buscas do seu plano.",
    VALIDATION_ERROR: "Parametros de busca invalidos. Verifique os filtros.",
    INTERNAL_ERROR: "Erro interno. Nossa equipe foi notificada.",
  };
  ```
  - Se `error_code` presente: usar mensagem mapeada (mais especifica)
  - Se `error_code` ausente: usar `getUserFriendlyError()` existente (fallback)

## Testes Obrigatorios

### Backend (pytest)

```bash
cd backend && python -m pytest tests/test_search_error_codes.py -v --no-header
```

- [ ] T1: `AllSourcesFailedError` retorna `error_code: "ALL_SOURCES_FAILED"` + `correlation_id` + `search_id`
- [ ] T2: `asyncio.TimeoutError` retorna `error_code: "TIMEOUT"`
- [ ] T3: `QuotaExceededError` retorna `error_code: "QUOTA_EXCEEDED"`
- [ ] T4: Erro generico retorna `error_code: "INTERNAL_ERROR"` (nao expoe stack trace)
- [ ] T5: Validacao de body com campos obrigatorios (detail, error_code, timestamp)

### Frontend (jest)

```bash
cd frontend && npm test -- --testPathPattern="error-observability|ErrorDetail" --no-coverage
```

- [ ] T6: Proxy preserva `error_code` e `correlation_id` do backend
- [ ] T7: Proxy gera campos quando backend nao os fornece (fallback graceful)
- [ ] T8: useSearch armazena `SearchError` estruturado (nao string)
- [ ] T9: ErrorDetail renderiza todos os campos disponiveis
- [ ] T10: ErrorDetail oculta campos null/undefined
- [ ] T11: Botao "Copiar detalhes" copia JSON correto para clipboard
- [ ] T12: Error code mapeado para mensagem amigavel em portugues
- [ ] T13: Error code desconhecido usa fallback generico
- [ ] T14: `X-Request-ID` presente no response header do proxy

### Pre-existing baselines
- Backend: ~35 fail / ~3924 pass
- Frontend: ~42 fail / ~1912 pass
- Nenhuma regressao permitida

## Definicao de Pronto

- [ ] Todos os ACs implementados e checkboxes marcados
- [ ] 14 testes novos passando
- [ ] Zero regressoes nos baselines
- [ ] TypeScript compila sem erros (`npx tsc --noEmit`)
- [ ] Backend: `SearchErrorCode` enum exportado no OpenAPI schema
- [ ] Testado manualmente: forcar erro 502 → verificar ErrorDetail mostra campos uteis
- [ ] Story file atualizado com `[x]` em todos os checkboxes

## Arquivos Afetados

| Arquivo | Tipo de Mudanca |
|---------|----------------|
| `backend/schemas.py` | Modificar — adicionar `SearchErrorCode` enum |
| `backend/routes/search.py` | Modificar — estruturar HTTPException responses |
| `frontend/app/api/buscar/route.ts` | Modificar — preservar metadata de erro |
| `frontend/app/buscar/hooks/useSearch.ts` | Modificar — `SearchError` interface, preservar estrutura |
| `frontend/app/buscar/components/ErrorDetail.tsx` | Modificar — exibir campos estruturados + copiar |
| `frontend/app/buscar/components/SearchResults.tsx` | Modificar — passar `SearchError` para ErrorDetail |
| `frontend/lib/error-messages.ts` | Modificar — mapeamento error_code → mensagem |
| `backend/tests/test_search_error_codes.py` | Criar — testes T1-T5 |
| `frontend/__tests__/error-observability.test.tsx` | Criar — testes T6-T14 |

## Notas Tecnicas

### Pitfalls Conhecidos
- `response.headers.get("X-Correlation-ID")` pode retornar `null` se middleware nao foi ativado — tratar com fallback
- `navigator.clipboard.writeText()` requer HTTPS ou localhost — guard com `try/catch` + fallback `document.execCommand('copy')`
- Alterar tipo de `error` state em `useSearch.ts` de `string | null` para `SearchError | null` requer atualizar TODOS os consumers — verificar com `grep "error" app/buscar/`
- `SearchErrorCode` enum no backend nao deve ser confundido com HTTP status codes — sao ortogonais

### Decisoes de Design
- **Error code vs HTTP status:** Error codes sao semanticos (o que aconteceu), HTTP status sao protocolares (como responder). Ambos necessarios.
- **Raw message preservada:** Permite suporte tecnico ver a mensagem original sem pedir logs ao usuario.
- **JSON clipboard:** Formato pensado para colar em Slack/email/ticket. Mais util que texto formatado.

## Dependencias

| Tipo | Story | Motivo |
|------|-------|--------|
| Complementar | CRIT-004 | CRIT-004 propaga IDs nos logs; esta story propaga IDs ate o usuario |
| Paralela | CRIT-008 | Resiliencia de restart complementa observabilidade |
| Nenhuma bloqueante | — | Pode ser implementada independentemente |
