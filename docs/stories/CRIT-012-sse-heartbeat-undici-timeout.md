# CRIT-012 — SSE Heartbeat Gap + Undici BodyTimeoutError

**Status:** completed
**Priority:** P1 — Production (erros recorrentes em logs Railway)
**Origem:** Consultoria externa — Análise de logs Railway (2026-02-21)
**Componentes:** backend/routes/search.py, backend/progress.py, frontend/app/api/buscar-progress/route.ts

---

## Contexto

Consultoria externa identificou nos logs de produção a seguinte cadeia de erros:

1. `BodyTimeoutError` (undici) — o body do fetch ficou tempo demais sem entregar dados
2. `TypeError: terminated` (Fetch.terminate) — conexão do fetch encerrada por timeout/abort
3. `Error: failed to pipe response` (next/dist/pipe-readable.js) — Next.js tentou transmitir stream que já morreu

**Causa raiz:** O proxy SSE em `buscar-progress/route.ts` faz pass-through do stream do backend. Quando o backend fica silencioso (sem eventos nem heartbeats), o undici do Node interpreta como "body parado" e mata a conexão.

## Análise Técnica

### O que já existe (parcialmente)

O backend SSE endpoint (`routes/search.py:~269`) **já tem heartbeat**:
```python
except _asyncio.TimeoutError:
    yield ": heartbeat\n\n"  # a cada 30s de silêncio
```

### Onde estão as lacunas

| Gap | Descrição | Impacto |
|-----|-----------|---------|
| **Gap 1: Wait-for-tracker** | O endpoint espera até 30s (60 × 0.5s) pelo tracker ser criado. **Nenhum dado é enviado durante esse período.** | undici pode abortar antes do primeiro byte |
| **Gap 2: Heartbeat interval** | 30s entre heartbeats pode ser muito próximo do timeout de proxies intermediários (Railway, Cloudflare) | Corridas de timeout causam falhas intermitentes |
| **Gap 3: Frontend proxy** | `buscar-progress/route.ts` não configura body timeout do undici e não gera heartbeats próprios | Sem controle sobre o timeout de leitura do body |
| **Gap 4: Sem signal/abort** | O fetch do proxy não usa `AbortController` — se o cliente desconecta, o fetch backend fica pendurado | Leak de conexões SSE |

## Acceptance Criteria

### Backend — Heartbeat durante wait-for-tracker

- [x] **AC1:** Durante o loop de espera pelo tracker (`wait_for_tracker`, até 30s), enviar comentários SSE (`:\n\n`) a cada 5s para manter a conexão viva
- [x] **AC2:** Reduzir o intervalo de heartbeat de 30s para 15s no loop principal de eventos (tanto Redis quanto in-memory)
- [x] **AC3:** Adicionar log de telemetria ao emitir heartbeats (nível DEBUG), com contagem de heartbeats por search_id

### Frontend Proxy — Configuração undici + resiliência

- [x] **AC4:** Configurar `bodyTimeout: 0` (desabilitar) no fetch do proxy SSE para evitar que undici mate a conexão durante streams longos
- [x] **AC5:** Usar `AbortController` com `request.signal` para cancelar o fetch backend quando o cliente desconecta
- [x] **AC6:** Adicionar tratamento explícito para `BodyTimeoutError` e `TypeError: terminated` no catch, retornando 504 com mensagem descritiva em vez de 502 genérico

### Observabilidade

- [x] **AC7:** Adicionar log estruturado no proxy SSE para erros de streaming: `{ error_type, search_id, elapsed_ms, heartbeats_received }`
- [x] **AC8:** Criar métrica Prometheus `sse_connection_errors_total` (labels: `error_type`, `phase`) no backend

### Testes

- [x] **AC9:** Teste backend: SSE endpoint envia heartbeat durante wait-for-tracker (simular tracker que demora 10s para aparecer, verificar que comentários SSE são emitidos antes)
- [x] **AC10:** Teste backend: heartbeat a cada 15s durante silêncio no loop principal
- [x] **AC11:** Teste frontend: proxy SSE trata `TypeError: terminated` e retorna 504
- [x] **AC12:** Zero regressões nos testes existentes (baseline: ~35 fail backend, ~50 fail frontend)

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `backend/routes/search.py` | Heartbeat no wait-for-tracker loop, reduzir intervalo de 30s→15s |
| `backend/progress.py` | (opcional) Expor contagem de heartbeats no tracker |
| `backend/metrics.py` | Nova métrica `sse_connection_errors_total` |
| `frontend/app/api/buscar-progress/route.ts` | bodyTimeout: 0, AbortController, error handling |

## Solução Proposta

### 1. Backend — Heartbeat durante espera pelo tracker

```python
# routes/search.py — dentro do generator
async def event_generator():
    # Fase 1: Esperar tracker com heartbeats
    tracker = None
    for i in range(60):
        tracker = get_tracker(search_id)
        if tracker:
            break
        if i > 0 and i % 10 == 0:  # a cada 5s (10 × 0.5s)
            yield ": waiting\n\n"
        await asyncio.sleep(0.5)

    # Fase 2: Loop de eventos com heartbeat a cada 15s
    while True:
        try:
            event = await asyncio.wait_for(queue.get(), timeout=15.0)
            yield f"event: {event['stage']}\ndata: {json.dumps(event)}\n\n"
            if event.get("stage") in terminal_stages:
                break
        except asyncio.TimeoutError:
            yield ": heartbeat\n\n"
```

### 2. Frontend Proxy — Timeout + cleanup

```typescript
// buscar-progress/route.ts
export async function GET(request: NextRequest, { params }) {
    const controller = new AbortController();

    // Cancelar fetch backend quando cliente desconecta
    request.signal.addEventListener('abort', () => controller.abort());

    const backendResponse = await fetch(url, {
        headers,
        signal: controller.signal,
        // @ts-ignore — undici-specific
        dispatcher: new (await import('undici')).Agent({ bodyTimeout: 0 }),
    });

    return new Response(backendResponse.body, { ... });
}
```

## Referências

- CRIT-008 (Frontend Resilience During Backend Restarts) — auto-retry + countdown
- CRIT-009 (Structured Error Observability) — error codes
- GTM-RESILIENCE-E03 (Prometheus Metrics)
- [undici BodyTimeoutError docs](https://undici.nodejs.org/#/docs/api/Errors)

## Definition of Done

- [x] Heartbeats emitidos durante wait-for-tracker (gap eliminado)
- [x] Intervalo de heartbeat reduzido para 15s
- [x] Proxy SSE com bodyTimeout desabilitado
- [x] AbortController conectado ao request.signal
- [x] Testes cobrindo todos os ACs
- [x] Zero regressões
- [ ] Deploy Railway + verificar ausência de BodyTimeoutError nos logs (24h)
