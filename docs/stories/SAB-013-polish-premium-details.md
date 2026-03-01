# SAB-013: Polish premium — animações, hover states e detalhes

**Origem:** UX Premium Audit P3-02, P3-03, P3-05
**Prioridade:** P3 — Baixo
**Complexidade:** S (Small)
**Sprint:** SAB-P3 (backlog)
**Owner:** @dev
**Screenshots:** `ux-audit/15-busca-clean.png`, `ux-audit/30-dark-mode.png`

---

## Problema

Detalhes de polish que separam um produto funcional de um produto premium:

### P3-02: Sidebar sem hover states claros
Items da sidebar têm highlight no ativo (azul) mas hover sutil demais, sem transição suave.

### P3-03: Filtros de busca collapsed por default
"Personalizar busca" sempre começa fechado. Usuários recorrentes precisam expandir toda vez.

### P3-05: Footer redundante na área logada
Footer com links "Sobre", "Planos", "Central de Ajuda" duplica informação já presente na sidebar.

---

## Critérios de Aceite

### Sidebar Hover (P3-02)

- [x] **AC1:** Adicionar `transition: background-color 150ms ease` em items da sidebar
- [x] **AC2:** Hover state mais visível: `bg-gray-100` (light) / `bg-gray-800` (dark)
- [x] **AC3:** Active item com left border accent (4px azul) além do background

### Filtros Persistentes (P3-03)

- [x] **AC4:** Salvar estado do accordion "Personalizar busca" no `localStorage`
- [x] **AC5:** Se usuário já expandiu antes, manter aberto no próximo acesso
- [x] **AC6:** Key do localStorage: `smartlic:buscar:filters-expanded`

### Footer Simplificado (P3-05)

- [x] **AC7:** Na área logada: footer reduzido a uma linha: "© 2026 SmartLic · Termos · Privacidade"
- [x] **AC8:** Na área pública (landing, login, signup): manter footer completo

---

## Arquivos Prováveis

- `frontend/components/Sidebar.tsx` — hover states
- `frontend/app/buscar/page.tsx` ou `FilterPanel.tsx` — accordion persistence
- `frontend/components/Footer.tsx` — footer condicional

## Notas

- P3-01 (stats counter FOUC) foi absorvido por SAB-006 (landing page condensar).
- Estas são melhorias incrementais que podem ser feitas em qualquer sprint quando houver tempo.
