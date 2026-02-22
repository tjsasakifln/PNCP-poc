# UX-337 — Sidebar de Navegacao Persistente na Area Logada

**Tipo:** Feature / UX Critico
**Prioridade:** Critica (C2 + C3 + M1 da auditoria UX 2026-02-22)
**Criada:** 2026-02-22
**Status:** Pendente
**Origem:** Auditoria UX — Persona "Seu Carlos" (gestor PME 60 anos, interior BR)

---

## Problema

Atualmente, a area logada do SmartLic nao possui navegacao visivel. O unico mecanismo de navegacao e um avatar circular (letra do nome) no canto superior direito, que ao ser clicado revela um dropdown com links para Dashboard, Pipeline, Historico, Mensagens, etc.

### Impacto Real

- Usuario de 60 anos nao descobre que existem Dashboard, Pipeline, Historico
- Avatar circular sem label parece botao de perfil, nao menu de navegacao
- Paginas internas (Historico, Conta) nao tem header padrao — usuario fica "preso"
- Taxa de descoberta de features alem da busca tende a zero para usuarios menos digitais

### Evidencias

- Screenshot `ux-audit-04-buscar.png` — nenhuma navegacao visivel
- Screenshot `ux-audit-10-user-menu.png` — menu oculto atras do avatar "T"
- Screenshot `ux-audit-09-historico.png` — pagina sem header de app
- Screenshot `ux-audit-14-mobile-buscar.png` — mobile sem navegacao

---

## Solucao Proposta

### Desktop (>= 1024px)

Sidebar colapsavel a esquerda com icones + labels:

```
[Logo SmartLic]
─────────────────
🔍  Buscar
📊  Dashboard
📋  Pipeline
📜  Historico
💬  Mensagens
─────────────────
👤  Minha Conta
❓  Ajuda
🚪  Sair
```

- Default: expandida (200px)
- Toggle para colapsar (so icones, 56px)
- Highlight do item ativo
- Badge de contagem em Mensagens (se houver nao-lidas)

### Mobile (< 1024px)

Bottom navigation bar (padrao Android/iOS):

```
[ 🔍 Buscar ] [ 📋 Pipeline ] [ 📜 Historico ] [ 💬 Msg ] [ 👤 Mais ]
```

- 5 itens fixos no rodape
- "Mais" abre drawer com links restantes
- Icone + micro-label (texto pequeno abaixo)

### Header Padrao

Todas as paginas internas devem ter o header com:
- Logo SmartLic (link para /buscar)
- Titulo da pagina atual
- Acoes contextuais (ex: "Nova busca" no Historico)

---

## Criterios de Aceitacao

### Sidebar Desktop

- [ ] AC1: Sidebar visivel em todas as paginas logadas (/buscar, /dashboard, /pipeline, /historico, /mensagens, /conta)
- [ ] AC2: Sidebar mostra 7 itens: Buscar, Dashboard, Pipeline, Historico, Mensagens, Minha Conta, Ajuda
- [ ] AC3: Item ativo esta highlighted com estilo distinto
- [ ] AC4: Sidebar pode ser colapsada (so icones) via toggle
- [ ] AC5: Estado colapsado/expandido persiste em localStorage
- [ ] AC6: Sidebar nao aparece em paginas publicas (/, /login, /signup, /planos, /ajuda)

### Bottom Nav Mobile

- [ ] AC7: Bottom nav aparece em < 1024px com 5 itens
- [ ] AC8: Cada item tem icone + label visivel
- [ ] AC9: Touch targets >= 44px (WCAG)
- [ ] AC10: "Mais" abre drawer com Conta, Ajuda, Sair

### Header Padrao

- [ ] AC11: Todas as paginas internas tem header com logo + navegacao
- [ ] AC12: Logo no header leva para /buscar (nao para /)
- [ ] AC13: Paginas sem header anterior (Historico, Conta) ganham header

### Nao-Regressao

- [ ] AC14: Pagina de busca continua funcional (filtros, SSE, resultados)
- [ ] AC15: Nenhum teste existente quebra (baseline: 50 fail FE)
- [ ] AC16: Performance: LCP nao aumenta mais que 200ms

---

## Arquivos Envolvidos (Estimativa)

### Criar
- `frontend/components/Sidebar.tsx` — componente sidebar desktop
- `frontend/components/BottomNav.tsx` — componente bottom nav mobile
- `frontend/components/AppLayout.tsx` — layout wrapper para area logada

### Modificar
- `frontend/app/buscar/page.tsx` — wrapper com AppLayout
- `frontend/app/dashboard/page.tsx` — wrapper com AppLayout
- `frontend/app/pipeline/page.tsx` — wrapper com AppLayout
- `frontend/app/historico/page.tsx` — wrapper com AppLayout + header
- `frontend/app/mensagens/page.tsx` — wrapper com AppLayout
- `frontend/app/conta/page.tsx` — wrapper com AppLayout + header

### Testes
- `frontend/__tests__/sidebar.test.tsx` — novo
- `frontend/__tests__/bottom-nav.test.tsx` — novo

---

## Estimativa

- **Complexidade:** Alta (impacta layout de todas as paginas internas)
- **Arquivos:** ~12 modificados/criados
- **Risco:** Medio (pode afetar layout existente da busca)

## Notas

- Inspiracao: Notion, Linear, monday.com — todas usam sidebar persistente
- O toggle de tema (Light/Dark) deve migrar para a sidebar ou settings, removendo do header
- "Buscas Salvas" tambem pode migrar para a sidebar como sub-item de Buscar
