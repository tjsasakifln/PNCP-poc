# SmartLic Database Schema

**Generated:** 2026-03-30 | **Auditor:** @data-engineer (Dara) -- Brownfield Discovery Phase 2
**Source:** 90+ migration files in `supabase/migrations/`
**Database:** PostgreSQL 17 (Supabase Cloud) | **Extensions:** pg_trgm, pg_cron

---

## Overview

| Metrica | Valor |
|---------|-------|
| Total de tabelas | 28 |
| Tabelas com RLS | 28 (100%) |
| RPC Functions | 12 |
| Triggers | 12 |
| pg_cron Jobs | 9 |
| CHECK Constraints | 25+ |
| Indexes | 80+ |

**Dominio principal:** Plataforma SaaS de inteligencia em licitacoes publicas (B2G).
**Modelo de dados:** Multi-tenant via RLS com `auth.uid()` e `service_role` pattern.
**FK padrao:** Todas as FKs de user_id apontam para `profiles(id)` (padronizadas via migrations 018, 20260225120000, 20260304100000).

---

## Tabelas

### 1. profiles
- **Proposito:** Extensao de `auth.users` -- perfil do usuario, plano, contexto de negocio
- **Migration:** 001, 004, 007, 020, 024, 027, 20260224000000, 20260225100000, 20260225110000, 20260227140000, 20260301200000
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, FK -> auth.users(id) ON DELETE CASCADE | ID do usuario |
| email | text | NOT NULL, UNIQUE (idx_profiles_email_unique) | Email do usuario |
| full_name | text | | Nome completo |
| company | text | | Empresa |
| plan_type | text | NOT NULL, DEFAULT 'free_trial', CHECK (free_trial, consultor_agil, maquina, sala_guerra, master, smartlic_pro, consultoria) | Plano atual |
| is_admin | boolean | NOT NULL, DEFAULT false | Administrador do sistema |
| avatar_url | text | | URL do avatar |
| sector | text | | Setor de atuacao |
| phone_whatsapp | text | CHECK (formato brasileiro 10-11 digitos), UNIQUE parcial (WHERE NOT NULL) | Telefone WhatsApp |
| whatsapp_consent | boolean | DEFAULT false | Consentimento LGPD WhatsApp |
| whatsapp_consent_at | timestamptz | | Timestamp do consentimento |
| context_data | jsonb | DEFAULT '{}', CHECK (pg_column_size < 524288) | Dados do onboarding wizard |
| subscription_status | text | DEFAULT 'trial', CHECK (trial, active, canceling, past_due, expired) | Status da assinatura |
| trial_expires_at | timestamptz | | Fim do trial |
| subscription_end_date | timestamptz | | Fim da assinatura cancelada |
| email_unsubscribed | boolean | DEFAULT false | Opt-out de email |
| email_unsubscribed_at | timestamptz | | Timestamp do opt-out |
| marketing_emails_enabled | boolean | NOT NULL, DEFAULT true | Opt-out de emails marketing |
| referred_by_partner_id | uuid | FK -> partners(id) | Parceiro que indicou |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |
| updated_at | timestamptz | NOT NULL, DEFAULT now() | Auto-update via trigger |

- **Indexes:** idx_profiles_is_admin (parcial), idx_profiles_email_trgm (GIN trigram), idx_profiles_whatsapp_consent (parcial), idx_profiles_context_porte (btree em JSONB), idx_profiles_subscription_status (parcial), idx_profiles_phone_whatsapp_unique, idx_profiles_email_unique, idx_profiles_referred_by_partner
- **RLS:** profiles_select_own (SELECT auth.uid()=id), profiles_update_own (UPDATE), profiles_insert_own (INSERT authenticated), profiles_insert_service (INSERT service_role), profiles_service_all (ALL service_role)
- **Triggers:** profiles_updated_at -> set_updated_at(), on_auth_user_created -> handle_new_user()

---

### 2. plans
- **Proposito:** Catalogo de planos (public, read-only para usuarios)
- **Migration:** 001, 005, 015, 020, 029, 20260226120000, 20260301300000
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | text | PK | Identificador do plano (free, smartlic_pro, consultoria, etc.) |
| name | text | NOT NULL | Nome exibido |
| description | text | | Descricao |
| max_searches | int | | Limite mensal (NULL = ilimitado) |
| price_brl | numeric(10,2) | NOT NULL, DEFAULT 0 | Preco base em BRL |
| duration_days | int | | Duracao (NULL = perpetuo) |
| stripe_price_id | text | | Stripe Price ID legado |
| stripe_price_id_monthly | text | | Stripe Price ID mensal |
| stripe_price_id_semiannual | text | | Stripe Price ID semestral |
| stripe_price_id_annual | text | | Stripe Price ID anual |
| is_active | boolean | NOT NULL, DEFAULT true | Plano ativo no catalogo |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |
| updated_at | timestamptz | NOT NULL, DEFAULT now() | Auto-update via trigger |

- **Planos ativos:** smartlic_pro (R$397/mes), consultoria (R$997/mes), free (trial), master (interno)
- **Planos legado (inativos):** consultor_agil, maquina, sala_guerra, pack_5/10/20, monthly, annual
- **RLS:** plans_select_all (SELECT true -- publico)
- **Triggers:** plans_updated_at -> set_updated_at()

---

### 3. plan_billing_periods
- **Proposito:** Precos por periodo de cobranca (mensal, semestral, anual)
- **Migration:** 029, 20260226120000, 20260301300000
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| plan_id | text | NOT NULL, FK -> plans(id) ON DELETE CASCADE | Plano |
| billing_period | text | NOT NULL, CHECK (monthly, semiannual, annual), UNIQUE(plan_id, billing_period) | Periodo |
| price_cents | integer | NOT NULL | Preco em centavos |
| discount_percent | integer | DEFAULT 0 | Desconto % |
| stripe_price_id | text | | Stripe Price ID |
| created_at | timestamptz | DEFAULT now() | |

