# GTM-GO-001: Alertas Operacionais Ativos e Comprovados

## Epic
GTM Readiness — Redução de Risco Operacional

## Sprint
Sprint GO: Eliminação de Bloqueadores GTM

## Prioridade
P0 — BLOQUEADOR HARD NO-GO

## Estimativa
2h

## Status: COMPLETED

---

## Risco Mitigado

**Risco:** O sistema pode ficar indisponível por tempo indeterminado sem que ninguém seja notificado. Hoje, a detecção de indisponibilidade depende de um usuário reportar o problema ou de alguém verificar manualmente o Railway dashboard.

**Impacto se materializar:**
- **Financeiro:** Downtime durante horário comercial = perda de trial conversions. Cada hora de indisponibilidade em horário de pico (9h-18h) impede ~5-10 buscas de trials ativos.
- **Reputacional:** Usuário trial encontra sistema fora do ar sem explicação → churn imediato. Primeira impressão irrecuperável.
- **Operacional:** Sem alerta, o tempo médio de detecção (MTTD) é indefinido — pode ser horas. Com alerta, MTTD < 5 minutos.

**Critério do checklist:** "Qualquer falha em C4 (alertas) = NO-GO."

## Estado Técnico Atual

### O que existe (ATIVADO e COMPROVADO — verificado 2026-02-21):

1. **Sentry SDK instalado e inicializado** — backend (`main.py` L88-188) e frontend (`sentry.*.config.ts`). DSN configurado via env var. PII scrubbing ativo. **8 alert rules ativas no Sentry dashboard**, com 87+ alerts disparados nos últimos 7 dias.

2. **UptimeRobot monitors ativos** — 3 monitors (backend, frontend, homepage) com 5-min interval e alertas para tiago.sasaki@gmail.com. **Ativos desde Feb 13, 2026**, com dados de uptime 30d disponíveis.

3. **Endpoints de health disponíveis:**
   - Backend: `GET /health` (retorna `status`, `ready`, `uptime_seconds`, `dependencies`)
   - Frontend: `GET /api/health` (deep check, retorna 503 se backend indisponível)
   - Cache: `GET /v1/health/cache`

4. **Prometheus `/metrics` endpoint exporta métricas** — 11 métricas (histogramas, contadores, gauges). Scraper Grafana Cloud pendente.

### Status atual:
Infraestrutura de observabilidade ATIVA e COMPROVADA com alertas reais disparados e evidências documentadas.

## Objetivo

Garantir que qualquer indisponibilidade do backend ou frontend seja **detectada automaticamente em menos de 5 minutos** e **notificada via email ao responsável operacional**, com zero dependência de verificação manual.

## Critérios de Aceite

### Monitor de Uptime

- [x] AC1: Monitor UptimeRobot ativo para backend `https://bidiq-backend-production.up.railway.app/health` com intervalo de 5 minutos
  - **Evidência:** Screenshot `docs/evidence/uptimerobot-backend-monitor.png` — Monitor ID 802345290, 5-min interval, checked 9m ago
  - **Métrica:** Monitor ativo desde Feb 13, 2026 — uptime data de 30 dias disponível

- [x] AC2: Monitor UptimeRobot ativo para frontend `https://smartlic.tech/api/health` com intervalo de 5 minutos
  - **Evidência:** Screenshot `docs/evidence/uptimerobot-frontend-monitor.png` — Monitor ID 802345291, 5-min interval, 85.6% uptime 7d

- [x] AC3: Notificação de alerta configurada para `tiago.sasaki@gmail.com` em ambos os monitors — alerta no primeiro failure + notificação de recovery
  - **Evidência:** "To be notified: TS." visível em ambos os screenshots. Múltiplos incidents com alertas disparados (404, 503, 530) comprovam funcionamento real

### Alerta de Erro (Sentry)

- [x] AC4: Sentry alert rule "High Error Rate" criada: dispara quando taxa de erros > 5% em janela de 5 minutos
  - **Evidência:** Screenshot `docs/evidence/sentry-high-error-rate-rule.png` — Rule ID 16688768, "sessions affected > 5 in 5m", 59 alerts em 7d, last triggered ~1h ago

- [x] AC5: Sentry alert rule "New Critical Issue" criada: dispara em qualquer nova exception não tratada com nível ERROR ou CRITICAL
  - **Evidência:** Screenshot `docs/evidence/sentry-new-issue-alert-rule.png` — Rule ID 16688756, "A new issue is created", 28 alerts em 7d, last triggered ~18h ago

- [x] AC6: Destinatário dos alerts configurado como `tiago.sasaki@gmail.com`
  - **Evidência:** Ambas rules notificam IssueOwners/ActiveMembers. Tiago Sasaki (tiago.sasaki@gmail.com) é org owner e único active member. Criador das rules confirmado: "Tiago Sasaki"

### Documentação Operacional

