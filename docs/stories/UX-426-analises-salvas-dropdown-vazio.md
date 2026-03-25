# UX-426 — "Análises Salvas" Dropdown sem Feedback de Estado Vazio

**Status:** Draft
**Severity:** LOW
**Origin:** Auditoria UX Playwright 25/03/2026
**Agent:** @ux-design-expert (Uma)

## Problema

Botão "Análises Salvas" existe no header da página de busca mas pode estar sem conteúdo, sem indicação visual de que não há análises salvas ainda. Novo botão "Salvar Análise" aparece após busca, mas relação entre salvar e acessar não é clara.

## Acceptance Criteria

- [ ] AC1: Dropdown "Análises Salvas" mostra estado vazio com texto explicativo quando não há análises salvas
- [ ] AC2: Após salvar uma análise, dropdown mostra a análise recém-salva
- [ ] AC3: Tooltip ou hint no botão "Salvar Análise" explica que a análise aparecerá em "Análises Salvas"
