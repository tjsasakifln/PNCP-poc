-- DEBT-207: RLS Policy Naming Standardization
-- Convention: {action}_{table}_{role}
--   action: select, insert, update, delete, all
--   table: exact table name
--   role: owner (auth.uid()=user_id), authenticated, service, admin, public, self
--
-- Uses ALTER POLICY ... RENAME TO (metadata-only, no behavior change).
-- Wrapped in DO blocks with EXCEPTION handling for idempotency.

-- Helper: safe rename that ignores missing policies
CREATE OR REPLACE FUNCTION pg_temp.safe_rename_policy(
  p_table TEXT, p_old TEXT, p_new TEXT
) RETURNS VOID AS $$
BEGIN
  EXECUTE format('ALTER POLICY %I ON public.%I RENAME TO %I', p_old, p_table, p_new);
EXCEPTION
  WHEN undefined_object THEN NULL;  -- policy doesn't exist, skip
  WHEN duplicate_object THEN NULL;  -- target name already exists, skip
END;
$$ LANGUAGE plpgsql;

-- ══════════════════════════════════════════════════════════════════
-- monthly_quota
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('monthly_quota', 'Users can view own quota', 'select_monthly_quota_owner');
SELECT pg_temp.safe_rename_policy('monthly_quota', 'Service role can manage quota', 'all_monthly_quota_service');

-- ══════════════════════════════════════════════════════════════════
-- profiles
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('profiles', 'profiles_insert_own', 'insert_profiles_owner');
SELECT pg_temp.safe_rename_policy('profiles', 'profiles_insert_service', 'insert_profiles_service');
SELECT pg_temp.safe_rename_policy('profiles', 'profiles_service_all', 'all_profiles_service');

-- ══════════════════════════════════════════════════════════════════
-- conversations
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('conversations', 'conversations_select_own', 'select_conversations_owner');
SELECT pg_temp.safe_rename_policy('conversations', 'conversations_insert_own', 'insert_conversations_owner');
SELECT pg_temp.safe_rename_policy('conversations', 'conversations_update_admin', 'update_conversations_admin');
SELECT pg_temp.safe_rename_policy('conversations', 'conversations_service_all', 'all_conversations_service');

-- ══════════════════════════════════════════════════════════════════
-- messages
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('messages', 'messages_select', 'select_messages_authenticated');
SELECT pg_temp.safe_rename_policy('messages', 'messages_insert_user', 'insert_messages_authenticated');
SELECT pg_temp.safe_rename_policy('messages', 'messages_update_read', 'update_messages_owner');
SELECT pg_temp.safe_rename_policy('messages', 'messages_service_all', 'all_messages_service');

-- ══════════════════════════════════════════════════════════════════
-- user_oauth_tokens
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('user_oauth_tokens', 'Users can view own OAuth tokens', 'select_user_oauth_tokens_owner');
SELECT pg_temp.safe_rename_policy('user_oauth_tokens', 'Users can update own OAuth tokens', 'update_user_oauth_tokens_owner');
SELECT pg_temp.safe_rename_policy('user_oauth_tokens', 'Users can delete own OAuth tokens', 'delete_user_oauth_tokens_owner');
SELECT pg_temp.safe_rename_policy('user_oauth_tokens', 'Service role can manage all OAuth tokens', 'all_user_oauth_tokens_service');

-- ══════════════════════════════════════════════════════════════════
-- google_sheets_exports
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('google_sheets_exports', 'Users can view own Google Sheets exports', 'select_google_sheets_exports_owner');
SELECT pg_temp.safe_rename_policy('google_sheets_exports', 'Users can create Google Sheets exports', 'insert_google_sheets_exports_owner');
SELECT pg_temp.safe_rename_policy('google_sheets_exports', 'Users can update own Google Sheets exports', 'update_google_sheets_exports_owner');
SELECT pg_temp.safe_rename_policy('google_sheets_exports', 'Service role can manage all Google Sheets exports', 'all_google_sheets_exports_service');

-- ══════════════════════════════════════════════════════════════════
-- stripe_webhook_events
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('stripe_webhook_events', 'webhook_events_insert_service', 'insert_stripe_webhook_events_service');
SELECT pg_temp.safe_rename_policy('stripe_webhook_events', 'webhook_events_select_admin', 'select_stripe_webhook_events_admin');
SELECT pg_temp.safe_rename_policy('stripe_webhook_events', 'webhook_events_service_role_select', 'select_stripe_webhook_events_service');

-- ══════════════════════════════════════════════════════════════════
-- plan_features
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('plan_features', 'plan_features_select_all', 'select_plan_features_public');

-- ══════════════════════════════════════════════════════════════════
-- plan_billing_periods
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('plan_billing_periods', 'plan_billing_periods_public_read', 'select_plan_billing_periods_public');
SELECT pg_temp.safe_rename_policy('plan_billing_periods', 'plan_billing_periods_service_all', 'all_plan_billing_periods_service');

