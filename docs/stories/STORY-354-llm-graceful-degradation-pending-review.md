# STORY-354: LLM graceful degradation — eliminar "oportunidades invisíveis" por outage

**Prioridade:** P0
**Tipo:** fix
**Sprint:** Sprint 1
**Estimativa:** XL
**Origem:** Conselho CTO Advisory Board — Auditoria de Promessas (2026-03-01)
**Dependências:** Nenhuma
**Bloqueado por:** —
**Bloqueia:** —
**Paralelo com:** STORY-351

---

## Contexto

O SmartLic promete "Nenhuma oportunidade invisível". Porém, quando OpenAI está indisponível, `llm_arbiter.py:792` aplica fallback = REJECT para bids com 0% keyword density. Isso descarta silenciosamente oportunidades legítimas que dependiam de classificação LLM (zero-match). O usuário nunca sabe que perdeu oportunidades.

## Promessa Afetada

> "Nenhuma oportunidade invisível"
> "Se uma licitação compatível com seu perfil é publicada em qualquer lugar do Brasil, você sabe."

## Causa Raiz

LLM fallback = REJECT (`llm_arbiter.py:789-800`) significa que durante outage OpenAI, bids com 0% keyword density são silenciosamente descartadas. O usuário não sabe que perdeu oportunidades. Timeout chain (Pipeline 110s) pode truncar resultados adicionalmente.

## Critérios de Aceite

- [x] AC1: Quando LLM falhar (timeout, rate limit, outage), classificar bids zero-match como `PENDING_REVIEW` (novo status) em vez de REJECT
- [x] AC2: Adicionar campo `pending_review_count` ao response schema (`BuscaResponse` em `schemas.py`)
- [x] AC3: No frontend, exibir banner informativo: "{X} oportunidades aguardam reclassificação (IA temporariamente indisponível)" — cor azul (info), não vermelho (erro)
- [x] AC4: Criar ARQ job `reclassify_pending_bids(search_id)` que re-processa bids pendentes quando LLM voltar
- [x] AC5: Prometheus counter `smartlic_llm_fallback_pending_total` (labels: sector, reason) para medir frequência de fallback
- [x] AC6: SSE event `pending_review` para atualizar frontend em tempo real quando reclassificação completar
- [x] AC7: Limite de retenção: bids PENDING_REVIEW expiram em 24h (não poluir resultados indefinidamente)
- [x] AC8: Feature flag `LLM_FALLBACK_PENDING_ENABLED` (default: true) para rollback seguro
- [x] AC9: Testes unitários: mock OpenAI down → bids não são perdidas, contagem de pending correta
- [x] AC10: Teste de integração: OpenAI volta → ARQ job reclassifica → SSE notifica frontend

## Arquivos Afetados

- `backend/llm_arbiter.py`
- `backend/schemas.py`
- `backend/search_pipeline.py`
- `backend/job_queue.py`
- `backend/progress.py`
- `backend/config.py`
- `backend/metrics.py`
- `frontend/app/buscar/components/SearchResults.tsx`
- `frontend/app/buscar/hooks/useSearch.ts`

## Validação

| Métrica | Threshold | Onde medir |
|---------|-----------|------------|
| `smartlic_llm_fallback_pending_total` / semana | <5% do total de classificações | Prometheus |
| Bids perdidas por outage LLM | 0 (zero perda) | Integration tests |

## Notas

- Esta é a story mais complexa (XL). Toca backend (LLM, pipeline, ARQ, SSE) e frontend.
- O status PENDING_REVIEW é um novo conceito — precisa de schema update + frontend rendering.
- Não alterar a copy "Nenhuma oportunidade invisível" — corrigir o sistema para que a promessa seja verdadeira.
