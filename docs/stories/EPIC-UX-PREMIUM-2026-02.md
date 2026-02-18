# EPIC: UX Premium Overhaul — SmartLic Production Quality

**Epic ID:** EPIC-UX-PREMIUM-2026-02
**Created:** 2026-02-18
**Owner:** @pm (Morgan) + @ux-design-expert (Uma)
**Status:** 🔴 PLANNING
**Target:** Production-grade premium experience (8.5+/10)

---

## Epic Overview

Transformar a experiência do SmartLic de **4.2/10 (não-premium)** para **8.5+/10 (premium)** através de 35 melhorias identificadas em auditoria UX completa.

**Audit Report:** Baseado em teste manual completo como admin em produção (smartlic.tech)

---

## Current State (Baseline)

### Scores por Dimensão
- **Performance & Confiabilidade:** 2/10 ⚠️ (CRÍTICO)
- **Feedback & Comunicação:** 3/10
- **Consistência Visual:** 5/10
- **Responsividade:** 6/10
- **Acessibilidade:** 6/10

**Score Geral:** 4.2/10 — **NÃO PREMIUM**

### Problemas Identificados
- 🔴 **Críticos (Bloqueadores):** 8 problemas
- 🟠 **Graves (Alta Prioridade):** 12 problemas
- 🟡 **Médios (Polimento):** 15 problemas
- **Total:** 35 problemas

---

## Target State (Goals)

### Scores Alvo
- **Performance & Confiabilidade:** 9/10 ✅
- **Feedback & Comunicação:** 9/10 ✅
- **Consistência Visual:** 8/10 ✅
- **Responsividade:** 8/10 ✅
- **Acessibilidade:** 8/10 ✅

**Score Geral Alvo:** 8.5/10 — **PREMIUM**

### Critérios de Sucesso
- [ ] Busca de 5 estados < 30s (95th percentile)
- [ ] Busca de 27 estados < 3min (com warning proativo)
- [ ] Progresso sempre monotônico (nunca volta para trás)
- [ ] Cache hit rate > 60%
- [ ] Zero mensagens de erro genéricas
- [ ] Toda ação tem feedback visual < 100ms
- [ ] Estimativas de tempo ±15% precisas
- [ ] Quota visível em todas as páginas
- [ ] Dark mode completo e consistente
- [ ] Contraste WCAG AA em 100% dos textos

---

## Epic Breakdown (Stories)

### 🚨 Wave 1: CRÍTICOS (Sprint 1-2, 2 semanas)
**Goal:** Tornar o sistema confiável e utilizável

| Story ID | Título | SP | Owner | Prioridade |
|----------|--------|----|----|------------|
| UX-301 | Fix Timeout Catastrófico na Busca Principal | 13 | @dev + @qa | P0 |
| UX-302 | Fix Progresso Não-Monotônico (Reinício Abrupto) | 8 | @dev | P0 |
| UX-303 | Fix Cache Supabase Quebrado (Falha Silenciosa) | 5 | @devops + @dev | P0 |
| UX-304 | Fix Filtros Hiper-Agressivos (11k→0 resultados) | 13 | @dev + @architect | P0 |
| UX-305 | Fix Landing Page Vazia (Usuário Logado) | 3 | @dev | P1 |
| UX-306 | Add Header/Navigation na Página de Conta | 3 | @dev | P1 |
| UX-307 | Add Validação de Senha em Tempo Real | 5 | @dev | P1 |
| UX-308 | Add Confirmação em Cancelamento de Plano | 8 | @dev + @ux | P1 |

**Total Wave 1:** 58 SP (~1.5 sprints)

### 🔥 Wave 2: GRAVES (Sprint 3, 1 semana)
**Goal:** Eliminar frustrações e melhorar comunicação

| Story ID | Título | SP | Prioridade |
|----------|--------|----|----|
| UX-309 | Fix Estados "Aguardando..." Indefinidamente | 5 | P1 |
| UX-310 | Mensagens de Erro Acionáveis (Não Genéricas) | 5 | P1 |
| UX-311 | Estimativa de Tempo Realista (Calibração) | 5 | P1 |
| UX-312 | Indicador de Quota de Análises | 3 | P1 |
| UX-313 | Empty State em "Buscas Salvas" | 2 | P2 |
| UX-314 | Indicador de Estado em "Personalizar busca" | 1 | P2 |
| UX-315 | Slider de Valor com Tooltip em Drag | 2 | P2 |
| UX-316 | Hover States em Cards de Modalidade | 1 | P2 |
| UX-317 | Fix Links Quebrados no Footer | 5 | P1 |
| UX-318 | Dark Mode Completo (Cores Adaptativas) | 8 | P2 |
| UX-319 | Heartbeat em Progresso "Em Tempo Real" | 5 | P1 |
| UX-320 | Cleanup Console Errors (Lighthouse) | 3 | P2 |

