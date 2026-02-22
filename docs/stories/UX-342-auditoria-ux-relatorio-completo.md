# UX-342 — Relatorio Completo da Auditoria UX (2026-02-22)

**Tipo:** Documento / Referencia
**Criada:** 2026-02-22
**Metodologia:** Auditoria heuristica com persona + navegacao real em producao

---

## Persona Utilizada

**"Seu Carlos"** — Carlos Ribeiro, 60 anos
- Empresa: Ribeiro Uniformes LTDA (PME, 25 funcionarios)
- Localizacao: Uberlandia, MG
- Experiencia digital: Basica (WhatsApp, email, planilhas)
- Dispositivo: Android 360px + notebook Dell 1366x768
- Dor: "Perdi uma licitacao de R$300 mil porque ninguem viu o edital a tempo"

---

## Stories Criados a partir da Auditoria

| ID | Titulo | Severidade | Status |
|----|--------|-----------|--------|
| UX-337 | Sidebar de Navegacao Persistente na Area Logada | Critica | Concluido |
| UX-338 | Fix Dashboard Loading Infinito | Critica | Concluido |
| UX-339 | Mostrar Pricing Completo para Usuario Logado | Alta | Concluido |
| UX-340 | Redesign Header Mobile | Alta | Concluido |
| UX-341 | Empty States Educativos (Pipeline, Historico, Dashboard, Conta) | Media | Concluido |
| UX-343 | Fix Exibicao Nome Plano Legacy ("Sala de Guerra" → "SmartLic Pro") | Alta | Concluido |

---

## Todos os Achados (14 itens)

### CRITICOS (3)

| ID | Achado | Pagina | Story |
|----|--------|--------|-------|
| C1 | Dashboard eternamente em loading (skeleton) | /dashboard | UX-338 |
| C2 | Navegacao principal inexistente na area logada | /buscar | UX-337 |
| C3 | Menu do usuario escondido atras de avatar sem label | /buscar header | UX-337 |

### ALTOS (5)

| ID | Achado | Pagina | Story |
|----|--------|--------|-------|
| A1 | Header mobile com icones sem labels | /buscar mobile | UX-340 |
| A2 | Filtros avancados com 27 UFs selecionados por default | /buscar | Backlog |
| A3 | Termos tecnicos sem explicacao (Modalidade, Concorrencia) | /buscar | UX-323 (existente) |
| A4 | Pagina de Planos bloqueada para usuario logado | /planos | UX-339 |
| A5 | Preco R$1.999/mes sem contexto ROI proeminente | /planos | Backlog |

### MEDIOS (6)

| ID | Achado | Pagina | Story |
|----|--------|--------|-------|
| M1 | Historico sem header/navegacao propria | /historico | UX-337 |
| M2 | Pipeline vazio sem onboarding contextual | /pipeline | UX-341 |
| M3 | Conta mostra so "Cancelar" na secao de plano | /conta | UX-341 |
| M4 | Signup: requisitos de senha so no placeholder | /signup | UX-307 (existente) |
| M5 | Login: "Magic Link" pode confundir | /login | Backlog |
| M6 | Footer: "servidores publicos" contradiz "nao afiliado ao governo" | Footer | Backlog |

### BAIXOS (4)

| ID | Achado | Pagina | Story |
|----|--------|--------|-------|
| B1 | Landing page muito longa com conteudo repetitivo | / | Backlog |
| B2 | Contadores animados mostram "0" antes de animar | / hero | Backlog |
| B3 | Toggle Light/Dark desnecessario no header | /buscar header | UX-340 |
| B4 | Central de Ajuda excelente (nota positiva) | /ajuda | N/A |

---

## Screenshots Capturados

| Arquivo | Pagina | Viewport |
|---------|--------|----------|
| ux-audit-01-landing-viewport.png | Landing page | 1280x800 |
| ux-audit-01-landing-full.png | Landing page (full) | 1280x800 |
| ux-audit-02-signup.png | Signup | 1280x800 |
| ux-audit-03-login.png | Login | 1280x800 |
| ux-audit-04-buscar.png | Buscar (logado) | 1280x800 |
| ux-audit-05-buscar-filtros.png | Buscar + filtros (full) | 1280x800 |
| ux-audit-06-planos.png | Planos (logado - bloqueado) | 1280x800 |
| ux-audit-07-dashboard.png | Dashboard (skeleton 3s) | 1280x800 |
| ux-audit-07b-dashboard-loaded.png | Dashboard (skeleton 8s) | 1280x800 |
| ux-audit-08-pipeline.png | Pipeline (vazio) | 1280x800 |
| ux-audit-09-historico.png | Historico (vazio) | 1280x800 |
| ux-audit-10-user-menu.png | Menu usuario dropdown | 1280x800 |
| ux-audit-11-conta.png | Minha Conta (full) | 1280x800 |
| ux-audit-12-ajuda.png | Central de Ajuda | 1280x800 |
| ux-audit-13-mobile-landing.png | Landing mobile | 360x740 |
| ux-audit-14-mobile-buscar.png | Buscar mobile | 360x740 |

---

## Ordem de Execucao Recomendada

1. **UX-338** (Dashboard fix) — Baixo esforco, impacto imediato, pode ser hotfix
2. **UX-339** (Pricing visivel) — Baixo esforco, impacto direto na conversao
3. **UX-341** (Empty states) — Medio esforco, melhora toda a experiencia de usuario novo
4. **UX-337** (Sidebar navegacao) — Alto esforco, maior impacto estrutural
5. **UX-340** (Header mobile) — Medio esforco, depende parcialmente de UX-337
