# Story UX-310: Mensagens de Erro Acionáveis (Não Genéricas)

**Epic:** EPIC-UX-PREMIUM-2026-02
**Priority:** 🟠 P1
**Story Points:** 5 SP
**Owner:** @dev

## Problem
Erros genéricos sem contexto ou ação clara. Ex: "Não foi possível processar sua busca".

## Acceptance Criteria
- [ ] Mapeamento de todos os códigos de erro HTTP
- [ ] Mensagens específicas por tipo de erro
- [ ] Sempre incluir ação sugerida
- [ ] Link para suporte quando aplicável
- [ ] Telemetria de tipos de erro (Sentry)

## Error Map
- 400: "Parâmetros inválidos" + mostrar quais
- 422: "Data em formato incorreto" + exemplo correto
- 500: "Erro no servidor" + botão "Relatar problema"
- 524: "Timeout" + sugestões (já em UX-301)

**Files:** `utils/errorMessages.ts`, `app/buscar/page.tsx`