-- ══════════════════════════════════════════════════════════════════
-- search_sessions
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('search_sessions', 'Service role can manage search sessions', 'all_search_sessions_service');

-- ══════════════════════════════════════════════════════════════════
-- search_results_cache
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('search_results_cache', 'Users can read own search cache', 'select_search_results_cache_owner');

-- ══════════════════════════════════════════════════════════════════
-- search_results_store
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('search_results_store', 'Users can read own results', 'select_search_results_store_owner');

-- ══════════════════════════════════════════════════════════════════
-- search_state_transitions
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('search_state_transitions', 'Service role can insert transitions', 'insert_search_state_transitions_service');

-- ══════════════════════════════════════════════════════════════════
-- alerts
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('alerts', 'Users can view own alerts', 'select_alerts_owner');
SELECT pg_temp.safe_rename_policy('alerts', 'Users can insert own alerts', 'insert_alerts_owner');
SELECT pg_temp.safe_rename_policy('alerts', 'Users can update own alerts', 'update_alerts_owner');
SELECT pg_temp.safe_rename_policy('alerts', 'Users can delete own alerts', 'delete_alerts_owner');
SELECT pg_temp.safe_rename_policy('alerts', 'Service role full access to alerts', 'all_alerts_service');

-- ══════════════════════════════════════════════════════════════════
-- alert_sent_items
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('alert_sent_items', 'Service role full access to alert_sent_items', 'all_alert_sent_items_service');
SELECT pg_temp.safe_rename_policy('alert_sent_items', 'Users can view own alert sent items', 'select_alert_sent_items_owner');

-- ══════════════════════════════════════════════════════════════════
-- alert_preferences
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('alert_preferences', 'Users can view own alert preferences', 'select_alert_preferences_owner');
SELECT pg_temp.safe_rename_policy('alert_preferences', 'Users can insert own alert preferences', 'insert_alert_preferences_owner');
SELECT pg_temp.safe_rename_policy('alert_preferences', 'Users can update own alert preferences', 'update_alert_preferences_owner');

-- ══════════════════════════════════════════════════════════════════
-- alert_runs
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('alert_runs', 'Service role full access to alert_runs', 'all_alert_runs_service');
SELECT pg_temp.safe_rename_policy('alert_runs', 'Users can view own alert runs', 'select_alert_runs_owner');

-- ══════════════════════════════════════════════════════════════════
-- mfa_recovery_codes
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('mfa_recovery_codes', 'Users can view own recovery codes', 'select_mfa_recovery_codes_owner');
SELECT pg_temp.safe_rename_policy('mfa_recovery_codes', 'Service role full access to recovery codes', 'all_mfa_recovery_codes_service');

-- ══════════════════════════════════════════════════════════════════
-- mfa_recovery_attempts
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('mfa_recovery_attempts', 'Service role full access to recovery attempts', 'all_mfa_recovery_attempts_service');

-- ══════════════════════════════════════════════════════════════════
-- audit_events
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('audit_events', 'Service role can manage audit events', 'all_audit_events_service');
SELECT pg_temp.safe_rename_policy('audit_events', 'Admins can read audit events', 'select_audit_events_admin');

-- ══════════════════════════════════════════════════════════════════
-- pipeline_items
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('pipeline_items', 'Users can view own pipeline items', 'select_pipeline_items_owner');
SELECT pg_temp.safe_rename_policy('pipeline_items', 'Users can insert own pipeline items', 'insert_pipeline_items_owner');
SELECT pg_temp.safe_rename_policy('pipeline_items', 'Users can update own pipeline items', 'update_pipeline_items_owner');
SELECT pg_temp.safe_rename_policy('pipeline_items', 'Users can delete own pipeline items', 'delete_pipeline_items_owner');
SELECT pg_temp.safe_rename_policy('pipeline_items', 'Service role full access on pipeline_items', 'all_pipeline_items_service');

-- ══════════════════════════════════════════════════════════════════
-- organizations
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('organizations', 'Org owner can view organization', 'select_organizations_owner');
SELECT pg_temp.safe_rename_policy('organizations', 'Org admins can view organization', 'select_organizations_admin');
SELECT pg_temp.safe_rename_policy('organizations', 'Owner can insert organization', 'insert_organizations_owner');
SELECT pg_temp.safe_rename_policy('organizations', 'Owner can update organization', 'update_organizations_owner');

-- ══════════════════════════════════════════════════════════════════
-- organization_members
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('organization_members', 'Users can view own membership', 'select_organization_members_self');
SELECT pg_temp.safe_rename_policy('organization_members', 'Org owner/admin can view all members', 'select_organization_members_admin');
SELECT pg_temp.safe_rename_policy('organization_members', 'Org owner/admin can insert members', 'insert_organization_members_admin');
SELECT pg_temp.safe_rename_policy('organization_members', 'Org owner/admin can delete members', 'delete_organization_members_admin');

