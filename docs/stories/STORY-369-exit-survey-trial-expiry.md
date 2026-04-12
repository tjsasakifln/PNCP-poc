# STORY-369 — Exit Survey no Trial Expiry

**Status:** InReview
**Priority:** P1 — Conversão (zero dados qualitativos de churn hoje)
**Origem:** Conselho de CEOs Advisory Board — melhorias on-page funil conversão (2026-04-11)
**Componentes:** backend/routes/user.py, backend/migrations/, frontend/components/TrialExitSurveyModal.tsx, frontend/app/buscar/page.tsx
**Depende de:** nenhuma
**Bloqueia:** nenhuma
**Estimativa:** ~4h

---

## Contexto

O SmartLic possui uma sequência de 6 emails automáticos e um `TrialConversionScreen` para converter trials, mas **não coleta nenhum dado qualitativo** sobre por que usuários não convertem. Quando o trial expira, o usuário simplesmente bate no paywall sem deixar sinal algum.

Com founder solo e 7h/dia, ligar para cada trial não é escalável. Um exit survey automático no momento de expiração substitui essa interação e alimenta o funil de melhoria contínua sem custo recorrente de tempo.

**Hipótese:** 30-50% dos trials expirados responderão o survey se perguntado no momento certo (acesso ao produto bloqueado). A resposta "Não encontrei editais relevantes" → ajuste de onboarding/setores. "Preço alto" → teste de oferta. "Ainda avaliando" → reengajamento em 30 dias.

## Acceptance Criteria

### AC1: Migração Supabase — tabela `trial_exit_surveys`

- [x] Nova migration em `supabase/migrations/` cria tabela:
  ```sql
  CREATE TABLE trial_exit_surveys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    reason TEXT NOT NULL CHECK (reason IN ('no_relevant_bids', 'price_too_high', 'still_evaluating', 'other')),
    reason_text TEXT, -- preenchido apenas quando reason = 'other'
    created_at TIMESTAMPTZ DEFAULT NOW()
  );
  ```
- [x] RLS habilitado: usuário só pode inserir seu próprio registro; admin pode ler todos
- [x] Index em `created_at` para queries de analytics
- [x] Constraint: 1 survey por usuário (UNIQUE em `user_id`)

### AC2: Backend — endpoint `POST /v1/trial/exit-survey`

- [x] Novo endpoint em `backend/routes/user.py` (ou novo arquivo `backend/routes/trial.py`)
- [x] Requer autenticação (`require_auth`)
- [x] Aceita body: `{ reason: string, reason_text?: string }`
- [x] Valida que `reason` está no enum permitido
- [x] Retorna 409 se survey já foi submetido para este usuário
- [x] Retorna 201 com `{ id, created_at }` em caso de sucesso
- [x] Testes unitários: submit válido, submit duplicado, reason inválido, sem auth

### AC3: Frontend — componente `TrialExitSurveyModal`

- [x] Novo arquivo `frontend/components/TrialExitSurveyModal.tsx`
- [x] Modal (não página inteira) com:
  - Título: "Antes de sair, nos ajude a melhorar"
  - Pergunta: "O que faltou para você assinar?"
  - 4 opções como radio buttons:
    - "Não encontrei editais relevantes para meu setor"
    - "O preço está alto para minha realidade"
    - "Ainda estou avaliando o produto"
    - "Outro motivo"
  - Campo de texto livre (exibido apenas quando "Outro motivo" selecionado)
  - Botão "Enviar resposta" (habilitado apenas quando opção selecionada)
  - Link "Pular" abaixo do botão (fecha modal sem enviar)
- [x] Ao enviar: chama `POST /v1/trial/exit-survey`, mostra feedback de sucesso, fecha modal
- [x] Ao fechar (pular): fecha modal, não chama endpoint
- [x] Loading state no botão durante submit
- [x] Testes: render, seleção de opção, campo "outro", submit, skip

### AC4: Integração — exibir modal no acesso pós-expiração

- [x] Em `frontend/app/buscar/page.tsx` (ou layout raiz), detectar combinação: `isTrialExpired === true` + survey ainda não submetido
- [x] Exibir `TrialExitSurveyModal` antes de exibir `TrialConversionScreen` (survey primeiro, upgrade depois)
- [x] Controle de "já respondido" via localStorage (chave: `trial_exit_survey_submitted`) para evitar re-exibição se API falhar
- [x] Verificar se survey já foi respondido via endpoint ou localStorage antes de exibir

### AC5: Evento Mixpanel

- [x] Ao submeter survey com sucesso: `mixpanel.track('trial_exit_survey_submitted', { reason, has_text: boolean })`
- [x] Ao pular: `mixpanel.track('trial_exit_survey_skipped')`
- [x] Usar o wrapper Mixpanel já existente no projeto (não criar novo)

### AC6: Admin — visibilidade básica

- [x] Endpoint admin `GET /v1/admin/trial-exit-surveys` retorna lista com `reason`, `created_at` (sem PII)
- [x] Requer role `is_admin` ou `is_master`
- [x] Agrupamento por `reason` com contagem (para dashboard futuro)

## Escopo

**IN:**
- Modal de survey no momento de expiração
- Tabela Supabase + RLS
- Endpoint de submit + endpoint admin
- Evento Mixpanel

**OUT:**
- Dashboard visual de analytics (fora desta story)
- Email automático baseado na resposta do survey (fora desta story)
- A/B teste de copy do modal (fora desta story)

## Riscos

- Usuários que nunca acessam o produto após expiração nunca verão o modal → aceitável, o survey é complementar não exaustivo
- Modal pode aumentar fricção antes do paywall → mitigado pelo botão "Pular" e por ser pergunta única

## Arquivos a Criar/Modificar

- [x] `supabase/migrations/20260411000000_trial_exit_surveys.sql` (novo)
- [x] `backend/routes/user.py` (modificar — novos endpoints)
- [x] `frontend/components/TrialExitSurveyModal.tsx` (novo)
- [x] `frontend/app/buscar/page.tsx` (modificar — integração)
- [x] `frontend/app/api/trial/exit-survey/route.ts` (novo — proxy)
- [x] `backend/tests/test_trial_exit_survey.py` (novo)
- [x] `frontend/__tests__/trial-exit-survey.test.tsx` (novo)

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-11 | @sm | Story criada — Conselho de CEOs Advisory Board |
| 2026-04-11 | @po | GO 10/10 — Draft → Ready |
