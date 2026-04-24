# SEN-BE-004: HTTP/2 ConnectionTerminated + RemoteProtocolError em queries DB

**Status:** Ready
**Origem:** Sentry unresolved — issues 7398298813 (48 evt ConnectionTerminated), 7396815122 (3 evt RemoteProtocolError)
**Prioridade:** P1 — Alto (51 eventos correlacionados, impacta rotas públicas)
**Complexidade:** M (Medium)
**Owner:** @dev + @data-engineer
**Tipo:** Reliability / Infra

---

## Problema

Erros HTTP/2 terminando streams prematuramente durante queries a Supabase:

1. `orgao_stats DB query failed for 02603612000102: <ConnectionTerminated error_code:1, last_stream_id:2875>` — 48 evt em `routes.orgao_publico.orgao_stats`
2. `RemoteProtocolError: Server disconnected` — 3 evt, sem culprit específico

Correlação:
- Mesmo orgao (02603612000102) aparece em múltiplos eventos — pode ser query específica longa
- `last_stream_id:2875` sugere que o stream foi usado bastante antes do kill — conexão reciclada no meio
- `error_code:1` em HTTP/2 = `PROTOCOL_ERROR` — peer enviou frame inválido ou fechou conexão unilateralmente

Hipóteses:
- Supabase pooler (PgBouncer/Supavisor) matando conexão idle
- `httpx` client reuso de conexão expirada após `keepalive_expiry` (default 5s em httpx)
- Correlação com statement_timeout (SEN-BE-001) — query cancelada gera connection reset

---

## Critérios de Aceite

- [ ] **AC1:** Reproduzir localmente: rodar `orgao_stats` para CNPJ `02603612000102` com `HTTPX_LOG_LEVEL=DEBUG` e capturar trace até ConnectionTerminated — documentar em `docs/investigation/SEN-BE-004.md`
- [ ] **AC2:** Auditar configuração httpx em `backend/supabase_client.py`: verificar `keepalive_expiry`, `max_keepalive_connections`, `http2=True/False`. Considerar `http2=False` se HTTP/2 for a causa (simplificar pool)
- [ ] **AC3:** Implementar retry com jitter (exponencial, max 3 tentativas) para `ConnectionTerminated` e `RemoteProtocolError` em `backend/supabase_client.py::sb_execute`
- [ ] **AC4:** Teste unitário mock httpx para disparar ConnectionTerminated na primeira tentativa, confirmar retry succeed na 2ª
- [ ] **AC5:** Métrica Prometheus nova: `smartlic_supabase_connection_reset_total{operation}` — incrementar em cada retry
- [ ] **AC6:** Sentry issues `7398298813` e `7396815122` reduzem para <5 eventos/semana após fix

### Anti-requisitos

- NÃO desabilitar pool — cria N new connections per req
- NÃO aumentar `max_keepalive` sem medir — muita conexão idle satura pool do Supabase

---

## Referência de implementação

Arquivos prováveis:
- `backend/supabase_client.py` — cliente httpx + sb_execute
- `backend/routes/orgao_publico.py::orgao_stats`
- `backend/redis_pool.py` — padrão de retry já existe, replicar

---

## Riscos

- **R1 (Alto):** Retry pode mascarar query realmente lenta (SEN-BE-001) — coordenar com aquela story, retry só aplica a ConnectionTerminated, NÃO a 57014
- **R2 (Médio):** `http2=False` pode aumentar latência marginal — medir antes de decidir
- **R3 (Baixo):** Retry em mutation (write) pode duplicar — só aplicar retry em reads ou em mutations idempotentes

## Dependências

- SEN-BE-001 (statement_timeout) — investigar se ConnectionTerminated é efeito colateral
- SEN-BE-003 (circuit breaker) — ConnectionTerminated contribui para breaker trip

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-23 | @sm | Story criada — 2 issues correlacionadas, 51 eventos |
| 2026-04-23 | @po | Validação 10/10 → **GO**. LIVE (lastSeen 2026-04-20). Promovida Draft → Ready |