**Total Wave 2:** 45 SP (~1 sprint)

### ✨ Wave 3: POLIMENTO (Sprint 4, 1 semana)
**Goal:** Elevar experiência para nível premium

| Story ID | Título | SP | Prioridade |
|----------|--------|----|----|
| UX-321 | Botões de Região com Contagem de Estados | 2 | P3 |
| UX-322 | Badge Visual para "27 estados selecionados" | 1 | P3 |
| UX-323 | Tooltips Explicativos em Filtros | 2 | P3 |
| UX-324 | Modalidades Responsivas em Mobile | 2 | P3 |
| UX-325 | Slider com Snap em Valores Redondos | 2 | P3 |
| UX-326 | Atalhos de Teclado Globais | 8 | P3 |
| UX-327 | Loading Skeletons Realistas | 3 | P3 |
| UX-328 | Animações com Easing Suave | 2 | P3 |
| UX-329 | Tabs com Keyboard Navigation | 2 | P3 |
| UX-330 | Botão "Buscar" com Loading Spinner | 1 | P3 |
| UX-331 | Indicador de Rede Lenta | 3 | P3 |
| UX-332 | Feedback Sonoro Opcional | 2 | P3 |
| UX-333 | Meta Description em Todas as Páginas | 2 | P3 |
| UX-334 | Alt Text em Todas as Imagens | 2 | P3 |
| UX-335 | Auditoria de Contraste WCAG AA | 5 | P2 |

**Total Wave 3:** 39 SP (~0.75 sprint)

---

## Total Epic Effort

**Total Story Points:** 142 SP
**Total Sprints:** ~3.25 sprints
**Duration:** 6-7 semanas
**Team:** Full squad (dev, qa, devops, ux, architect, pm)

---

## Dependencies

### External
- [ ] Supabase migration para `fetched_at` column (UX-303)
- [ ] Railway timeout configs (UX-301)
- [ ] Stripe webhook testing sandbox (UX-308)

### Internal
- UX-302 depende de UX-301 (ambos mexem no progresso)
- UX-304 depende de UX-310 (mensagens de erro para filtros)
- UX-318 depende de UX-335 (contraste em dark mode)

---

## Risks & Mitigations

### Risk 1: Timeout Backend Pode Não Ser Suficiente
**Mitigation:**
- UX-301 inclui timeout progressivo (warning → graceful degradation)
- Fallback para cache stale se timeout

### Risk 2: Dark Mode Afeta Toda a UI
**Mitigation:**
- UX-318 como story separada no final
- Fazer auditoria completa antes de implementar

### Risk 3: Scope Creep (35 problemas)
**Mitigation:**
- Waves bem definidas (critical → grave → polish)
- Wave 1 é MVP para produção confiável
- Wave 2-3 podem deslizar se necessário

---

## Success Metrics

### Quantitative
- [ ] System Usability Scale (SUS): 75+ → 85+
- [ ] Time to First Result: média 45s → <30s
- [ ] Error Rate: 15% → <5%
- [ ] Cache Hit Rate: 0% → >60%
- [ ] Support Tickets (UX): 12/week → <3/week

### Qualitative
- [ ] User feedback: "Não consigo fazer buscar funcionar" → "Sistema rápido e intuitivo"
- [ ] Internal team: "Falta polimento" → "Experiência premium"
- [ ] NPS: 35 → 70+

---

## Stakeholders

- **Product Owner:** @po
- **Engineering Manager:** @pm
- **UX Lead:** @ux-design-expert
- **Tech Lead:** @architect
- **DevOps Lead:** @devops
- **QA Lead:** @qa

---

## Timeline

```
Week 1-2:  Wave 1 (Críticos) — UX-301 to UX-308
Week 3:    Wave 2 (Graves) — UX-309 to UX-320
Week 4:    Wave 3 (Polimento) — UX-321 to UX-335
Week 5-6:  Buffer + QA + Production rollout
```

---

## Related Documents

- `docs/gtm-ok/stories/UX-AUDIT-REPORT-2026-02-18.md` — Full audit report
- `docs/stories/UX-301.md` to `UX-335.md` — Individual stories
- `.aios-core/development/workflows/bidiq-ux-overhaul.yaml` — Workflow definition

---

**Status:** 🔴 Aguardando criação das 35 stories individuais
**Next:** @pm criar stories UX-301 a UX-335