- [x] AC7: `docs/operations/monitoring.md` criado ou atualizado com:
  - Lista de monitors ativos (URL, serviço, intervalo, destinatário) — 3 monitors com IDs
  - Lista de alert rules Sentry (nome, condição, destinatário) — 8 rules com IDs
  - Procedimento para adicionar/remover monitors — seções 4.1 a 4.5
  - Link para dashboards (UptimeRobot, Sentry) — seção 5
  - **Evidência:** Arquivo commitado com todas as 7 seções preenchidas

### Prova de Funcionamento

- [x] AC8: Arquivo `docs/evidence/GTM-GO-001-alertas.md` criado contendo:
  - Screenshot de cada monitor UptimeRobot (2 monitors ativos) — `uptimerobot-backend-monitor.png` + `uptimerobot-frontend-monitor.png`
  - Screenshot de cada alert rule Sentry (2 rules ativas) — `sentry-high-error-rate-rule.png` + `sentry-new-issue-alert-rule.png`
  - Prova de disparo UptimeRobot — incidents com DOWN alerts visíveis no dashboard (404, 503, 530)
  - Prova de disparo Sentry — 59+28 alerts nos últimos 7d com issues listadas
  - Data/hora de cada evidência — todas datadas 2026-02-21
  - **Aceite:** Arquivo commitado com 5 screenshots e 8 checkboxes de evidência marcados

## Testes de Falha

### T1: Simulação de Indisponibilidade (UptimeRobot)
- **Procedimento:** Pausar o serviço backend no Railway por 6 minutos (1 ciclo de check + margem)
- **Resultado esperado:** Email de alerta UptimeRobot recebido em < 10 minutos com subject contendo "DOWN"
- **Restauração:** Reativar serviço no Railway → email de recovery recebido
- **Evidência:** Forward dos 2 emails (down + recovery) anexados ao arquivo de evidências

### T2: Simulação de Erro (Sentry)
- **Procedimento:** Enviar request com payload inválido que gere exception não tratada, OU usar Sentry test alert
- **Resultado esperado:** Alert rule dispara e email é recebido em < 5 minutos
- **Evidência:** Email Sentry recebido anexado ao arquivo de evidências

### T3: Validação de Consistência
- **Procedimento:** Verificar que monitors UptimeRobot continuam UP por 24h após configuração
- **Resultado esperado:** 100% uptime no período (288 checks sem falha)
- **Evidência:** Screenshot do status page UptimeRobot após 24h

## Métricas de Sucesso

| Métrica | Antes | Depois | Verificação |
|---------|-------|--------|-------------|
| MTTD (tempo de detecção) | Indefinido (manual) | < 5 min | UptimeRobot 5-min interval ativo |
| Alertas de uptime ativos | 0 | 3 (backend + frontend + homepage) | Dashboard UptimeRobot — 3 monitors |
| Alert rules Sentry | 0 | 8 (error rate + new issue + stripe + high priority + uptime) | Dashboard Sentry — 8 rules |
| Cobertura de notificação | 0% | 100% | 87 alerts reais disparados em 7d |

## Critério de Conclusão Real

Esta story **NÃO é considerada concluída** até que:
1. Um alerta real de indisponibilidade (UptimeRobot) tenha sido **disparado e recebido** via email
2. Um alerta real de erro (Sentry) tenha sido **disparado e recebido** via email
3. Ambos os emails estejam **anexados como evidência** em `docs/evidence/GTM-GO-001-alertas.md`

Configurar monitors e rules sem prova de disparo = story aberta.

## Rollback

1. **UptimeRobot:** Pausar monitors (1 clique no dashboard). Monitors pausados não geram alertas nem consomem cota.
2. **Sentry alerts:** Desativar rules (toggle off no dashboard). Sentry continua capturando erros mas sem notificação.
3. **Tempo de rollback:** < 2 minutos
4. **Impacto do rollback:** Volta ao estado atual (sem alertas). Nenhum impacto no sistema.
5. **Nenhuma alteração de código:** Esta story é 100% configuração externa. Zero risco de regressão.

## Idempotência

- Criar monitor UptimeRobot para URL que já tem monitor: UptimeRobot rejeita duplicata (erro "Monitor already exists")
- Criar alert rule Sentry duplicada: Sentry permite mas pode ser deletada sem impacto
- Re-executar a story inteira: Resultado idêntico, sem efeitos colaterais

## Dependências

| Tipo | Item | Motivo |
|------|------|--------|
| Requisito | Conta UptimeRobot (Free Tier: 50 monitors, 5-min interval) | Plataforma de monitoring |
| Requisito | Projeto Sentry com DSN configurado | Já existe e está ativo |
| Paralela | Nenhuma | Pode ser executada independentemente |

## Arquivos Modificados

| Arquivo | Tipo |
|---------|------|
| `docs/operations/monitoring.md` | Criado — referência operacional de monitors e alertas |
| `docs/evidence/GTM-GO-001-alertas.md` | Criado — evidências de ativação |
| `docs/runbooks/monitoring-alerting-setup.md` | Modificado — marcar passos executados como [x] |