- **RLS:** plan_billing_periods_public_read (SELECT authenticated+anon), plan_billing_periods_service_all (ALL service_role)

---

### 4. plan_features
- **Proposito:** Feature flags por plano e periodo de cobranca
- **Migration:** 009, 029, 20260301300000
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | serial | PK | |
| plan_id | text | NOT NULL, FK -> plans(id) ON DELETE CASCADE | |
| billing_period | varchar(10) | NOT NULL, CHECK (monthly, semiannual, annual), UNIQUE(plan_id, billing_period, feature_key) | |
| feature_key | varchar(100) | NOT NULL | Ex: full_access, early_access, multi_user |
| enabled | boolean | NOT NULL, DEFAULT true | |
| metadata | jsonb | DEFAULT '{}', CHECK (pg_column_size < 524288) | Config especifica |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |
| updated_at | timestamptz | NOT NULL, DEFAULT now() | Auto-update via trigger |

- **Indexes:** idx_plan_features_lookup (parcial WHERE enabled)
- **RLS:** plan_features_select_all (SELECT true -- publico)
- **Triggers:** plan_features_updated_at -> set_updated_at()

---

### 5. user_subscriptions
- **Proposito:** Assinaturas ativas/historicas do usuario (Stripe-backed)
- **Migration:** 001, 008, 021, 20260225100000, 20260227120002, 20260227130000
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| user_id | uuid | NOT NULL, FK -> profiles(id) ON DELETE CASCADE | |
| plan_id | text | NOT NULL, FK -> plans(id) ON DELETE RESTRICT | |
| credits_remaining | int | | Creditos restantes (NULL = ilimitado) |
| starts_at | timestamptz | NOT NULL, DEFAULT now() | |
| expires_at | timestamptz | | |
| stripe_subscription_id | text | UNIQUE parcial (WHERE NOT NULL) | |
| stripe_customer_id | text | | |
| is_active | boolean | NOT NULL, DEFAULT true | |
| billing_period | varchar(10) | NOT NULL, DEFAULT 'monthly', CHECK (monthly, semiannual, annual) | |
| annual_benefits | jsonb | NOT NULL, DEFAULT '{}', CHECK (pg_column_size < 524288) | |
| subscription_status | text | DEFAULT 'active', CHECK (active, trialing, past_due, canceled, expired) | |
| first_failed_at | timestamptz | DEFAULT NULL | Primeiro pagamento falho (dunning) |
| updated_at | timestamptz | NOT NULL, DEFAULT now() | |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |

- **Indexes:** idx_user_subscriptions_user, idx_user_subscriptions_active (parcial), idx_user_subscriptions_billing (parcial), idx_user_subscriptions_stripe_sub_id (UNIQUE parcial), idx_user_subscriptions_customer_id (parcial), idx_user_subscriptions_first_failed_at (parcial)
- **RLS:** subscriptions_select_own (SELECT), Service role can manage subscriptions (ALL service_role)
- **Triggers:** user_subscriptions_updated_at -> set_updated_at(), trg_sync_subscription_status -> sync_subscription_status_to_profile()

---

### 6. monthly_quota
- **Proposito:** Contagem mensal de buscas por usuario (lazy reset por mes)
- **Migration:** 002, 018
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| user_id | uuid | NOT NULL, FK -> profiles(id) ON DELETE CASCADE | |
| month_year | varchar(7) | NOT NULL, UNIQUE(user_id, month_year) | Formato YYYY-MM |
| searches_count | int | NOT NULL, DEFAULT 0 | |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |
| updated_at | timestamptz | NOT NULL, DEFAULT now() | |

- **Indexes:** idx_monthly_quota_user_month
- **RLS:** Users can view own quota (SELECT), Service role can manage quota (ALL service_role)
- **Retencao:** pg_cron cleanup-monthly-quota (24 meses, 1o dia do mes 2h UTC)

---

### 7. search_sessions
- **Proposito:** Historico de buscas realizadas pelo usuario (lifecycle completo)
- **Migration:** 001, 20260220120000, 20260221100000, 20260225140000
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| user_id | uuid | NOT NULL, FK -> profiles(id) ON DELETE CASCADE | |
| search_id | uuid | DEFAULT NULL | Link para SSE/ARQ/cache |
| sectors | text[] | NOT NULL | Setores buscados |
| ufs | text[] | NOT NULL | UFs buscadas |
| data_inicial | date | NOT NULL | |
| data_final | date | NOT NULL | |
| custom_keywords | text[] | | |
| total_raw | int | NOT NULL, DEFAULT 0 | |
| total_filtered | int | NOT NULL, DEFAULT 0 | |
| valor_total | numeric(14,2) | DEFAULT 0 | |
| resumo_executivo | text | | |
| destaques | text[] | | |
| excel_storage_path | text | | |
| status | text | NOT NULL, DEFAULT 'created', CHECK (created, processing, completed, failed, timed_out, cancelled) | |
| error_message | text | | |
| error_code | text | | |
| started_at | timestamptz | NOT NULL, DEFAULT now() | |
| completed_at | timestamptz | | |
| duration_ms | integer | | |
| pipeline_stage | text | | Ultimo estagio alcancado |
| raw_count | integer | DEFAULT 0 | |
| response_state | text | | live, cached, degraded, empty_failure |
| failed_ufs | text[] | | UFs que falharam |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |

