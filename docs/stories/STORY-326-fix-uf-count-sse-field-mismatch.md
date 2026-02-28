# STORY-326: Corrigir campo `count` vs `items_found` no SSE — contagem zero permanente no grid de UFs

**Prioridade:** P0 (bug user-facing)
**Complexidade:** S (Small)
**Sprint:** CRIT-SEARCH

## Problema

O grid de progresso por UF mostra permanentemente "**0 oportunidades**" e "Sem oportunidades" para **todos** os estados (ES, MG, RJ, SP), mesmo quando fontes retornam dados. O contador no topo (`Encontradas: 0 oportunidades até agora`) fica em zero durante toda a busca, enquanto o banner inferior mostra corretamente "1930 oportunidades encontradas até agora".

**Evidência:** Screenshots de produção 2026-02-28 mostram `0` no topo vs `1930` embaixo.

## Causa Raiz

Mismatch de campo no contrato SSE entre backend e frontend:

- **Backend** (`pncp_client.py`): chama `on_uf_status(uf, "success", count=len(items))` → `progress.py:emit_uf_status()` passa `count` como `**detail` kwarg → evento SSE tem `detail.count = N`
- **Frontend** (`useSearchSSE.ts:~226`): lê `event.detail.items_found` (campo do evento `emit_uf_complete`, NÃO do `emit_uf_status`)
- **Resultado**: `ufEvent.count = undefined` → `UfStatus.count = undefined` → `(status.count || 0) = 0` → "Sem oportunidades"

## Critérios de Aceite

- [ ] AC1: No `useSearchSSE.ts`, o handler de `uf_status` deve ler `event.detail.count` (que o backend envia) em vez de `event.detail.items_found` para popular o count da UF
- [ ] AC2: Quando PNCP retorna N itens para uma UF e emite `uf_status` com `status=success`, o grid deve mostrar "N oportunidades" em verde (não "Sem oportunidades" em amarelo)
- [ ] AC3: O contador no topo (`ufTotalFound`) deve somar corretamente os counts de todas as UFs com status `success` ou `recovered`
- [ ] AC4: Teste unitário simula evento `uf_status` com `detail: { count: 42, uf: "SP", uf_status: "success" }` e verifica que `ufStatuses.get("SP").count === 42`
- [ ] AC5: Teste de `UfProgressGrid` renderiza com `totalFound=150` e verifica que exibe "150" (não "0")
- [ ] AC6: Documentar o contrato SSE do evento `uf_status` no JSDoc do `SearchProgressEvent.detail` com campos corretos: `uf`, `uf_status`, `count`, `attempt`, `reason`
- [ ] AC7: Backend NÃO é alterado — o campo `count` já está correto no backend

## Arquivos Afetados

- `frontend/hooks/useSearchSSE.ts` (correção principal ~1 linha)
- `frontend/__tests__/hooks/useSearchSSE-uf-count.test.tsx` (novo)
- `frontend/__tests__/components/UfProgressGrid.test.tsx` (expandir)

## Notas

- Fix de 1 linha no frontend: trocar `items_found` por `count`
- Não requer mudanças no backend
- Pré-requisito para STORY-327
