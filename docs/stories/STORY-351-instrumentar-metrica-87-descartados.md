# STORY-351: Instrumentar e validar métrica "87% descartados"

**Prioridade:** P0
**Tipo:** feature (observabilidade) + fix (copy condicional)
**Sprint:** Sprint 1
**Estimativa:** L
**Origem:** Conselho CTO Advisory Board — Auditoria de Promessas (2026-03-01)
**Dependências:** Nenhuma
**Bloqueado por:** —
**Bloqueia:** —
**Paralelo com:** STORY-354

---

## Contexto

O número "87% dos editais descartados" aparece em 6+ locais na UI (HeroSection, StatsSection, comparisons.ts, valueProps.ts). Não existe nenhum Prometheus counter, logging estruturado, ou dashboard que meça o discard rate real. O número não tem origem.

## Promessa Afetada

> "87% dos editais descartados antes de chegar até você"

## Causa Raiz

Número arbitrário exibido como fato. Zero infraestrutura de medição. O pipeline de filtragem funciona (2.549 regras em sectors_data.yaml), mas o ratio real nunca foi medido.

## Critérios de Aceite

- [ ] AC1: Adicionar Prometheus counter `smartlic_filter_input_total` e `smartlic_filter_output_total` (labels: sector, source) em `filter.py`
- [ ] AC2: Adicionar Prometheus histogram `smartlic_filter_discard_rate` (ratio = 1 - output/input) em `search_pipeline.py` ao final do estágio filter
- [ ] AC3: Criar endpoint `GET /v1/metrics/discard-rate` que retorna a média móvel de 30 dias do discard rate por setor
- [ ] AC4: No frontend, substituir "87%" hardcoded por valor dinâmico do endpoint (com fallback para "a maioria" se API falhar)
- [ ] AC5: Se discard rate real < 87%, tunar pipeline de filtragem (keywords, exclusões em sectors_data.yaml) para atingir target — a copy é o objetivo, o sistema se adapta
- [ ] AC6: Atualizar `StatsSection.tsx` para renderizar valor dinâmico com loading state
- [ ] AC7: Atualizar testes de `StatsSection.test.tsx` para mock do novo endpoint
- [ ] AC8: Adicionar o número exato ao Grafana dashboard com alerta se discard rate cair abaixo de 70%
- [ ] AC9: Log estruturado: `{"event": "filter_stats", "input": N, "output": M, "discard_rate": X, "sector": "...", "search_id": "..."}`

## Arquivos Afetados

- `backend/filter.py`
- `backend/filter_stats.py`
- `backend/search_pipeline.py`
- `backend/metrics.py`
- `backend/routes/analytics.py`
- `frontend/app/components/landing/StatsSection.tsx`
- `frontend/lib/copy/valueProps.ts`
- `frontend/__tests__/landing/StatsSection.test.tsx`

## Validação

| Métrica | Threshold | Onde medir |
|---------|-----------|------------|
| `smartlic_filter_discard_rate` média 30d | >70% para claim "a maioria" | Prometheus/Grafana |
| Log estruturado `filter_stats` | Emitido para cada busca | Railway logs |

## Notas

- Após 30 dias de coleta, revisar se "87%" é próximo da realidade e atualizar copy de acordo.
- Se rate real for >85%, pode voltar a usar número exato (agora verificável).
