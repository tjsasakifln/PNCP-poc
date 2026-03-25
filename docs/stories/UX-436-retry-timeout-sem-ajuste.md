# UX-436: Retry de timeout repete mesma busca sem ajuste

**Status:** Draft
**Prioridade:** P1 — Importante
**Origem:** UX Audit 2026-03-25 (I5)
**Sprint:** Proximo

## Contexto

Quando uma busca da timeout, o botao "Tentar novamente" repete exatamente os mesmos parametros (mesmas 4 UFs). Alta probabilidade de falhar novamente no mesmo limite.

## Acceptance Criteria

- [ ] AC1: Retry deve sugerir reducao de UFs ("Buscar apenas SP e SC?") ou auto-otimizar
- [ ] AC2: Alternativa: retry com timeout extendido + banner "Aguardando mais tempo..."
- [ ] AC3: Mostrar quais UFs completaram antes do timeout para informar decisao
- [ ] AC4: Se 2 retries falharam, oferecer busca por UF individual

## Arquivos Provaveis

- `frontend/app/buscar/page.tsx` — logica de retry
- `frontend/app/buscar/components/` — componente de erro/retry