-- ══════════════════════════════════════════════════════════════════
-- classification_feedback
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('classification_feedback', 'feedback_insert_own', 'insert_classification_feedback_owner');
SELECT pg_temp.safe_rename_policy('classification_feedback', 'feedback_select_own', 'select_classification_feedback_owner');
SELECT pg_temp.safe_rename_policy('classification_feedback', 'feedback_update_own', 'update_classification_feedback_owner');
SELECT pg_temp.safe_rename_policy('classification_feedback', 'feedback_delete_own', 'delete_classification_feedback_owner');

-- ══════════════════════════════════════════════════════════════════
-- partners
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('partners', 'partners_admin_all', 'all_partners_admin');
SELECT pg_temp.safe_rename_policy('partners', 'partners_self_read', 'select_partners_self');

-- ══════════════════════════════════════════════════════════════════
-- partner_referrals
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('partner_referrals', 'partner_referrals_admin_all', 'all_partner_referrals_admin');
SELECT pg_temp.safe_rename_policy('partner_referrals', 'partner_referrals_partner_read', 'select_partner_referrals_partner');

-- ══════════════════════════════════════════════════════════════════
-- reconciliation_log
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('reconciliation_log', 'Admin read reconciliation_log', 'select_reconciliation_log_admin');

-- ══════════════════════════════════════════════════════════════════
-- trial_email_log
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('trial_email_log', 'Users can view own trial emails', 'select_trial_email_log_owner');

-- ══════════════════════════════════════════════════════════════════
-- Standardize service_role_all → all_{table}_service (unique per table)
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('health_checks', 'service_role_all', 'all_health_checks_service');
SELECT pg_temp.safe_rename_policy('incidents', 'service_role_all', 'all_incidents_service');
SELECT pg_temp.safe_rename_policy('alert_preferences', 'service_role_all', 'all_alert_preferences_service');
SELECT pg_temp.safe_rename_policy('reconciliation_log', 'service_role_all', 'all_reconciliation_log_service');
SELECT pg_temp.safe_rename_policy('organizations', 'service_role_all', 'all_organizations_service');
SELECT pg_temp.safe_rename_policy('organization_members', 'service_role_all', 'all_organization_members_service');
SELECT pg_temp.safe_rename_policy('partners', 'service_role_all', 'all_partners_service');
SELECT pg_temp.safe_rename_policy('partner_referrals', 'service_role_all', 'all_partner_referrals_service');
SELECT pg_temp.safe_rename_policy('search_results_store', 'service_role_all', 'all_search_results_store_service');
SELECT pg_temp.safe_rename_policy('classification_feedback', 'service_role_all', 'all_classification_feedback_service');
SELECT pg_temp.safe_rename_policy('search_state_transitions', 'service_role_all', 'all_search_state_transitions_service');

-- ══════════════════════════════════════════════════════════════════
-- Standardize pncp_raw_bids / ingestion tables
-- (already close but {table}_{action}_{role} → {action}_{table}_{role})
-- ══════════════════════════════════════════════════════════════════
SELECT pg_temp.safe_rename_policy('pncp_raw_bids', 'pncp_raw_bids_select_authenticated', 'select_pncp_raw_bids_authenticated');
SELECT pg_temp.safe_rename_policy('pncp_raw_bids', 'pncp_raw_bids_insert_service', 'insert_pncp_raw_bids_service');
SELECT pg_temp.safe_rename_policy('pncp_raw_bids', 'pncp_raw_bids_update_service', 'update_pncp_raw_bids_service');
SELECT pg_temp.safe_rename_policy('pncp_raw_bids', 'pncp_raw_bids_delete_service', 'delete_pncp_raw_bids_service');

SELECT pg_temp.safe_rename_policy('ingestion_checkpoints', 'ingestion_checkpoints_select_authenticated', 'select_ingestion_checkpoints_authenticated');
SELECT pg_temp.safe_rename_policy('ingestion_checkpoints', 'ingestion_checkpoints_write_service', 'all_ingestion_checkpoints_service');

SELECT pg_temp.safe_rename_policy('ingestion_runs', 'ingestion_runs_select_authenticated', 'select_ingestion_runs_authenticated');
SELECT pg_temp.safe_rename_policy('ingestion_runs', 'ingestion_runs_write_service', 'all_ingestion_runs_service');

-- ══════════════════════════════════════════════════════════════════
-- Cleanup: drop the temp helper function
-- ══════════════════════════════════════════════════════════════════
DROP FUNCTION IF EXISTS pg_temp.safe_rename_policy(TEXT, TEXT, TEXT);

-- ══════════════════════════════════════════════════════════════════
-- Verification: All policies should follow {action}_{table}_{role} pattern
-- SELECT tablename, policyname FROM pg_policies
-- WHERE schemaname = 'public'
-- AND policyname !~ '^(select|insert|update|delete|all)_'
-- ORDER BY tablename, policyname;
-- Should return 0 rows.
-- ══════════════════════════════════════════════════════════════════

NOTIFY pgrst, 'reload schema';