- **Indexes:** idx_search_sessions_user (user_id), idx_search_sessions_created (user_id, created_at DESC), idx_search_sessions_search_id (parcial), idx_search_sessions_status (parcial WHERE IN created/processing), idx_search_sessions_inflight (parcial), idx_search_sessions_user_status_created (composito)
- **RLS:** sessions_select_own (SELECT), sessions_insert_own (INSERT), Service role can manage search sessions (ALL service_role)

---

### 8. search_state_transitions
- **Proposito:** Audit trail de transicoes de estado do pipeline de busca
- **Migration:** 20260221100002, 20260308320000
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| search_id | uuid | NOT NULL | Correlacao com search_sessions.search_id |
| user_id | uuid | FK -> profiles(id) ON DELETE CASCADE | Adicionado para otimizar RLS |
| from_state | text | | Estado anterior (NULL para CREATED inicial) |
| to_state | text | NOT NULL | Novo estado |
| stage | text | | Estagio do pipeline |
| details | jsonb | DEFAULT '{}', CHECK (pg_column_size < 524288) | Metadata |
| duration_since_previous_ms | integer | | |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |

- **Indexes:** idx_state_transitions_search_id (search_id, created_at ASC), idx_state_transitions_to_state (to_state, created_at)
- **RLS:** Users can read own transitions (SELECT via user_id), Service role can insert transitions (INSERT service_role)
- **Retencao:** pg_cron cleanup-search-state-transitions (30 dias, diario 4h UTC)

---

### 9. search_results_cache
- **Proposito:** Cache persistente L2 (SWR) -- ultimas buscas por usuario
- **Migration:** 026, 027b, 031, 032, 033, 20260223100000, 20260224200000
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| user_id | uuid | NOT NULL, FK -> profiles(id) ON DELETE CASCADE, UNIQUE(user_id, params_hash) | |
| params_hash | text | NOT NULL | Hash dos parametros de busca |
| params_hash_global | text | | Hash global para cache cross-user |
| search_params | jsonb | NOT NULL | Snapshot dos parametros |
| results | jsonb | NOT NULL, CHECK (octet_length <= 2MB) | Resultados cacheados |
| total_results | integer | NOT NULL, DEFAULT 0 | |
| sources_json | jsonb | NOT NULL, DEFAULT '["pncp"]' | Fontes que contribuiram |
| fetched_at | timestamptz | NOT NULL, DEFAULT now() | Quando o fetch ocorreu |
| priority | text | NOT NULL, DEFAULT 'cold', CHECK (hot, warm, cold) | Prioridade no cache |
| access_count | integer | NOT NULL, DEFAULT 0 | |
| last_accessed_at | timestamptz | | |
| last_success_at | timestamptz | | |
| last_attempt_at | timestamptz | | |
| fail_streak | integer | NOT NULL, DEFAULT 0 | |
| degraded_until | timestamptz | | |
| coverage | jsonb | | |
| fetch_duration_ms | integer | | |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |

- **Indexes:** idx_search_cache_user (user_id, created_at DESC), idx_search_cache_params_hash, idx_search_cache_global_hash, idx_search_cache_priority, idx_search_cache_degraded (parcial)
- **RLS:** Users can read own search cache (SELECT), Service role full access (ALL service_role)
- **Triggers:** trg_cleanup_search_cache -> cleanup_search_cache_per_user() (max 10 entries, eviction por prioridade)
- **Retencao:** pg_cron cleanup-cold-cache-entries (7 dias para cold, diario 5h UTC)

---

### 10. search_results_store
- **Proposito:** Armazenamento persistente L3 (24h TTL) -- previne "Busca nao encontrada"
- **Migration:** 20260303100000, 20260304100000, 20260304110000
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| search_id | uuid | PK | |
| user_id | uuid | NOT NULL, FK -> profiles(id) ON DELETE CASCADE | |
| results | jsonb | NOT NULL, CHECK (octet_length < 2MB) | |
| sector | text | | |
| ufs | text[] | | |
| total_filtered | int | DEFAULT 0 | |
| created_at | timestamptz | DEFAULT now() | |
| expires_at | timestamptz | DEFAULT now() + 24h | |

- **Indexes:** idx_search_results_user (user_id), idx_search_results_expires (expires_at), idx_search_results_store_user_expires (composito), idx_search_results_store_user_id
- **RLS:** Users can read own results (SELECT), service_role_all (ALL service_role)
- **Retencao:** pg_cron cleanup-expired-search-results (7 dias apos expiracao, diario 4h UTC)

---

### 11. pipeline_items
- **Proposito:** Pipeline kanban de oportunidades (descoberta -> resultado)
- **Migration:** 025, 027, 20260227120002, 20260315100000
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| user_id | uuid | NOT NULL, FK -> profiles(id) ON DELETE CASCADE, UNIQUE(user_id, pncp_id) | |
| pncp_id | text | NOT NULL | ID da licitacao no PNCP |
| objeto | text | NOT NULL | Objeto da licitacao |
| orgao | text | | |
| uf | text | | |
| valor_estimado | numeric | | |
| data_encerramento | timestamptz | | |
| link_pncp | text | | |
| stage | text | NOT NULL, DEFAULT 'descoberta', CHECK (descoberta, analise, preparando, enviada, resultado) | |
| notes | text | | |
| version | integer | DEFAULT 1, NOT NULL | Optimistic locking |
| search_id | text | | Rastreabilidade (TEXT, nao UUID FK) |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |
| updated_at | timestamptz | NOT NULL, DEFAULT now() | |

