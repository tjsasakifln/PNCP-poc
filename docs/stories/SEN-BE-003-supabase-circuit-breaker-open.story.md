# SEN-BE-003: Supabase circuit breaker OPEN em produção + PNCP health degraded/unhealthy

**Status:** Ready
**Origem:** Sentry unresolved — issues 7402940322 (4 evt DLQ scan fail), 7323248631 (2 evt fatal STARTUP GATE), 7355911985 (713 evt degraded), 7400220880 (3 evt unhealthy)
**Prioridade:** P0 — Crítico (fatal na startup gate, 713 eventos de health degraded em 14d)
**Complexidade:** M (Medium)
**Owner:** @dev + @devops
**Tipo:** Reliability / Observability

---

## Problema

Quatro issues correlacionadas indicam instabilidade estrutural na conexão backend ↔ Supabase + health da fonte PNCP:

1. **STORY-418 — DLQ scan failed: Supabase circuit breaker[read] is OPEN — sb_execute rejected** (4 evt) — job de DLQ scan aborta pois CB já está em fail-open
2. **STARTUP GATE: Supabase unreachable — Server disconnected. SERVICE DEGRADED but staying alive** (level=fatal, 2 evt) — backend sobe em modo degradado na inicialização
3. **Health incident: System status changed to degraded. Affected: pncp** (warning, **713 eventos** em 14d) — PNCP é flagada como degraded várias vezes ao dia
4. **Health incident: System status changed to unhealthy. Affected: pncp** (error, 3 evt) — escala para unhealthy em picos

Impacto:
- DLQ scan não processa retries — mensagens enfileiradas ficam paradas
- Startup fatal é silenciado ("staying alive") — monitoramento externo pode não pegar a falha inicial
- 713 degraded warnings sinalizam que o circuit breaker está sendo acionado ~51x/dia em média — ou threshold muito apertado ou PNCP tem instabilidade real

---

## Critérios de Aceite

- [ ] **AC1:** Análise documentada em `docs/investigation/SEN-BE-003-cb-analysis.md`: baseline de disponibilidade real do PNCP upstream (consultar status page ou medir via canary)
- [ ] **AC2:** Revisar thresholds do circuit breaker `backend/pncp_client.py` (hoje: 15 failures / 60s cooldown). Ajustar se necessário, documentar decisão
- [ ] **AC3:** Job `dlq_scan` NÃO deve falhar por `CB OPEN` — deve fazer skip gracioso com log INFO (não ERROR). Criar teste unitário em `backend/tests/test_dlq_scan_cb_open.py`
- [ ] **AC4:** STARTUP GATE fatal deve ter retry exponencial (3 tentativas, 5/10/20s) ANTES de entrar em "staying alive" — evita falha transitória de deploy virar incident. `backend/main.py::startup_supabase_gate`
- [ ] **AC5:** Alert Sentry configurado: rate `smartlic_pncp_breaker_open_total` > 3/hora dispara pagerduty (fora do padrão esperado de intermitência)
- [ ] **AC6:** Issues `7402940322`, `7323248631`, `7355911985`, `7400220880` resolvidos ou reduzidos a <10 eventos/semana após fix

### Anti-requisitos

- NÃO remover circuit breaker — proteção contra cascading failure é essencial
- NÃO converter STARTUP GATE em hard-fail sem retry — causaria flapping em deploys

---

## Referência de implementação

Arquivos prováveis:
- `backend/pncp_client.py` — thresholds CB
- `backend/main.py::startup_supabase_gate` — fatal handler
- `backend/jobs/dlq_scan.py` — skip on CB open
- `backend/health.py` — lógica de degraded/unhealthy

Métrica existente: `smartlic_pncp_breaker_open_total` (Prometheus)

---

## Riscos

- **R1 (Alto):** Afrouxar threshold esconde problema real do PNCP — medir baseline antes
- **R2 (Médio):** Retry no STARTUP GATE atrasa deploy se Supabase estiver genuinamente down — cap em 40s total (3 retries)
- **R3 (Baixo):** Alerta `>3/hora` pode ser ruidoso durante incidentes PNCP legítimos — começar em 5/hora, calibrar

## Dependências

- SEN-BE-004 (ConnectionTerminated) — provavelmente mesma causa-raiz Supabase
- Acesso a métricas Prometheus para calibrar thresholds

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-23 | @sm | Story criada — 4 issues correlacionadas, 722 eventos combinados |
| 2026-04-23 | @po | Validação 10/10 → **GO**. LIVE (health events lastSeen 2026-04-22). Promovida Draft → Ready |
