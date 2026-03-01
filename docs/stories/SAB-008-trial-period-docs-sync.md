# SAB-008: Inconsistência do período de trial na documentação

**Origem:** UX Premium Audit P1-05
**Prioridade:** P1 — Alto
**Complexidade:** XS (Extra Small)
**Sprint:** SAB-P1
**Owner:** @pm
**Screenshot:** `ux-audit/11-signup-page.png`

---

## Problema

A tela de signup diz "14 dias do produto completo" mas o CLAUDE.md e stories anteriores (STORY-264/277) referenciam trial de **30 dias**.

**Resolução:** STORY-319 já alterou o trial de 30 para 14 dias (ACs completos). O **código está correto** (14 dias). A **documentação** (CLAUDE.md, MEMORY.md) está desatualizada.

---

## Critérios de Aceite

### Atualizar Documentação

- [x] **AC1:** CLAUDE.md — alterar "Trial: 30 dias gratis" → "Trial: 14 dias gratis" (seção Billing & Auth)
- [x] **AC2:** Verificar MEMORY.md e remover/atualizar qualquer referência a "30 dias de trial" — nenhuma referência encontrada
- [x] **AC3:** Verificar PRD.md — atualizar referências de 30 → 14 dias se existirem — nenhuma referência encontrada
- [x] **AC4:** Verificar se há outros docs em `docs/` referenciando "30 dias" de trial — corrigidos: README.md, system-architecture.md, MKT-001, .env.example, CHANGELOG.md, squads/gtm-readiness-squad (3 arquivos)

### Validação no Frontend

- [x] **AC5:** Confirmar que TODAS as menções de trial no frontend dizem "14 dias" (signup, planos, banners, emails) — confirmado via grep
- [x] **AC6:** Confirmar que `config.py` `TRIAL_DURATION_DAYS` = 14 — confirmado (linha 393)

---

## Notas

- Story pequena — é apenas sync de documentação. O código já foi corrigido em STORY-319.
- Grep global por "30 dias" e "30-day" para encontrar todas as referências desatualizadas.