- **Indexes:** idx_pipeline_user_stage, idx_pipeline_encerramento (parcial), idx_pipeline_user_created, idx_pipeline_items_user_id, idx_pipeline_items_search_id (parcial)
- **RLS:** Users can view/insert/update/delete own pipeline items (4 policies), Service role full access (ALL service_role)
- **Triggers:** tr_pipeline_items_updated_at -> set_updated_at()

---

### 12. conversations
- **Proposito:** Threads de suporte interno (InMail)
- **Migration:** 012, 20260301400000
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| user_id | uuid | NOT NULL, FK -> profiles(id) ON DELETE CASCADE | |
| subject | text | NOT NULL, CHECK (char_length <= 200) | |
| category | text | NOT NULL, CHECK (suporte, sugestao, funcionalidade, bug, outro) | |
| status | text | NOT NULL, DEFAULT 'aberto', CHECK (aberto, respondido, resolvido) | |
| first_response_at | timestamptz | | SLA tracking |
| last_message_at | timestamptz | NOT NULL, DEFAULT now() | |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |
| updated_at | timestamptz | NOT NULL, DEFAULT now() | |

- **Indexes:** idx_conversations_user_id, idx_conversations_status, idx_conversations_last_message (DESC), idx_conversations_unanswered (parcial)
- **RLS:** conversations_select_own (SELECT user ou admin), conversations_insert_own (INSERT), conversations_update_admin (UPDATE admin), conversations_service_all (ALL service_role)
- **Triggers:** update_conversation_last_message (AFTER INSERT ON messages)

---

### 13. messages
- **Proposito:** Mensagens dentro de conversations
- **Migration:** 012
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| conversation_id | uuid | NOT NULL, FK -> conversations(id) ON DELETE CASCADE | |
| sender_id | uuid | NOT NULL, FK -> profiles(id) ON DELETE CASCADE | |
| body | text | NOT NULL, CHECK (1 <= char_length <= 5000) | |
| is_admin_reply | boolean | NOT NULL, DEFAULT false | |
| read_by_user | boolean | NOT NULL, DEFAULT false | |
| read_by_admin | boolean | NOT NULL, DEFAULT false | |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |

- **Indexes:** idx_messages_conversation (conversation_id, created_at), idx_messages_unread_by_user (parcial), idx_messages_unread_by_admin (parcial)
- **RLS:** messages_select (SELECT via join conversation), messages_insert_user (INSERT), messages_update_read (UPDATE), messages_service_all (ALL service_role)

---

### 14. stripe_webhook_events
- **Proposito:** Idempotencia de webhooks Stripe (dedup por event ID)
- **Migration:** 010, 016, 028, 20260227120001
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | varchar(255) | PK, CHECK (id ~ '^evt_') | Stripe event ID |
| type | varchar(100) | NOT NULL | Tipo do evento |
| processed_at | timestamptz | NOT NULL, DEFAULT now() | |
| payload | jsonb | | Evento completo para debug |
| status | varchar(20) | NOT NULL, DEFAULT 'completed' | processing/completed/failed |
| received_at | timestamptz | DEFAULT now() | Deteccao de eventos stuck |

- **Indexes:** idx_webhook_events_type (type, processed_at), idx_webhook_events_recent (processed_at DESC)
- **RLS:** webhook_events_insert_service (INSERT service_role), webhook_events_select_admin (SELECT authenticated + is_admin), webhook_events_service_role_select (SELECT service_role)
- **Retencao:** pg_cron cleanup-webhook-events (90 dias, diario 3h UTC)

---

### 15. audit_events
- **Proposito:** Log de auditoria persistente (PII como hash SHA-256)
- **Migration:** 023
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| timestamp | timestamptz | NOT NULL, DEFAULT now() | |
| event_type | text | NOT NULL | auth.login, billing.checkout, etc. |
| actor_id_hash | text | | SHA-256 truncado 16 hex chars |
| target_id_hash | text | | |
| details | jsonb | | Metadata sanitizada |
| ip_hash | text | | SHA-256 do IP |

- **Indexes:** idx_audit_events_event_type, idx_audit_events_timestamp, idx_audit_events_actor (parcial), idx_audit_events_type_timestamp (composito)
- **RLS:** Service role can manage audit events (ALL service_role), Admins can read audit events (SELECT is_admin)
- **Retencao:** pg_cron cleanup-audit-events (12 meses, 1o dia do mes 4h UTC)

---

### 16. user_oauth_tokens
- **Proposito:** Tokens OAuth 2.0 encriptados (Google Sheets)
- **Migration:** 013, 018
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| user_id | uuid | NOT NULL, FK -> profiles(id) ON DELETE CASCADE, UNIQUE(user_id, provider) | |
| provider | varchar(50) | NOT NULL, CHECK (google, microsoft, dropbox) | |
| access_token | text | NOT NULL | AES-256 encriptado |
| refresh_token | text | | AES-256 encriptado |
| expires_at | timestamptz | NOT NULL | |
| scope | text | NOT NULL | |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |
| updated_at | timestamptz | NOT NULL, DEFAULT now() | |

- **Indexes:** idx_user_oauth_tokens_user_id, idx_user_oauth_tokens_expires_at
- **RLS:** Users can view/update/delete own OAuth tokens (3 policies), Service role can manage all (ALL service_role)

---

### 17. google_sheets_exports
- **Proposito:** Historico de exportacoes Google Sheets
- **Migration:** 014, 018
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| user_id | uuid | NOT NULL, FK -> profiles(id) ON DELETE CASCADE | |
| spreadsheet_id | varchar(255) | NOT NULL | |
| spreadsheet_url | text | NOT NULL | |
| search_params | jsonb | NOT NULL | Snapshot dos parametros |
| total_rows | int | NOT NULL, CHECK >= 0 | |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |
| last_updated_at | timestamptz | DEFAULT now() | |

