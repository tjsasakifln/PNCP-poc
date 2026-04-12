# STORY-446: Upgrade Gate no Pipeline Kanban (Limite Trial)

**Priority:** P1 — Demonstra valor sem dar tudo grátis
**Effort:** S (2 dias)
**Squad:** @dev + @qa
**Status:** Done
**Epic:** [EPIC-CONVERSION-2026-04](EPIC-CONVERSION-2026-04.md)
**Sprint:** Sprint 2 — Semanas 3-4

---

## Contexto

O pipeline kanban está 100% funcional durante o trial sem nenhuma limitação — o usuário pode adicionar quantos cards quiser. Isso entrega todo o valor do pipeline sem criar urgência de conversão.

O objetivo é demonstrar o valor do pipeline (deixar o usuário usar e gostar) mas criar um gate que motive o upgrade. O limite de 5 cards foi escolhido porque é suficiente para entender o workflow mas insuficiente para uso profissional real.

**Impacto estimado:** +1pp em trial-to-paid conversion.

---

## Acceptance Criteria

### AC1: Limite de 5 cards para trial
- [x] Usuários trial podem adicionar até 5 oportunidades ao pipeline
- [x] Cards já existentes no pipeline de trial users são preservados (sem remoção retroativa)
- [x] Limite aplica-se apenas a `plan_type === "free_trial"` com trial ativo

### AC2: Modal de bloqueio ao tentar adicionar o 6º card
- [x] Ao tentar adicionar card além do limite, exibir modal `TrialPipelineLimitModal`
- [x] Conteúdo do modal:
  - Título: "Limite do trial atingido"
  - Texto: "Você já tem 5 oportunidades no seu pipeline. Com SmartLic Pro, gerencie oportunidades ilimitadas."
  - Botão primário: "Assinar SmartLic Pro" (href="/planos")
  - Botão secundário: "Fechar"
- [x] Modal fecha ao clicar fora ou no botão "Fechar"

### AC3: Contador de uso no header do pipeline
- [x] Para trial users, exibir no header do pipeline: "X/5 oportunidades usadas"
- [x] Formato: `{count}/5 oportunidades usadas`
- [x] Cor do contador: verde (0-3), amarelo (4), vermelho (5)
- [x] Para pagantes: contador NÃO é exibido

### AC4: Cards existentes preservados
- [x] Se um trial user já tem >5 cards (criados antes desta implementação): todos são mantidos
- [x] Gate aplica-se apenas para NOVOS cards após a implementação
- [x] Não há remoção retroativa de cards

### AC5: Pagantes sem limite
- [x] Usuários pagantes (`smartlic_pro`, `consultoria`, etc.) NÃO veem limite nem contador
- [x] Comportamento atual do pipeline preservado para pagantes

### AC6: Backend — 403 com erro estruturado
- [x] `POST /pipeline` verifica quota de pipeline para trial users
- [x] Se trial user já tem ≥ 5 cards: retornar `HTTP 403` com body:
  ```json
  { "error": "trial_pipeline_limit", "limit": 5, "current": 5 }
  ```
- [x] Helper `get_pipeline_count(user_id)` em `authorization.py` ou `pipeline.py`

### AC7: Testes
- [x] Teste backend: trial user com 4 cards → POST pipeline retorna 201 (pode adicionar)
- [x] Teste backend: trial user com 5 cards → POST pipeline retorna 403 com `trial_pipeline_limit`
- [x] Teste backend: paid user com 10 cards → POST pipeline retorna 201 (sem limite)
- [x] Teste frontend: modal aparece ao tentar adicionar 6º card
- [x] Teste frontend: contador mostra "5/5 oportunidades usadas" quando no limite

---

## Scope

**IN:**
- Check de limite no `POST /pipeline` backend
- Modal `TrialPipelineLimitModal.tsx`
- Contador de uso no header do `PipelineKanban.tsx`
- Testes backend e frontend

**OUT:**
- Limite em outras operações do pipeline (drag-and-drop entre colunas é livre)
- Remoção retroativa de cards de trials antigos
- Limite por coluna (limite é total, não por coluna)
- Limite diferente por plano (apenas trial vs. pagante)

---

## Dependencies

- `backend/routes/pipeline.py` — endpoint POST existente
- `frontend/app/pipeline/PipelineKanban.tsx` — componente principal existente
- Nenhuma dependência de outras stories deste epic

---

## Risks

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| Trial users com >5 cards antes da implementação afetam a contagem | Média | Consulta de count considera apenas registros com `is_active = true`; preservar cards existentes |
| Frontend envia POST múltiplos antes do backend responder (double-click) | Baixa | Desabilitar botão após primeiro click (loading state) |

---

## File List

- [x] `backend/routes/pipeline.py` — AC6: adicionar check de limite no POST
- [x] `backend/authorization.py` — AC6: helper `get_pipeline_count(user_id)` ou similar
- [x] `frontend/app/pipeline/PipelineKanban.tsx` — AC3: contador no header
- [x] `frontend/app/pipeline/components/TrialPipelineLimitModal.tsx` — AC2: novo modal
- [x] `backend/tests/test_pipeline_trial_limit.py` — AC7: testes de backend
- [x] `frontend/__tests__/pipeline/TrialPipelineLimitModal.test.tsx` — AC7: testes de frontend

---

## Dev Notes

- Query para contar cards do pipeline: `SELECT COUNT(*) FROM pipeline_items WHERE user_id = :user_id AND is_active = TRUE`
- O limit check deve acontecer no backend (não apenas no frontend) — segurança first
- Modal: usar o padrão de modal existente no projeto (verificar componentes de modal em `components/`)
- Contador no header: buscar count atual via `GET /pipeline` que já retorna os cards (count do array)

---

## Change Log
- 2026-04-12: Status → Done (implementado em EPIC-CONVERSION-2026-04, testes corrigidos)

| Data | Agente | Mudança |
|------|--------|---------|
| 2026-04-12 | @sm | Story criada — CEO Board Sprint, impacto +1pp |
