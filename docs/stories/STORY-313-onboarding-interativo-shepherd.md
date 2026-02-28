# STORY-313: Onboarding Interativo Shepherd.js

**Epic:** EPIC-PRE-GTM-2026-02
**Sprint:** Sprint 2 (Launch)
**Priority:** HIGH
**Story Points:** 5 SP
**Estimate:** 2-3 dias
**Owner:** @dev + @ux-design-expert

---

## Problem

Apos o onboarding inicial (3 passos: CNAE → UFs → Confirmacao), o usuario chega na pagina de busca sem orientacao sobre como usar os filtros, interpretar resultados, usar o pipeline, etc. O time-to-value e alto porque o usuario precisa descobrir sozinho a interface. Shepherd.js ja esta instalado (v14.5.1) mas nenhum tour foi implementado.

## Solution

Criar tour interativo guiado com Shepherd.js que introduz as funcionalidades principais em 3 fluxos contextuais (busca, resultados, pipeline), disparados automaticamente na primeira visita ou acessiveis via botao "Ajuda".

---

## Acceptance Criteria

### Frontend — Tour de Busca (primeira visita a /buscar)

- [ ] **AC1:** Tour automatico na primeira visita a `/buscar` (detectar via `localStorage` flag `onboarding_tour_completed`):
  - Step 1: Highlight filtro de setor — "Escolha o setor da sua empresa para filtrar oportunidades relevantes"
  - Step 2: Highlight seletor de UFs — "Selecione os estados onde sua empresa atua ou quer atuar"
  - Step 3: Highlight periodo de busca — "Defina o periodo para buscar editais recentes"
  - Step 4: Highlight botao Buscar — "Clique para iniciar sua busca inteligente!"
  - Total: 4 steps, botoes "Proximo" / "Pular tour"
- [ ] **AC2:** Tour nao aparece se usuario ja completou (`localStorage` check)
- [ ] **AC3:** Botao "Pular tour" em qualquer step encerra e marca como completado
- [ ] **AC4:** Tracking: `trackEvent('onboarding_tour_started', { tour: 'search' })`
- [ ] **AC5:** Tracking: `trackEvent('onboarding_tour_completed', { tour: 'search', steps_seen: N })`
- [ ] **AC6:** Tracking: `trackEvent('onboarding_tour_skipped', { tour: 'search', skipped_at_step: N })`

### Frontend — Tour de Resultados (primeira busca com resultados)

- [ ] **AC7:** Tour automatico apos primeira busca com >= 1 resultado:
  - Step 1: Highlight card de licitacao — "Cada card mostra uma oportunidade com data, valor e orgao"
  - Step 2: Highlight badge de viabilidade — "O score de viabilidade indica o potencial desta oportunidade"
  - Step 3: Highlight botao pipeline — "Adicione ao pipeline para acompanhar oportunidades promissoras"
  - Step 4: Highlight botao Excel — "Exporte resultados para Excel para analise detalhada"
  - Total: 4 steps
- [ ] **AC8:** Condicional: so dispara se `onboarding_results_tour_completed` nao existe no localStorage

### Frontend — Tour de Pipeline (primeira visita a /pipeline)

- [ ] **AC9:** Tour automatico na primeira visita a `/pipeline`:
  - Step 1: Highlight colunas Kanban — "Arraste oportunidades entre etapas para acompanhar seu progresso"
  - Step 2: Highlight card no pipeline — "Clique para ver detalhes e adicionar notas"
  - Step 3: Highlight alertas — "Receba alertas quando prazos estiverem proximos"
  - Total: 3 steps
- [ ] **AC10:** Condicional: so dispara se `onboarding_pipeline_tour_completed` nao existe

### Frontend — Componente Shepherd Wrapper

- [ ] **AC11:** Criar `frontend/hooks/useShepherdTour.ts`:
  - Wrapper hook em torno de Shepherd.js
  - Props: `tourId`, `steps[]`, `onComplete`, `onSkip`
  - Gerencia localStorage flags automaticamente
  - Styling customizado com tema SmartLic (cores, fontes, border-radius)
- [ ] **AC12:** CSS theme para Shepherd que segue design system SmartLic:
  - Fundo branco, borda azul SmartLic, sombra suave
  - Botoes com estilo primario/secundario do app
  - Overlay escuro (70% opacity) com spotlight no elemento
  - Responsive: funcionar em mobile (< 640px)
- [ ] **AC13:** Steps devem ter `attachTo` com posicionamento inteligente (Shepherd auto-posiciona)
- [ ] **AC14:** `scrollTo: true` em cada step (scroll suave ate o elemento)

### Frontend — Botao "Guia Interativo" Permanente

- [ ] **AC15:** Botao flutuante "?" ou "Guia" no canto inferior direito de `/buscar`, `/pipeline`, `/dashboard`
- [ ] **AC16:** Click abre menu com opcoes: "Tour de busca", "Tour de resultados", "Tour de pipeline"
- [ ] **AC17:** Replay do tour mesmo se ja completado (reset flag + start tour)

### Backend — Tracking (opcional)

- [ ] **AC18:** Endpoint `POST /v1/onboarding/tour-event` para persistir tour completion no servidor:
  - `{ tour_id, event: 'completed' | 'skipped', steps_seen, timestamp }`
  - Permite analytics de quantos usuarios completam tours

### Testes

- [ ] **AC19:** Testes para cada tour (busca, resultados, pipeline) — render, step navigation, skip
- [ ] **AC20:** Teste localStorage persistence (nao repetir tour)
- [ ] **AC21:** Teste botao replay
- [ ] **AC22:** Zero regressions

---

## Infraestrutura Existente

| Componente | Arquivo | Status |
|-----------|---------|--------|
| Shepherd.js | `package.json` → shepherd.js ^14.5.1 | Instalado, nao usado |
| Onboarding hook | `frontend/hooks/useOnboarding.tsx` | Existe (wizard, nao tour) |
| Onboarding page | `frontend/app/onboarding/` | Existe (3-step wizard) |
| Analytics | `frontend/hooks/useAnalytics.ts` | Existe |
| Design system | Tailwind + CSS vars | Existe |

## Files Esperados (Output)

**Novos:**
- `frontend/hooks/useShepherdTour.ts`
- `frontend/components/OnboardingTourButton.tsx`
- `frontend/styles/shepherd-theme.css` (ou inline no hook)
- `frontend/__tests__/onboarding/shepherd-tours.test.tsx`
- `backend/routes/onboarding.py` (adicionar endpoint tour-event)

**Modificados:**
- `frontend/app/buscar/page.tsx` (trigger tour busca + resultados)
- `frontend/app/pipeline/page.tsx` (trigger tour pipeline)

## Dependencias

- Shepherd.js ja instalado
- Elementos do DOM devem ter `data-tour` attributes para targeting

## Riscos

- Shepherd.js pode conflitar com z-index de modais existentes — testar overlay
- Tour em mobile precisa ser mais curto (menos steps)
- Performance: Shepherd nao deve atrasar hydration (lazy load)
