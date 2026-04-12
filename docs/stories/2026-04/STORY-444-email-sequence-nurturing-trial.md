# STORY-444: Email Sequence de Nurturing (5 Emails ao Longo do Trial)

**Priority:** P1 — Reativa trials abandonados + cria urgência progressiva
**Effort:** M (3-4 dias)
**Squad:** @dev + @qa
**Status:** Ready
**Epic:** [EPIC-CONVERSION-2026-04](EPIC-CONVERSION-2026-04.md)
**Sprint:** Sprint 2 — Semanas 3-4

---

## Contexto

Atualmente existem apenas 3 comunicações durante o trial: welcome email (Supabase Auth automático), reminder Day 7, e reminder Day 13. Não há sequência de nurturing que guie o usuário durante o trial, mostre casos de uso, e crie urgência progressiva baseada em comportamento.

Benchmarks B2B SaaS mostram que sequências de nurturing de 4-6 emails durante o trial aumentam conversão em +1-2pp — especialmente quando incluem dados personalizados do setor/UF do usuário.

**Impacto estimado:** +1-2pp em trial-to-paid conversion.

---

## Acceptance Criteria

### AC1: Email Day 1 — Boas-vindas + Tour (1h após signup)
- [x] Assunto: "Seu SmartLic está pronto — veja como configurar sua primeira busca"
- [x] Conteúdo: saudação com nome do usuário + link para o produto + destacar 3 features principais + link para guided tour (se STORY-442 implementada, caso contrário link direto para /buscar)
- [x] Template: `trial_welcome_tour.html`
- [x] Enviado 1 hora após criação do usuário (não imediatamente)

### AC2: Email Day 3 — Insight do setor/UF do usuário
- [x] Assunto: "Editais de [setor] em [UF] esta semana — veja o que encontramos"
- [x] Conteúdo: dados reais do datalake — quantidade de editais abertos no setor+UF do usuário nos últimos 3 dias + valor total + CTA "Ver todos os editais →"
- [x] Template: `trial_day3_sector_insight.html`
- [x] Dados personalizados: buscar de `pncp_raw_bids` WHERE setor LIKE keywords AND uf IN profile_ufs (últimas 72h)
- [x] Se usuário não tiver setor configurado no perfil: usar setor genérico "do seu mercado"

### AC3: Email Day 5 — Case de uso do setor
- [x] Assunto: "Como empresas de [setor] encontram oportunidades que perderiam sem o SmartLic"
- [x] Conteúdo: narrativa de caso de uso fictício mas realista para o setor do usuário + dados de mercado (ex: "SC tem X editais de TI por mês") + CTA para busca
- [x] Template: `trial_day5_case.html`
- [x] 1 template genérico parametrizado com tokens `{setor}` e `{uf}` — NÃO criar 15 variações por setor (escopo V2). Se setor não disponível no perfil, usar "do seu mercado".

### AC4: Email Day 10 — Resumo do valor do trial
- [x] Assunto: "Você analisou X oportunidades no SmartLic — veja seu resumo"
- [x] Conteúdo: dados reais do usuário (total de buscas, total de editais encontrados, valor estimado) + CTA "Continue com SmartLic Pro →"
- [x] Template: `trial_day10_value_summary.html`
- [x] Dados: buscar do analytics endpoint (`/v1/analytics/trial-value` por usuário)
- [x] Se usuário não fez nenhuma busca: email de reativação "Ainda não testou? Aqui está como começar"

### AC5: Email Day 12 — Urgência (48h antes do fim)
- [x] Assunto: "⏰ Seu trial encerra em 48h — garanta acesso ao SmartLic Pro"
- [x] Conteúdo: lista dos benefícios que serão perdidos + preço Pro (R$397/mês) + CTA "Assinar agora →" com link direto para checkout
- [x] Template: `trial_day12_urgency.html`
- [x] Link de checkout: `/planos` (não link direto Stripe — pode mudar)

### AC6: Emails existentes preservados
- [x] Emails Day 7 ("Faltam 7 dias") e Day 13 ("Seu trial encerra amanhã") existentes são mantidos sem alteração
- [x] Nenhum email existente é removido ou alterado