- **Indexes:** idx_google_sheets_exports_user_id, idx_google_sheets_exports_created_at (DESC), idx_google_sheets_exports_spreadsheet_id, idx_google_sheets_exports_search_params (GIN)
- **RLS:** Users can view/create/update own exports (3 policies), Service role can manage all (ALL service_role)

---

### 18. classification_feedback
- **Proposito:** Feedback do usuario sobre classificacao IA (relevante/irrelevante)
- **Migration:** 20260308200000 (DEBT-002)
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| user_id | uuid | NOT NULL, FK -> profiles(id) ON DELETE CASCADE | |
| pncp_id | text | NOT NULL | |
| setor_id | text | NOT NULL | |
| user_verdict | text | NOT NULL | relevante/irrelevante |
| original_verdict | text | | Classificacao original do sistema |
| comment | text | | |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |

- **Indexes:** idx_feedback_sector_verdict, idx_feedback_user_created, idx_classification_feedback_user_id
- **RLS:** feedback_insert_own, feedback_select_own, feedback_update_own, feedback_delete_own, service_role_all

---

### 19. alert_preferences
- **Proposito:** Preferencias de alerta por email por usuario
- **Migration:** 20260226100000
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| user_id | uuid | NOT NULL, FK -> profiles(id) ON DELETE CASCADE, UNIQUE | |
| frequency | alert_frequency (enum) | NOT NULL, DEFAULT 'daily' | daily, twice_weekly, weekly, off |
| enabled | boolean | NOT NULL, DEFAULT true | |
| last_digest_sent_at | timestamptz | | |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |
| updated_at | timestamptz | NOT NULL, DEFAULT now() | |

- **Indexes:** idx_alert_preferences_digest_due (parcial WHERE enabled AND frequency != 'off')
- **RLS:** Users can view/insert/update own (3 policies), service_role_all (ALL service_role)
- **Triggers:** trigger_alert_preferences_updated_at -> set_updated_at(), trigger_create_alert_preferences_on_profile (auto-cria para novos usuarios)

---

### 20. alerts
- **Proposito:** Alertas de email definidos pelo usuario (filtros de busca)
- **Migration:** 20260227100000
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| user_id | uuid | NOT NULL, FK -> profiles(id) ON DELETE CASCADE | |
| name | text | NOT NULL, DEFAULT '' | |
| filters | jsonb | NOT NULL, DEFAULT '{}' | {setor, ufs[], valor_min, valor_max, keywords[]} |
| active | boolean | NOT NULL, DEFAULT true | |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |
| updated_at | timestamptz | NOT NULL, DEFAULT now() | |

- **Indexes:** idx_alerts_user_id, idx_alerts_active (parcial WHERE active)
- **RLS:** Users can view/insert/update/delete own (4 policies), Service role full access (ALL service_role)
- **Triggers:** trigger_alerts_updated_at -> set_updated_at()

---

### 21. alert_sent_items
- **Proposito:** Dedup de itens ja enviados por alerta
- **Migration:** 20260227100000
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| alert_id | uuid | NOT NULL, FK -> alerts(id) ON DELETE CASCADE | |
| item_id | text | NOT NULL, UNIQUE(alert_id, item_id) | |
| sent_at | timestamptz | NOT NULL, DEFAULT now() | |

- **Indexes:** idx_alert_sent_items_dedup (UNIQUE), idx_alert_sent_items_alert_id, idx_alert_sent_items_sent_at
- **RLS:** Service role full access (ALL service_role), Users can view own alert sent items (SELECT via join)
- **Retencao:** pg_cron cleanup (180 dias, diario 4:05 UTC)

---

### 22. alert_runs
- **Proposito:** Historico de execucoes de alertas (debugging/auditoria)
- **Migration:** 20260228100000
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| alert_id | uuid | NOT NULL, FK -> alerts(id) ON DELETE CASCADE | |
| run_at | timestamptz | NOT NULL, DEFAULT now() | |
| items_found | integer | NOT NULL, DEFAULT 0 | |
| items_sent | integer | NOT NULL, DEFAULT 0 | |
| status | text | NOT NULL, DEFAULT 'pending', CHECK (matched, no_results, no_match, all_deduped, error, pending) | |

- **Indexes:** idx_alert_runs_alert_id, idx_alert_runs_run_at (DESC)
- **RLS:** Service role full access (ALL service_role), Users can view own alert runs (SELECT via join)
- **Retencao:** pg_cron cleanup (90 dias, diario 4:25 UTC)

---

### 23. trial_email_log
- **Proposito:** Idempotencia de emails da sequencia trial (6 emails, 14 dias)
- **Migration:** 20260224100000, 20260227140000, 20260228110000
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| user_id | uuid | NOT NULL, FK -> profiles(id) ON DELETE CASCADE | |
| email_type | text | NOT NULL | midpoint, expiring, last_day, expired |
| email_number | integer | CHECK (1 <= n <= 6), UNIQUE(user_id, email_number) | |
| sent_at | timestamptz | NOT NULL, DEFAULT now() | |
| opened_at | timestamptz | | Resend webhook |
| clicked_at | timestamptz | | Resend webhook |
| resend_email_id | text | | Resend email ID |

- **Indexes:** idx_trial_email_log_user_id, idx_trial_email_log_resend_id (parcial)
- **RLS:** RLS habilitado, service_role only (sem policies de usuario direto), Users can view own trial emails (SELECT)

---

