# GTM-FIX-033: Busca completa no backend mas frontend exibe erro

**Priority:** P0 (usuário perde resultado já processado)
**Effort:** M (4-6h)
**Origin:** Teste de produção manual 2026-02-18
**Status:** PENDENTE
**Assignee:** @dev
**Tracks:** Backend (1 AC), Frontend (4 ACs), Ops (1 AC), Tests (2 ACs)

---

## Problem Statement

O backend completa a busca com sucesso (1717 bids → filtros → Excel gerado), mas o frontend exibe "Não foi possível processar sua busca. Tente novamente em instantes." O progresso chega a 80%+ e depois reseta para erro.

### Evidência dos Logs (Railway)

```
[PCP] Reached page limit (100). Total records (1807) may exceed fetched.
[PCP] Fetch complete: 36 records (truncated=True)
[CONSOLIDATION] PORTAL_COMPRAS: 36 records in 130091ms    ← 130s para PCP
[MULTI-SOURCE] PNCP: 1733 records, error=None
[MULTI-SOURCE] PORTAL_COMPRAS: 36 records, error=None
[CONSOLIDATION] Complete: 1769 raw -> 1717 deduped (52 duplicates removed) in 130110ms
✅ Excel available via signed URL (TTL: 60min)               ← Backend COMPLETOU
```

O PCP sozinho levou **130s** para SP. O frontend mostra erro apesar do backend ter terminado com sucesso.

### Root Cause Analysis

1. **SSE desconecta silenciosamente**: `useUfProgress.ts:136-139` — `eventSource.onerror` apenas loga warning e chama `cleanup()`. Não retenta nem notifica componente pai. O frontend perde tracking em tempo real.
2. **Simulação time-based descasa do backend**: Com SSE morta, `useSearchProgress.ts` roda simulação que pode "concluir" antes do POST real retornar, ou resetar a barra.
3. **Erro genérico no frontend**: `lib/error-messages.ts:36-37,87` — qualquer falha de rede/timeout vira "Não foi possível processar sua busca" sem detalhes.
4. **PCP lentidão**: 130s para 1 estado é excessivo. A env var `PCP_TIMEOUT` existe mas pode não estar configurada em produção, usando default alto.

### Impact

| Cenário | Efeito no Usuário |
|---------|-------------------|
| Busca 1 UF (SP) | Espera 2+ min, vê 80%, recebe erro. Resultado perdido. |
| Busca 27 UFs | Timeout garantido. Nunca vê resultado. |
| Retry | Cache já existe (`search_pipeline.py:590-603` salva antes de retornar) mas o frontend pode não buscar do cache no retry |

---

## Acceptance Criteria

### Ops (Railway)

- [ ] **AC1**: Configurar `PCP_TIMEOUT=30` como env var no Railway. Quick win imediato que limita PCP a 30s em vez de default alto.

### Frontend

- [ ] **AC2**: `useUfProgress.ts:136-139` — SSE `onerror` deve tentar reconectar 1x (com delay de 2s) antes de desistir. Se desistir, setar flag `sseDisconnected=true` no state retornado.
- [ ] **AC3**: Progress bar não pode resetar de 80%+ para 0%. Se SSE desconecta (`sseDisconnected`), travar na última porcentagem conhecida e exibir "Finalizando busca..."
- [ ] **AC4**: Se o POST `/api/buscar` retorna sucesso (HTTP 200) mas SSE já marcou erro/desconectou, o resultado do POST deve prevalecer e ser exibido normalmente.
- [ ] **AC5**: Mensagem de erro melhorada em `lib/error-messages.ts`: incluir "A busca pode ter sido concluída. Verifique suas buscas salvas ou tente novamente."

### Tests

- [ ] **AC6**: Teste frontend: SSE desconecta no meio da busca → resultado POST ainda é processado e exibido
- [ ] **AC7**: Teste backend: PCP timeout não bloqueia resposta PNCP (partial results devem ser servidos quando PCP falha)

---

## Arquivos Relevantes

| Arquivo | Linhas | O que mudar |
|---------|--------|-------------|
| `frontend/app/buscar/hooks/useUfProgress.ts` | 136-139 | SSE error → retry 1x + flag |
| `frontend/hooks/useSearchProgress.ts` | Full | Respeitar flag `sseDisconnected` |
| `frontend/lib/error-messages.ts` | 36-37, 87 | Mensagem melhorada |
| `frontend/app/buscar/page.tsx` | Busca handler | POST result prevalece sobre SSE error |
| `backend/search_pipeline.py` | 590-603 | Cache já funciona (verificar) |

## Prioridade de Implementação

1. **AC1 — Quick win** (5 min): Setar `PCP_TIMEOUT=30` no Railway
2. **AC3 — Visual** (1h): Progress bar não reseta — impede frustração imediata
3. **AC4 — Dados** (2h): POST result prevalece — impede perda de resultado
4. **AC2 — Resiliência** (1h): SSE retry — reduz chance do problema ocorrer
5. **AC5 — Copy** (30min): Mensagem de erro útil