### AC7: Configuração como cron jobs
- [x] 5 novos cron jobs em `backend/jobs/cron/notifications.py` (ou arquivo dedicado)
- [x] Jobs executam diariamente e enviam para usuários que estão no dia correto do trial
- [x] Lógica de "dia N": `(today - user.created_at).days == N`
- [x] Emails enviados via Resend (provider atual) usando `email_service.py`

### AC8: Cancelamento automático após upgrade
- [x] Antes de enviar qualquer email nurturing, verificar se `profile.plan_type != "free_trial"`
- [x] Se usuário já fez upgrade: não enviar o email e continuar para o próximo usuário
- [x] Logs: registrar emails enviados e pulados com motivo

### AC9: Templates HTML
- [x] Todos os templates em `backend/templates/emails/`
- [x] Herdam header/footer do template base existente
- [x] Responsivos (verificar template base existente para padrão)
- [x] Texto simples (plain text) como fallback

### AC10: Testes
- [x] Teste unitário para cada template: render com dados mock → HTML válido sem erros
- [x] Teste para lógica de cancelamento: usuário paid → email não enviado
- [x] Teste para cálculo de dias: usuário criado há 3 dias → recebe Day 3
- [x] Teste para Day 3 com dados de setor: template renderizado com dados corretos

---

## Scope

**IN:**
- 5 novos templates HTML de email
- 5 novos cron jobs em notifications.py
- Lógica de cancelamento após upgrade
- Query de dados reais para Day 3 e Day 10

**OUT:**
- A/B test de assuntos (futuro)
- Sequência para usuários pagantes (fora do escopo)
- Emails de abandono de checkout (→ futuro)
- Alteração dos emails Day 7 e Day 13 existentes
- Unsubscribe customizado (usar o da Resend)

---

## Dependencies

- `email_service.py` (existente) — verificar API de envio
- `backend/jobs/cron/notifications.py` (existente) — estender
- Resend configurado com domínio `smartlic.tech` (verificar variável `RESEND_API_KEY`)
- Template base de email (verificar `backend/templates/emails/` para estrutura existente)
- `pncp_raw_bids` — para dados do Day 3 (query por setor/UF)
- `/v1/analytics/trial-value` — para dados do Day 10

---

## Risks

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| Resend free tier limita envios (1 domínio, 3k emails/mês) | Média | Verificar limites; com poucos trial users ativos não deve ser problema ainda |
| Dados de setor não disponíveis para Day 3 | Média | Template fallback sem dados específicos se perfil incompleto |
| Cron jobs executando múltiplas vezes → emails duplicados | Baixa | Usar tabela de log de emails enviados ou flag Redis para deduplicação |

---

## File List

- [x] `backend/jobs/cron/notifications.py` — AC7, AC8: 5 novos cron jobs + lógica de cancelamento
- [x] `backend/templates/emails/trial_welcome_tour.html` — AC1: template Day 1
- [x] `backend/templates/emails/trial_day3_sector_insight.html` — AC2: template Day 3
- [x] `backend/templates/emails/trial_day5_case.html` — AC3: template Day 5
- [x] `backend/templates/emails/trial_day10_value_summary.html` — AC4: template Day 10
- [x] `backend/templates/emails/trial_day12_urgency.html` — AC5: template Day 12
- [x] `backend/tests/test_nurturing_sequence.py` — AC10: testes unitários

---

## Dev Notes

- Verificar `backend/jobs/cron/notifications.py` existente para entender o padrão de cron jobs e como os Day 7/Day 13 já são implementados
- Query Day 3: `SELECT COUNT(*), SUM(valor_estimado) FROM pncp_raw_bids WHERE setor = :setor AND uf = ANY(:ufs) AND data_publicacao > NOW() - INTERVAL '72 hours'`
- Deduplicação simples: Redis key `email_sent:{user_id}:day_{N}` com TTL 48h — se key existe, não enviar
- Verificar se `email_service.py` tem método `send_template_email(to, template_name, context)` ou similar

---

## Change Log

| Data | Agente | Mudança |
|------|--------|---------|
| 2026-04-12 | @sm | Story criada — CEO Board Sprint, impacto +1-2pp |
| 2026-04-12 | @po | GO — Ressalva: AC3 simplificado para 1 template genérico parametrizado (não 15 variações). Esforço mantido em M. |