### 24. reconciliation_log
- **Proposito:** Log de reconciliacao Stripe <-> DB
- **Migration:** 20260228140000
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| run_at | timestamptz | NOT NULL, DEFAULT now() | |
| total_checked | int | NOT NULL, DEFAULT 0 | |
| divergences_found | int | NOT NULL, DEFAULT 0 | |
| auto_fixed | int | NOT NULL, DEFAULT 0 | |
| manual_review | int | NOT NULL, DEFAULT 0 | |
| duration_ms | int | NOT NULL, DEFAULT 0 | |
| details | jsonb | DEFAULT '[]' | |

- **Indexes:** idx_reconciliation_log_run_at (DESC)
- **RLS:** Admin read reconciliation_log (SELECT is_admin), service_role_all (ALL service_role)
- **Retencao:** pg_cron (90 dias, diario 4:30 UTC)

---

### 25. health_checks
- **Proposito:** Resultados de health checks periodicos
- **Migration:** 20260228150000, 20260303200000
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| checked_at | timestamptz | NOT NULL, DEFAULT now() | |
| overall_status | text | NOT NULL, CHECK (healthy, degraded, unhealthy) | |
| sources_json | jsonb | NOT NULL, DEFAULT '{}' | |
| components_json | jsonb | NOT NULL, DEFAULT '{}' | |
| latency_ms | integer | | |

- **Indexes:** idx_health_checks_checked_at (DESC)
- **RLS:** service_role_all (ALL service_role)
- **Retencao:** pg_cron (30 dias, diario 4:10 UTC)

---

### 26. incidents
- **Proposito:** Incidentes do sistema (pagina de status)
- **Migration:** 20260228150001, 20260303200000
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| started_at | timestamptz | NOT NULL, DEFAULT now() | |
| resolved_at | timestamptz | | |
| status | text | NOT NULL, DEFAULT 'ongoing', CHECK (ongoing, resolved) | |
| affected_sources | text[] | NOT NULL, DEFAULT '{}' | |
| description | text | NOT NULL, DEFAULT '' | |

- **Indexes:** idx_incidents_status (parcial WHERE ongoing), idx_incidents_started_at (DESC)
- **RLS:** service_role_all (ALL service_role)
- **Retencao:** pg_cron (90 dias, diario 4:15 UTC)

---

### 27. organizations + organization_members
- **Proposito:** Contas multi-usuario para consultorias
- **Migration:** 20260301100000

**organizations:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| name | text | NOT NULL | |
| logo_url | text | | |
| owner_id | uuid | NOT NULL, FK -> profiles(id) ON DELETE RESTRICT | |
| max_members | int | NOT NULL, DEFAULT 5 | |
| plan_type | text | NOT NULL, DEFAULT 'consultoria' | |
| stripe_customer_id | text | | |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |
| updated_at | timestamptz | NOT NULL, DEFAULT now() | |

**organization_members:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| org_id | uuid | NOT NULL, FK -> organizations(id) ON DELETE CASCADE, UNIQUE(org_id, user_id) | |
| user_id | uuid | NOT NULL, FK -> profiles(id) ON DELETE CASCADE | |
| role | text | NOT NULL, DEFAULT 'member', CHECK (owner, admin, member) | |
| invited_at | timestamptz | NOT NULL, DEFAULT now() | |
| accepted_at | timestamptz | | NULL = pendente |

- **Indexes:** idx_organizations_owner, idx_org_members_org, idx_org_members_user
- **RLS (organizations):** Org owner can view, Org admins can view, Owner can insert/update, service_role_all
- **RLS (organization_members):** Users can view own membership, Org owner/admin can view all/insert/delete, Users can leave (delete own), service_role_all

---

### 28. partners + partner_referrals
- **Proposito:** Revenue share tracking -- parceiros e indicacoes
- **Migration:** 20260301200000

**partners:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| name | text | NOT NULL | |
| slug | text | UNIQUE, NOT NULL | |
| contact_email | text | NOT NULL | |
| contact_name | text | | |
| stripe_coupon_id | text | | |
| revenue_share_pct | numeric(5,2) | DEFAULT 25.00 | |
| status | text | DEFAULT 'active', CHECK (active, inactive, pending) | |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |

**partner_referrals:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| partner_id | uuid | NOT NULL, FK -> partners(id) | |
| referred_user_id | uuid | FK -> profiles(id) ON DELETE SET NULL (nullable) | |
| signup_at | timestamptz | DEFAULT now() | |
| converted_at | timestamptz | | |
| churned_at | timestamptz | | |
| monthly_revenue | numeric(10,2) | | |
| revenue_share_amount | numeric(10,2) | | |

- **Indexes:** idx_partners_slug, idx_partners_status, idx_partner_referrals_partner_id, idx_partner_referrals_referred_user_id
- **RLS (partners):** partners_admin_all (ALL is_admin), partners_self_read (SELECT own by email), service_role_all
- **RLS (partner_referrals):** partner_referrals_admin_all, partner_referrals_partner_read (via join), service_role_all

---

### 29. mfa_recovery_codes + mfa_recovery_attempts
- **Proposito:** Codigos de recuperacao MFA (TOTP backup)
- **Migration:** 20260228160000

**mfa_recovery_codes:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK | |
| user_id | uuid | NOT NULL, FK -> profiles(id) ON DELETE CASCADE | |
| code_hash | text | NOT NULL | bcrypt hash |
| used_at | timestamptz | DEFAULT NULL | |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |

**mfa_recovery_attempts:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | uuid | PK | |
| user_id | uuid | NOT NULL, FK -> profiles(id) ON DELETE CASCADE | |
| attempted_at | timestamptz | NOT NULL, DEFAULT now() | |
| success | boolean | NOT NULL, DEFAULT false | |

