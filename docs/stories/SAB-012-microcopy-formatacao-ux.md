# SAB-012: Microcopy, formatação monetária e UX login/mobile

**Origem:** UX Premium Audit P2-05, P2-06, P2-07, P2-08
**Prioridade:** P2 — Médio
**Complexidade:** M (Medium)
**Sprint:** SAB-P2
**Owner:** @dev
**Screenshots:** `ux-audit/24-historico.png`, `ux-audit/22-dashboard.png`, `ux-audit/31-mobile-busca.png`, `ux-audit/10-login-page.png`

---

## Problema

Quatro issues de polimento:

### P2-05: Tempo de busca exposto
Histórico mostra tempos de busca (39.8s, 93.8s). Tempos de 90+ segundos transmitem lentidão.

### P2-06: Formatação monetária inconsistente
Dashboard usa formato americano "R$ 3495.1M" em vez de PT-BR "R$ 3,5 bi" ou "R$ 3.495,1 mi".

### P2-07: Mobile bottom nav truncado
Bottom nav em 375px: "Histórico" fica apertado, "Msg" é abreviação não óbvia.

### P2-08: Login sem hierarquia visual
Login oferece Google OAuth + Email/Senha + Magic Link no mesmo nível visual, sem destaque no método preferido.

---

## Critérios de Aceite

### Tempo de Busca (P2-05)

- [x] **AC1:** Esconder tempo de busca quando > 60s. Substituir por label "Análise profunda" com ícone.
- [x] **AC2:** Mostrar tempo apenas quando < 30s (como diferencial de velocidade)
- [x] **AC3:** Tempo nunca visível no card — apenas no detail view se usuário expandir

### Formatação Monetária (P2-06)

- [x] **AC4:** Criar helper `formatCurrencyBR(value: number)` que formata em PT-BR: "R$ 3,5 bi", "R$ 130,7 mi", "R$ 45.000"
- [x] **AC5:** Aplicar formatação PT-BR em TODOS os valores monetários do Dashboard
- [x] **AC6:** Aplicar formatação PT-BR nos valores do Histórico

### Mobile Bottom Nav (P2-07)

- [ ] **AC7:** Bottom nav 375px: usar apenas ícones (sem labels) com tooltips no long-press
- [x] **AC8:** OU: abreviar consistentemente — "Busca | Pipeline | Hist. | Msgs | Mais"
- [x] **AC9:** Testar em viewport 375px que nenhum label fica cortado

### Login Hierarquia (P2-08)

- [x] **AC10:** Google OAuth como botão primary: full-width, acima dos demais, cor destacada
- [x] **AC11:** Divider visual "ou continue com email" após Google
- [x] **AC12:** Email/senha e magic link como secundários (menor destaque visual)

---

## Arquivos Prováveis

- `frontend/app/historico/page.tsx` — tempo de busca
- `frontend/app/dashboard/page.tsx` — formatação monetária
- `frontend/components/BottomNav.tsx` ou `MobileNav.tsx` — navegação mobile
- `frontend/app/login/page.tsx` — hierarquia de login
- `frontend/lib/utils.ts` ou similar — helper de formatação

## Notas

- O helper `formatCurrencyBR` pode ser reutilizado em todo o app. Verificar se já existe algo similar antes de criar.
