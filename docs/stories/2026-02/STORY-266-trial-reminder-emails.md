# STORY-266 — Emails de Lembrete e Conversão do Trial

**Status:** DONE
**Sprint:** GTM-TRIAL
**Priority:** P1 — Conversão
**Estimate:** 5 SP
**Squad:** team-bidiq-backend

---

## Contexto

Com trial completo (STORY-264) e bloqueio hard (STORY-265), precisamos de uma **cadeia de emails** que guie o usuário para conversão. Hoje existem apenas emails de quota (80% e 100%), mas nenhum email específico de expiração do trial. O objetivo é criar urgência progressiva com dados concretos de valor descoberto.

## Objetivo

Implementar cadeia de 4 emails automáticos durante e após o trial, com dados personalizados do uso real do usuário.

## Cadeia de Emails

| Dia | Tipo | Assunto | Objetivo |
|-----|------|---------|----------|
| **Dia 3** | Meio do trial | "Você já analisou R$X em oportunidades" | Mostrar valor, incentivar uso |
| **Dia 5** | 2 dias restantes | "Seu acesso completo ao SmartLic acaba em 2 dias" | Criar urgência moderada |
| **Dia 6** | Último dia | "Amanhã seu acesso expira — não perca o que você construiu" | Urgência máxima |
| **Dia 8** | 1 dia após expirar | "Suas X oportunidades estão esperando por você" | Reengajamento |

## Acceptance Criteria

### Backend — Templates de Email

- [x] **AC1**: Template `render_trial_midpoint_email(user_name, stats)` — Dia 3
  - Dados: total de buscas realizadas, oportunidades encontradas, valor total estimado
  - CTA: "Continuar descobrindo oportunidades" → `/buscar`
  - Tom: celebratório, mostrar progresso

- [x] **AC2**: Template `render_trial_expiring_email(user_name, days_remaining, stats)` — Dia 5
  - Dados: oportunidades encontradas, valor total, itens no pipeline
  - CTA: "Garantir acesso contínuo" → `/planos`
  - Tom: informativo com urgência leve

- [x] **AC3**: Template `render_trial_last_day_email(user_name, stats)` — Dia 6
  - Dados: resumo completo do trial (buscas, oportunidades, valor, pipeline)
  - CTA: "Ativar SmartLic Pro — R$1.999/mês" → `/planos`
  - Tom: urgência alta, "amanhã perde acesso"
  - Incluir: preço com desconto anual como alternativa

- [x] **AC4**: Template `render_trial_expired_email(user_name, stats)` — Dia 8
  - Dados: oportunidades salvas no pipeline, valor total descoberto
  - CTA: "Reativar acesso" → `/planos`
  - Tom: reengajamento, "suas oportunidades estão esperando"
  - Incluir: "seus dados ficam salvos por 30 dias"

### Backend — Coleta de Stats do Trial

- [x] **AC5**: Função `get_trial_usage_stats(user_id) -> TrialUsageStats` em novo módulo ou em `quota.py`
  - Retorna: `searches_count`, `opportunities_found`, `total_value_estimated`, `pipeline_items_count`, `sectors_searched`
  - Consulta: `monthly_quota` (buscas), `search_history` (oportunidades + valor), `user_pipeline` (itens)

- [x] **AC6**: `TrialUsageStats` é um Pydantic model reutilizável por templates e API

### Backend — Agendamento (Cron Job)

- [x] **AC7**: Job `check_trial_reminders()` em `cron_jobs.py` — executa 1x/dia (manhã, ~9h BRT)
- [x] **AC8**: Query: buscar todos os users com `plan_type='free_trial'` e `created_at` nos marcos (dia 3, 5, 6, 8)
- [x] **AC9**: Idempotência: tabela `email_sent_log` ou campo em profiles para registrar emails já enviados (evitar duplicatas)
- [x] **AC10**: Flag `TRIAL_EMAILS_ENABLED` em config.py (default: true) — permite desligar sem deploy

### Backend — Envio

- [x] **AC11**: Usar `send_email_async()` existente (fire-and-forget, retry 3x)
- [x] **AC12**: Log estruturado: `logger.info("trial_email_sent", user_id=..., email_type=..., day=...)`
- [x] **AC13**: Métrica Prometheus: `trial_emails_sent_total{type=midpoint|expiring|last_day|expired}` (counter)

### Migração (Supabase)

- [x] **AC14**: Migration para tabela `trial_email_log`:
  ```sql
  CREATE TABLE trial_email_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    email_type TEXT NOT NULL, -- midpoint, expiring, last_day, expired
    sent_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, email_type)
  );
  ```
- [x] **AC15**: RLS: service_role only (backend acessa via service key)

### Testes

- [x] **AC16**: Teste unitário para cada template (renderiza sem erro, contém dados corretos)
- [x] **AC17**: Teste para `get_trial_usage_stats()` com dados mock
- [x] **AC18**: Teste para `check_trial_reminders()` — identifica corretamente usuários em cada marco
- [x] **AC19**: Teste de idempotência — rodar job 2x no mesmo dia não envia email duplicado
- [x] **AC20**: Teste com trial que não fez nenhuma busca (stats zeradas — mensagem adaptada)

---

## Notas Técnicas

- **Cron job**: Se ARQ worker estiver ativo, agendar via ARQ cron; senão, usar cron_jobs.py existente com scheduling manual
- **Stats query**: Considerar cache de 1h para stats do trial (evitar queries repetidas)
- **Timezone**: Todos os cálculos de "dia X do trial" devem usar `created_at` do profiles em UTC, comparando com `datetime.now(timezone.utc)`
- **Limite de envio Resend**: Free tier = 100 emails/dia, 3000/mês. Suficiente para beta, mas monitorar
- **Fallback**: Se stats estiverem zeradas (usuário não usou), adaptar copy: "Você ainda tem X dias para descobrir oportunidades"
- **Anti-spam**: Respeitar `EMAIL_ENABLED` flag + rate limit global

## Dependências

- **STORY-264**: Precisa estar implementada (trial com acesso completo) para que os emails façam sentido
- **email_service.py**: Já existe e funciona (Resend + retry)
- **templates/emails/**: Padrão existente (welcome.py, quota.py) como referência de estilo

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `backend/templates/emails/trial.py` | NOVO — 4 templates de email |
| `backend/cron_jobs.py` | Adicionar check_trial_reminders() |
| `backend/quota.py` ou `backend/services/trial.py` | get_trial_usage_stats() |
| `backend/config.py` | TRIAL_EMAILS_ENABLED flag |
| `backend/metrics.py` | trial_emails_sent_total counter |
| `supabase/migrations/XXXXXX_trial_email_log.sql` | NOVO — tabela de log |
| `backend/tests/test_trial_emails.py` | NOVO — testes completos |
| `backend/tests/test_trial_usage_stats.py` | NOVO — testes de stats |