- **RLS:** Users can view own recovery codes (SELECT authenticated), Service role full access (ALL service_role)
- **Retencao:** pg_cron cleanup-mfa-recovery-attempts (30 dias, diario 4:20 UTC)

---

### 30. pncp_raw_bids (Data Lake)
- **Proposito:** Dados brutos de licitacoes ingeridos do PNCP (Layer 1)
- **Migration:** 20260326000000
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| pncp_id | text | PK | ID unico no PNCP |
| objeto_compra | text | NOT NULL | Objeto da compra |
| valor_total_estimado | numeric(18,2) | | |
| modalidade_id | integer | NOT NULL | |
| modalidade_nome | text | | |
| situacao_compra | text | | |
| esfera_id | text | | Federal/Estadual/Municipal |
| uf | text | NOT NULL | |
| municipio | text | | |
| codigo_municipio_ibge | text | | |
| orgao_razao_social | text | | |
| orgao_cnpj | text | | |
| unidade_nome | text | | |
| data_publicacao | timestamptz | | |
| data_abertura | timestamptz | | |
| data_encerramento | timestamptz | | |
| link_sistema_origem | text | | |
| link_pncp | text | | |
| content_hash | text | NOT NULL | MD5 para dedup |
| ingested_at | timestamptz | NOT NULL, DEFAULT now() | |
| updated_at | timestamptz | NOT NULL, DEFAULT now() | |
| source | text | NOT NULL, DEFAULT 'pncp' | |
| crawl_batch_id | text | | Link para ingestion_runs |
| is_active | boolean | NOT NULL, DEFAULT true | Flag de atividade. FALSE = marcado para purge. purge_old_bids() executa hard DELETE periodicamente (12 dias de retencao). |

- **Indexes:** idx_pncp_raw_bids_fts (GIN full-text Portuguese), idx_pncp_raw_bids_uf_date (parcial WHERE is_active), idx_pncp_raw_bids_modalidade (parcial), idx_pncp_raw_bids_valor (parcial), idx_pncp_raw_bids_esfera (parcial), idx_pncp_raw_bids_encerramento (parcial), idx_pncp_raw_bids_content_hash, idx_pncp_raw_bids_ingested_at (DESC)
- **RLS:** pncp_raw_bids_select_authenticated (SELECT authenticated -- dados publicos), pncp_raw_bids_insert/update/delete_service (service_role)
- **Triggers:** trg_pncp_raw_bids_updated_at -> set_updated_at()
- **Retencao:** purge_old_bids() RPC (12 dias, chamada via ARQ cron)

---

### 31. ingestion_checkpoints
- **Proposito:** Progresso de crawl por UF/modalidade (resumable crawls)
- **Migration:** 20260326000000
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | bigint | PK (GENERATED ALWAYS AS IDENTITY) | |
| source | text | NOT NULL, DEFAULT 'pncp' | |
| uf | text | NOT NULL | |
| modalidade_id | integer | NOT NULL | |
| last_date | date | NOT NULL | |
| last_page | integer | DEFAULT 1 | |
| records_fetched | integer | DEFAULT 0 | |
| status | text | NOT NULL, DEFAULT 'pending', CHECK (pending, running, completed, failed) | |
| error_message | text | | |
| started_at | timestamptz | | |
| completed_at | timestamptz | | |
| crawl_batch_id | text | NOT NULL, UNIQUE(source, uf, modalidade_id, crawl_batch_id) | |

- **Indexes:** idx_ingestion_checkpoints_batch, idx_ingestion_checkpoints_uf_mod
- **RLS:** ingestion_checkpoints_select_authenticated (SELECT), ingestion_checkpoints_write_service (ALL service_role)

---

### 32. ingestion_runs
- **Proposito:** Ledger de batches de ingestao (monitoramento)
- **Migration:** 20260326000000
- **Colunas:**

| Coluna | Tipo | Constraints | Descricao |
|--------|------|-------------|-----------|
| id | bigint | PK (GENERATED ALWAYS AS IDENTITY) | |
| crawl_batch_id | text | UNIQUE, NOT NULL | |
| run_type | text | NOT NULL, CHECK (full, incremental) | |
| status | text | NOT NULL, DEFAULT 'running', CHECK (running, completed, failed, partial) | |
| started_at | timestamptz | NOT NULL, DEFAULT now() | |
| completed_at | timestamptz | | |
| total_fetched | integer | NOT NULL, DEFAULT 0 | |
| inserted | integer | NOT NULL, DEFAULT 0 | |
| updated | integer | NOT NULL, DEFAULT 0 | |
| unchanged | integer | NOT NULL, DEFAULT 0 | |
| errors | integer | NOT NULL, DEFAULT 0 | |
| ufs_completed | text[] | | |
| ufs_failed | text[] | | |
| duration_s | numeric(10,1) | | |
| metadata | jsonb | NOT NULL, DEFAULT '{}' | |

- **Indexes:** idx_ingestion_runs_started (DESC), idx_ingestion_runs_status (parcial WHERE IN running/failed)
- **RLS:** ingestion_runs_select_authenticated (SELECT), ingestion_runs_write_service (ALL service_role)

---

## RPC Functions

