# UX-340 — Redesign Header Mobile (Labels + Hamburger Menu)

**Tipo:** Feature / UX Alto
**Prioridade:** Alta (A1 + B3 da auditoria UX 2026-02-22)
**Criada:** 2026-02-22
**Status:** Pendente
**Origem:** Auditoria UX — Persona "Seu Carlos" (gestor PME 60 anos, interior BR)
**Depende de:** UX-337 (se implementar bottom nav, este story muda de escopo)

---

## Problema

No mobile (360px), o header da area logada mostra icones genericos sem qualquer label:

```
[SmartLic.tech] [⏱ v] [◯ v] [✉] [T]
```

- O icone de relogio = "Buscas Salvas" (nao e obvio)
- O circulo vazio = toggle Light/Dark (desnecessario no header)
- O envelope = Mensagens (razoavel, mas sem label)
- T = avatar/menu (nao indica que e menu)

### Impacto

- Seu Carlos no celular Android nao sabe o que os icones fazem
- Toggle de tema ocupa espaco precioso sem beneficio para PME
- "Buscas Salvas" e uma feature secundaria que nao deveria estar no header mobile

### Evidencia

- Screenshot `ux-audit-14-mobile-buscar.png` — icones sem label, avatar cortado

---

## Solucao Proposta

### Header Mobile Redesenhado

```
[SmartLic] _________________ [≡ Menu]
```

Simplificar para:
- **Logo** (link para /buscar)
- **Espaco** (titulo da pagina atual opcionalmente)
- **Hamburger menu** com label "Menu" ao lado

O hamburger abre um drawer lateral com:
```
┌──────────────────┐
│  Seu Carlos      │
│  carlos@email.com│
│  ──────────────  │
│  🔍 Buscar      │
│  📋 Pipeline     │
│  📜 Historico    │
│  💬 Mensagens    │
│  📊 Dashboard    │
│  ──────────────  │
│  ⏱ Buscas Salvas│
│  👤 Minha Conta  │
│  ❓ Ajuda       │
│  🌙 Tema Escuro  │ ← toggle aqui
│  🚪 Sair        │
└──────────────────┘
```

### Nota sobre UX-337

Se UX-337 implementar bottom navigation, o hamburger menu mobile tera menos itens (apenas os que nao estao no bottom nav). Implementar este story considerando ambos os cenarios.

---

## Criterios de Aceitacao

- [ ] AC1: Header mobile mostra apenas Logo + botao Menu (hamburger com label)
- [ ] AC2: Toggle Light/Dark removido do header mobile (movido para drawer)
- [ ] AC3: "Buscas Salvas" removido do header mobile (movido para drawer)
- [ ] AC4: Hamburger abre drawer lateral com todas as opcoes de navegacao
- [ ] AC5: Drawer mostra nome + email do usuario no topo
- [ ] AC6: Drawer fecha ao clicar fora ou no X
- [ ] AC7: Drawer fecha ao navegar para outra pagina
- [ ] AC8: Touch target do hamburger >= 44px (WCAG 2.2 AA)
- [ ] AC9: Animacao de abertura suave (slide from right, 200ms)

### Desktop (manter como esta ou ajustar minimamente)

- [ ] AC10: Em desktop (>= 1024px), header mantem layout atual (ou simplifica se UX-337 trouxer sidebar)
- [ ] AC11: Breakpoint: 1024px (abaixo = mobile header, acima = desktop header)

### Nao-Regressao

- [ ] AC12: Busca continua funcional no mobile
- [ ] AC13: Nenhum teste existente quebra (baseline: 50 fail FE)

---

## Arquivos Envolvidos (Estimativa)

### Criar
- `frontend/components/MobileDrawer.tsx` — drawer lateral
- `frontend/components/MobileHeader.tsx` — header simplificado

### Modificar
- `frontend/app/buscar/page.tsx` — substituir header no mobile
- Qualquer componente que renderize o header atual

### Testes
- `frontend/__tests__/mobile-header.test.tsx` — novo

---

## Estimativa

- **Complexidade:** Media
- **Risco:** Medio (impacta header em todas as paginas)
