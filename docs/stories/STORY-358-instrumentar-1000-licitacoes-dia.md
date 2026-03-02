# STORY-358: Instrumentar e validar claim "1000+ licitações/dia"

**Prioridade:** P2
**Tipo:** feature (observabilidade)
**Sprint:** Sprint 3
**Estimativa:** M
**Origem:** Conselho CTO Advisory Board — Auditoria de Promessas (2026-03-01)
**Dependências:** Nenhuma
**Bloqueado por:** —
**Bloqueia:** —
**Paralelo com:** STORY-353, STORY-359, STORY-360

---

## Contexto

A InstitutionalSidebar exibe "1000+ licitações/dia" sem fonte de dados. PNCP publica milhares/dia, mas o volume processado pelo SmartLic nunca foi medido.

## Promessa Afetada

> "1000+ licitações/dia"

## Causa Raiz

Número exibido na sidebar sem fonte de dados. Pode ser verdade (PNCP publica milhares/dia), mas não é medido.

## Critérios de Aceite

- [ ] AC1: Criar Prometheus counter `smartlic_bids_processed_total` (labels: source, date) incrementado no pipeline de busca
- [ ] AC2: Criar cron job diário que registra contagem de bids processados nas últimas 24h
- [ ] AC3: Criar endpoint `GET /v1/metrics/daily-volume` retornando média de bids/dia dos últimos 30 dias
- [ ] AC4: No frontend, substituir "1000+" hardcoded por valor dinâmico (com fallback "centenas" se API falhar)
- [ ] AC5: Se volume processado < 1000/dia, investigar causa raiz e otimizar throughput do pipeline para atingir target — a copy é o objetivo, o sistema se adapta
- [ ] AC6: Testes do endpoint e do cron job

## Arquivos Afetados

- `backend/metrics.py`
- `backend/cron_jobs.py`
- `backend/routes/analytics.py`
- `frontend/app/components/InstitutionalSidebar.tsx`

## Validação

| Métrica | Threshold | Onde medir |
|---------|-----------|------------|
| `smartlic_bids_processed_total` / dia | >500 para claim "centenas/dia" | Prometheus |
