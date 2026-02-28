# CRIT-042: Health Canary Não Deve Sabotar o Próprio Circuit Breaker

**Epic:** Production Stability
**Sprint:** Sprint 4
**Priority:** P1 — HIGH
**Story Points:** 5 SP
**Estimate:** 3-4 horas
**Owner:** @dev

---

## Problem

O health canary (`cron_jobs.py:run_health_canary()`) faz queries ao Supabase via `sb_execute()` que passam pelo mesmo `supabase_cb` usado por toda a aplicação. Se o health check falha (por qualquer razão), ele registra falhas no circuit breaker, podendo abri-lo e derrubar funcionalidades que estavam funcionando perfeitamente.

**Padrão anti-pattern:** O mecanismo de monitoramento causa o problema que deveria detectar.

**Fluxo observado em produção:**
1. Health canary roda a cada 5 min
2. Tenta `save_health_check()` → `sb_execute(sb.table("health_checks")...)` → PGRST205
3. Tenta `detect_incident()` → `sb_execute(sb.table("incidents")...)` → PGRST205
4. Tenta `cleanup_old_health_checks()` → PGRST205
5. Cada chamada registra failure no `supabase_cb` (shared singleton)
6. Em 2 ciclos de canary (6 erros), CB atinge threshold (50% de 10) → OPEN
7. Toda a aplicação para de acessar Supabase

---

## Solution

Isolar as operações do health canary do circuit breaker principal, usando uma de duas abordagens:

### Opção A — Bypass CB para health checks (Recomendada)
Criar `sb_execute_unchecked()` que acessa Supabase diretamente, sem passar pelo CB. Usar exclusivamente nas operações internas do canary (`save_health_check`, `detect_incident`, `cleanup_old_health_checks`).

### Opção B — CB separado para canary
Criar `health_cb = SupabaseCircuitBreaker()` dedicado ao canary, isolando do `supabase_cb` principal. Mais complexo, menos benefício.

---

## Acceptance Criteria

### Backend — Isolamento do Canary

- [x] **AC1:** Criar função `sb_execute_direct()` em `supabase_client.py` que executa queries Supabase SEM registrar no `supabase_cb`:
  ```python
  async def sb_execute_direct(query) -> dict:
      """Execute Supabase query bypassing circuit breaker.
      Use ONLY for internal health monitoring operations."""
      ...
  ```
- [x] **AC2:** Em `health.py:save_health_check()`: substituir `sb_execute()` por `sb_execute_direct()`
- [x] **AC3:** Em `health.py:detect_incident()`: substituir `sb_execute()` por `sb_execute_direct()`
- [x] **AC4:** Em `health.py:cleanup_old_health_checks()`: substituir `sb_execute()` por `sb_execute_direct()`
- [x] **AC5:** Em `health.py:get_public_status()` — a query `sb.table("profiles").select("id").limit(1)` que verifica se Supabase está vivo DEVE continuar usando `sb_execute()` (é um health probe legítimo)
- [x] **AC6:** Adicionar docstring clara em `sb_execute_direct()`: "NEVER use for user-facing operations"

### Backend — Log Improvement

- [x] **AC7:** Em `save_health_check()`: catch PGRST205 → log WARNING com mensagem "health_checks table not found — migration pending" (não ERROR)
- [x] **AC8:** Em `detect_incident()`: catch PGRST205 → log WARNING (não ERROR)
- [x] **AC9:** Métricas: adicionar label `source="canary"` vs `source="app"` ao `smartlic_supabase_cb_transitions_total` para distinguir origem de failures

### Testes

- [x] **AC10:** Teste: health canary falha 20x consecutivas → `supabase_cb` permanece CLOSED
- [x] **AC11:** Teste: erro de conexão real em query de app → `supabase_cb` abre normalmente
- [x] **AC12:** Teste: `sb_execute_direct()` funciona quando `supabase_cb` está OPEN

---

## Observação

Esta story complementa CRIT-040 (exclude PGRST205 do CB). Mesmo após CRIT-040, o canary ainda pode causar falsos positivos por outros erros (timeout transiente no health check, etc). O isolamento é a solução definitiva.

---

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `backend/supabase_client.py` | Nova função `sb_execute_direct()` |
| `backend/health.py` | Usar `sb_execute_direct()` em 3 funções + log levels |
| `backend/tests/test_supabase_circuit_breaker.py` | Testes de isolamento |
