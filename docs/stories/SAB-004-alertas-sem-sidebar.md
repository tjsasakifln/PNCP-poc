# SAB-004: Página Alertas sem sidebar de navegação

**Origem:** UX Premium Audit P1-01
**Prioridade:** P1 — Alto
**Complexidade:** S (Small)
**Sprint:** SAB-P1
**Owner:** @dev
**Screenshot:** `ux-audit/26-alertas.png`

---

## Problema

A página `/alertas` renderiza em layout full-width SEM a sidebar padrão de navegação. Todas as outras páginas logadas (Buscar, Dashboard, Pipeline, Histórico, Conta) têm sidebar consistente.

**Impacto:** Quebra de consistência de navegação. Usuário "perde" o menu e precisa usar o browser back.

---

## Critérios de Aceite

- [x] **AC1:** Página `/alertas` renderiza com a mesma sidebar de navegação das demais páginas logadas
- [x] **AC2:** Item "Alertas" na sidebar fica highlighted/ativo quando na página `/alertas`
- [x] **AC3:** Layout responsivo: no mobile, sidebar colapsa igual às outras páginas (bottom nav)
- [x] **AC4:** Verificar se `/mensagens` também tem sidebar (se não, incluir no fix) — já tem, confirmado

---

## Arquivos Prováveis

- `frontend/app/alertas/page.tsx` ou `frontend/app/alertas/layout.tsx` — provavelmente falta wrapper de layout
- `frontend/app/layout.tsx` — layout raiz com sidebar
- `frontend/components/Sidebar.tsx` — componente sidebar

## Notas

- Fix provavelmente é apenas envolver a página no layout correto (copiar padrão das outras páginas).
- Verificar se a rota `/alertas` está dentro do grupo de rotas logadas que usa o layout com sidebar.
