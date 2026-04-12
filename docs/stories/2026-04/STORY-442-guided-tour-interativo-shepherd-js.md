# STORY-442: Guided Tour Interativo com Shepherd.js

**Priority:** P1 — Reduz abandono nos primeiros 10 minutos
**Effort:** M (3-4 dias)
**Squad:** @dev + @ux-design-expert + @qa
**Status:** Ready
**Epic:** [EPIC-CONVERSION-2026-04](EPIC-CONVERSION-2026-04.md)
**Sprint:** Sprint 2 — Semanas 3-4

---

## Contexto

O Shepherd.js está listado no stack do SmartLic mas não está sendo utilizado. Não existe nenhum guided tour no produto. Benchmarks B2B SaaS mostram que 70% dos trials abandonam nos primeiros 10 minutos por não saberem o que fazer após o primeiro login.

O onboarding de 3 passos (CNAE → UFs → Confirmação) leva até a primeira busca automática, mas após os resultados aparecerem o usuário está sozinho — sem entender o que é o score de viabilidade (STORY-440), como usar o pipeline, ou como exportar.

**Impacto estimado:** +2pp em trial-to-paid conversion.

---

## Acceptance Criteria

### AC1: Tour ativado automaticamente no primeiro login pós-onboarding
- [x] Tour inicia automaticamente quando usuário acessa `/buscar` pela primeira vez após completar o onboarding
- [x] "Primeira vez" verificado via localStorage: se `smartlic_tour_completed` não existe → iniciar tour
- [x] Tour aguarda resultados de busca carregarem antes de iniciar (não iniciar com tela em loading)

### AC2: 5 passos do tour com targets específicos
- [x] **Passo 1 — Busca:** Aponta para o `FilterPanel` (campo de setor/UF) — "Configure sua busca: selecione seu setor e as UFs onde atua"
- [x] **Passo 2 — Score de viabilidade:** Aponta para o `ViabilityBadge` do primeiro resultado (STORY-440) — "Este badge mostra a viabilidade de cada oportunidade: verde = alta, vermelho = baixa"
- [x] **Passo 3 — Resumo IA:** Aponta para o resumo executivo do primeiro card — "O SmartLic gerou um resumo executivo automático de cada edital com IA"
- [x] **Passo 4 — Pipeline:** Aponta para o botão "Adicionar ao Pipeline" do primeiro card — "Salve as melhores oportunidades no seu pipeline para acompanhar"
- [x] **Passo 5 — Export:** Aponta para o botão de export Excel — "Exporte todos os resultados para Excel com 1 clique"
- [x] Cada passo tem: título, descrição, botão "Próximo" / "Concluir" no último passo

### AC3: Opção de pular o tour
- [x] Todo passo tem botão "Pular tour" no canto superior direito do popup
- [x] Ao pular: salvar `smartlic_tour_completed: true` em localStorage
- [x] Tour não reinicia na próxima visita

### AC4: Estado salvo em localStorage
- [x] Após completar todos os 5 passos: salvar `smartlic_tour_completed: true` em localStorage
- [x] Tour NÃO é re-ativado se `smartlic_tour_completed: true` já existe

### AC5: Botão "Ver tour novamente" em /conta
- [x] Em `/conta` (preferências), adicionar botão "Ver tour do produto novamente"
- [x] Ao clicar: remover `smartlic_tour_completed` do localStorage + redirecionar para `/buscar`

### AC6: Tracking Mixpanel
- [x] `tour_started` — ao iniciar automaticamente
- [x] `tour_step_completed` com propriedade `step: number` — a cada passo completado
- [x] `tour_completed` — ao concluir o passo 5
- [x] `tour_skipped` com propriedade `at_step: number` — ao clicar "Pular"

### AC7: Responsividade
- [x] Tour funciona em mobile (375px+): popups posicionados para não sair da tela
- [x] Tour funciona em tablet (768px+) e desktop
- [x] Shepherd.js suporta responsividade nativa — usar configuração adequada

### AC8: Compatibilidade com Shepherd.js existente
- [x] Verificar versão do Shepherd.js em `package.json` e usar API dessa versão
- [x] NÃO instalar nova versão — usar o que já está instalado
- [x] Importar Shepherd CSS se necessário (verificar se já está importado)

---

## Scope

**IN:**
- Componente `GuidedTour.tsx` com lógica Shepherd.js
- 5 passos do tour descritos acima
- localStorage para estado do tour
- Botão "ver tour novamente" em /conta
- Tracking Mixpanel

**OUT:**
- Tour para outras páginas além de /buscar
- Tour de onboarding (etapas já existem)
- Vídeo tutorial
- Tooltips permanentes (não é tour)

---

## Dependencies

- STORY-440 (ViabilityBadge) — Passo 2 do tour aponta para o badge. Se STORY-440 não estiver concluída, o passo 2 aponta para a área de score mesmo sem o badge (degradação graciosa)
- Shepherd.js instalado em `package.json` (verificar)

---

## Risks

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| Shepherd.js não está no package.json (apenas mencionado no stack) | Média | Verificar antes de implementar; se não estiver, instalar versão LTS |
| Elementos do DOM (targets do tour) não renderizados quando tour inicia | Média | Aguardar resultados de busca carregarem (observer ou setTimeout conservador) |
| Tour quebra em mobile por falta de elementos visíveis | Baixa | Testar em 375px e usar `floatingUIOptions` do Shepherd para posicionamento responsivo |

---

## File List

- [x] `frontend/app/buscar/components/GuidedTour.tsx` — AC1-AC7: componente principal do tour
- [x] `frontend/app/buscar/page.tsx` — AC1: integrar GuidedTour após resultados carregarem
- [x] `frontend/app/conta/page.tsx` — AC5: botão "Ver tour novamente"
- [x] `frontend/__tests__/buscar/GuidedTour.test.tsx` — AC3, AC4, AC6: testes

---

## Dev Notes

- Shepherd.js docs: https://shepherdjs.dev/docs/
- Target dos passos: usar `data-tour="step-N"` como atributos nos elementos alvo (adicionar nos componentes correspondentes)
- Passo 2 depende de STORY-440 estar implementado; caso contrário, definir target fallback (ex: classe do card)
- CSS do Shepherd: importar `shepherd.js/dist/css/shepherd.css` (verificar se já importado em globals.css)
- Para aguardar resultados: verificar state de busca em `buscar/page.tsx` e só renderizar `GuidedTour` quando `results.length > 0`

---

## Change Log

| Data | Agente | Mudança |
|------|--------|---------|
| 2026-04-12 | @sm | Story criada — CEO Board Sprint, impacto +2pp |
