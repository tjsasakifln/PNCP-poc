# UX-431: Dashboard mostra dados desatualizados da ultima busca

**Status:** Draft
**Prioridade:** P0 — Critico
**Origem:** UX Audit 2026-03-25 (C5)
**Sprint:** Proximo

## Contexto

Dashboard mostra "6 oportunidades na sua ultima busca" mas a busca mais recente retornou 394 resultados. O card parece referenciar uma busca anterior (a de 6 resultados feita as 09:57, nao a de 394 feita as ~10:00).

## Acceptance Criteria

- [ ] AC1: Card "ultima busca" deve refletir a busca mais recente com status Concluida
- [ ] AC2: Se busca mais recente deu timeout/falhou, mostrar ultima busca bem-sucedida
- [ ] AC3: Verificar query de busca mais recente — ORDER BY created_at DESC LIMIT 1
- [ ] AC4: Considerar se a busca de 394 foi salva no banco (pode ter falhado no save por ser grande)

## Arquivos Provaveis

- `frontend/app/dashboard/page.tsx` — fetch de ultima busca
- `backend/routes/analytics.py` — endpoint de summary/ultima busca
- `backend/search_cache.py` — persistencia de resultados

## Screenshot

`ux-audit/08-dashboard.png`
