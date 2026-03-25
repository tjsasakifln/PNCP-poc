# UX-414 — Tour Guiado Aparece Sobre Estado de Erro

**Status:** Done
**Severity:** CRITICAL
**Origin:** Auditoria UX Playwright 25/03/2026
**Agent:** @ux-design-expert (Uma)

## Problema

Na página Pipeline, o onboarding tour (Shepherd.js) exibe "Kanban de oportunidades — Passo 1 de 3" sobreposto à mensagem de erro "Não foi possível carregar seu pipeline". Console mostra: "The element for this Shepherd step was not found".

## Impacto

Experiência absurda: tutorial ensinando a usar feature que está quebrada. Destrói credibilidade.

## Evidências

- Screenshot: `ux-audit-pipeline.png`
- Console error: "The element for this Shepherd step was not found"

## Acceptance Criteria

- [x] AC1: Tour NÃO inicia se Pipeline falhou ao carregar (verificar estado de erro antes de ativar Shepherd)
- [x] AC2: Tour só inicia quando kanban board está renderizado e com dados
- [x] AC3: Se Pipeline está vazio (0 itens, sem erro), tour pode iniciar com step adaptado ("Adicione licitações via busca")
- [x] AC4: Shepherd step com elemento não encontrado deve silenciar, não crashar

## File List

- [x] `frontend/app/pipeline/` — componente Pipeline, lógica do tour
- [x] Shepherd.js configuração — verificar `beforeShowPromise` ou `showOn` conditions
