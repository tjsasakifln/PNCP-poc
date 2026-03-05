# CRIT-060: Alinhamento de Timeouts Proxy Frontend vs Railway

**Prioridade:** HIGH
**Componente:** Frontend — app/api/buscar/route.ts, app/api/buscar-progress/route.ts
**Origem:** Incidente 2026-03-05 — SSE AbortError em 208s; proxy POST timeout 115s desalinhado com Railway 300s
**Status:** TODO
**Dependencias:** Nenhuma (fix isolado)
**Estimativa:** 1h

## Problema

O proxy POST `/api/buscar/route.ts` tem AbortController com timeout de 115s, baseado na premissa (incorreta) de que Railway tem hard timeout de ~120s. Railway real timeout e 300s (confirmado em MEMORY.md).

O proxy SSE `/api/buscar-progress/route.ts` tem `bodyTimeout: 0` (sem limite), mas depende do client-side abort signal. Na pratica, o SSE pipe falhou em 208s com AbortError — possivelmente causado por:

1. Browser/tab timeout (improvavel — SSE recebe heartbeats)
2. Railway proxy idle timeout entre chunks (mais provavel se heartbeat gap > idle timeout)
3. Next.js serverless function timeout (se Vercel — mas estamos no Railway)

### Desalinhamento atual

```
Frontend POST proxy:  115s (AbortController) ← MUITO CURTO
Backend PIPELINE:     110s (PIPELINE_TIMEOUT)
Railway hard timeout: 300s
Backend Gunicorn:     180s (GUNICORN_TIMEOUT)
```

Se o pipeline leva 157s, o proxy POST ja teria abortado em 115s. So funciona porque o frontend usa SSE (GET) em paralelo com POST.

Mas se o SSE cair (como aconteceu), o POST tambem ja foi abortado, e o usuario perde tudo.

## Acceptance Criteria

### AC1: Ajustar timeout do proxy POST
- [ ] `buscar/route.ts` AbortController: 115s → 180s
- [ ] Comentario atualizado: `"Railway hard timeout: 300s; proxy stays below with margin"`
- [ ] Manter STAB-003 AC5 label no comentario para rastreabilidade

### AC2: Ajustar heartbeat interval para SSE
- [ ] Verificar que heartbeat backend (`_SSE_HEARTBEAT_INTERVAL`) e menor que Railway idle timeout
- [ ] Se Railway idle timeout e 60s e heartbeat e 15s → OK (CRIT-012 ja corrigiu)
- [ ] Documentar a cadeia de timeouts no comentario do proxy SSE

### AC3: Documentar cadeia de timeouts atualizada
- [ ] Atualizar CLAUDE.md secao "Timeout chain" com valores corretos:
  ```
  Railway(300s) > Gunicorn(180s) > Proxy POST(180s) > Pipeline(110s) >
  Consolidation(100s) > PerSource(80s) > PerUF(30s)
  SSE: bodyTimeout(0) + heartbeat(15s) > Railway idle(60s)
  ```

### AC4: Teste
- [ ] Atualizar `buscar.test.ts` se tiver assertion no timeout value
- [ ] Nenhum teste novo necessario (e apenas mudanca de constante)

## File List

| Arquivo | Mudanca |
|---------|---------|
| `frontend/app/api/buscar/route.ts` | Timeout 115s → 180s |
| `frontend/app/api/buscar-progress/route.ts` | Comentario de timeout chain |
| `CLAUDE.md` | Atualizar secao timeout chain |