| Funcao | Proposito | SECURITY | Grants |
|--------|-----------|----------|--------|
| `handle_new_user()` | Auto-cria profile no signup (trigger on auth.users INSERT) | DEFINER | N/A (trigger) |
| `set_updated_at()` | Trigger generico para updated_at = now() | N/A | N/A (trigger) |
| `update_updated_at()` | Versao antiga (removida em DEBT-001, substituida por set_updated_at) | N/A | Removida |
| `increment_quota_atomic(uuid, varchar, int)` | Incremento atomico de quota mensal | N/A | service_role |
| `check_and_increment_quota(uuid, varchar, int)` | Check + increment atomico (primary path) | N/A | service_role |
| `increment_quota_fallback_atomic(uuid, text, int)` | Fallback atomico para quota | N/A | service_role |
| `get_user_billing_period(uuid)` | Retorna periodo de cobranca do usuario | DEFINER | N/A |
| `user_has_feature(uuid, varchar)` | Verifica se usuario tem feature especifica | DEFINER | N/A |
| `get_user_features(uuid)` | Retorna array de features do usuario | DEFINER | N/A |
| `get_conversations_with_unread_count(uuid, bool, text, int, int)` | Conversations com contagem de nao lidos (elimina N+1) | DEFINER | N/A |
| `get_analytics_summary(uuid, timestamptz, timestamptz)` | Resumo analytics por usuario | DEFINER | N/A |
| `get_table_columns_simple(text)` | Validacao de schema (lista colunas) | DEFINER | authenticated, service_role |
| `cleanup_search_cache_per_user()` | Eviction do cache (max 10, prioridade hot>warm>cold) | DEFINER | N/A (trigger) |
| `update_conversation_last_message()` | Atualiza last_message_at em conversations | N/A | N/A (trigger) |
| `create_default_alert_preferences()` | Auto-cria alert_preferences para novos profiles | N/A | N/A (trigger) |
| `sync_subscription_status_to_profile()` | Sync subscription_status -> profiles | N/A | N/A (trigger) |
| `upsert_pncp_raw_bids(jsonb)` | Bulk upsert de bids do PNCP (content_hash dedup) | DEFINER | service_role |
| `search_datalake(text[], date, date, text, int[], numeric, numeric, text[], text, int)` | Busca full-text no data lake (FTS Portuguese + filtros) | DEFINER | authenticated, service_role |
| `purge_old_bids(int)` | Remove bids com data_publicacao > N dias | DEFINER | service_role |

---

## pg_cron Jobs

| Job | Schedule | Retencao | Tabela |
|-----|----------|----------|--------|
| cleanup-monthly-quota | 0 2 1 * * (1o dia, 2h UTC) | 24 meses | monthly_quota |
| cleanup-webhook-events | 0 3 * * * (diario, 3h UTC) | 90 dias | stripe_webhook_events |
| cleanup-audit-events | 0 4 1 * * (1o dia, 4h UTC) | 12 meses | audit_events |
| cleanup-cold-cache-entries | 0 5 * * * (diario, 5h UTC) | 7 dias (cold) | search_results_cache |
| cleanup-expired-search-results | 0 4 * * * (diario, 4h UTC) | 7 dias apos expirar | search_results_store |
| cleanup-search-state-transitions | 0 4 * * * (diario, 4h UTC) | 30 dias | search_state_transitions |
| cleanup-alert-sent-items | diario, 4:05 UTC | 180 dias | alert_sent_items |
| cleanup-health-checks | diario, 4:10 UTC | 30 dias | health_checks |
| cleanup-incidents | diario, 4:15 UTC | 90 dias | incidents |
| cleanup-mfa-recovery-attempts | diario, 4:20 UTC | 30 dias | mfa_recovery_attempts |
| cleanup-alert-runs | diario, 4:25 UTC | 90 dias (completed) | alert_runs |
| cleanup-reconciliation-log | diario, 4:30 UTC | 90 dias | reconciliation_log |

---

## Relacionamentos Chave (ER)

```
auth.users (1) ---> (1) profiles (hub central)
    profiles (1) ---> (N) user_subscriptions
    profiles (1) ---> (N) search_sessions
    profiles (1) ---> (N) monthly_quota
    profiles (1) ---> (N) pipeline_items
    profiles (1) ---> (N) conversations ---> (N) messages
    profiles (1) ---> (N) classification_feedback
    profiles (1) ---> (N) search_results_cache
    profiles (1) ---> (N) search_results_store
    profiles (1) ---> (N) user_oauth_tokens
    profiles (1) ---> (N) google_sheets_exports
    profiles (1) ---> (1) alert_preferences
    profiles (1) ---> (N) alerts ---> (N) alert_sent_items
                                  ---> (N) alert_runs
    profiles (1) ---> (N) trial_email_log
    profiles (1) ---> (N) mfa_recovery_codes
    profiles (1) ---> (N) mfa_recovery_attempts
    profiles (1) ---> (N) search_state_transitions
    profiles (1) ---> (N) organizations (owner_id, ON DELETE RESTRICT)
    profiles (1) ---> (N) organization_members
    plans    (1) ---> (N) plan_billing_periods
    plans    (1) ---> (N) plan_features
    plans    (1) ---> (N) user_subscriptions (ON DELETE RESTRICT)
    partners (1) ---> (N) partner_referrals
    partners (1) ---> (N) profiles (referred_by_partner_id)

    -- Data Lake (sem FK para profiles)
    pncp_raw_bids (standalone, PK=pncp_id)
    ingestion_checkpoints (link logico via crawl_batch_id)
    ingestion_runs (PK=crawl_batch_id)

    -- Observabilidade (sem FK para profiles)
    audit_events (PII como hash)
    health_checks (service_role only)
    incidents (service_role only)
    reconciliation_log (admin only)
    stripe_webhook_events (PK=evt_*)
```

---

## Extensions Requeridas

| Extension | Proposito |
|-----------|-----------|
| pg_trgm | ILIKE search via GIN trigram index (profiles.email) |
| pg_cron | Scheduled cleanup jobs (12 jobs) |

---

## Custom Types

| Type | Valores | Tabela |
|------|---------|--------|
| alert_frequency (ENUM) | daily, twice_weekly, weekly, off | alert_preferences |
