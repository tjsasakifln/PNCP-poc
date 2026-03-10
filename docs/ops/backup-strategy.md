# Backup Strategy — SmartLic

## Overview

SmartLic uses Supabase Pro as its primary database, which provides automated backup and point-in-time recovery (PITR) capabilities.

## Supabase Pro Backup Features

### Daily Backups
- **Frequency:** Automated daily backups
- **Retention:** 7 days
- **Type:** Full database snapshots
- **Location:** Managed by Supabase in the project's region (South America East / sa-east-1)

### Point-in-Time Recovery (PITR)
- **Granularity:** Restore to any point within the 7-day retention window
- **Technology:** PostgreSQL WAL (Write-Ahead Logging) archival
- **RTO:** Minutes (depends on database size)
- **RPO:** Near-zero (continuous WAL archiving)

## Data Retention Policies

Automated pg_cron jobs handle data lifecycle management:

| Table | Retention | Schedule | Job Name |
|-------|-----------|----------|----------|
| `monthly_quota` | 24 months | 1st of month, 02:00 UTC | `cleanup-monthly-quota` |
| `stripe_webhook_events` | 90 days | Daily, 03:00 UTC | `cleanup-webhook-events` |
| `search_state_transitions` | 30 days | Daily, 04:00 UTC | `cleanup-search-state-transitions` |
| `alert_sent_items` | 180 days | Daily, 04:05 UTC | `cleanup-alert-sent-items` |
| `health_checks` | 30 days | Daily, 04:10 UTC | `cleanup-health-checks` |
| `incidents` | 90 days | Daily, 04:15 UTC | `cleanup-incidents` |
| `mfa_recovery_attempts` | 30 days | Daily, 04:20 UTC | `cleanup-mfa-recovery-attempts` |
| `alert_runs` (completed) | 90 days | Daily, 04:25 UTC | `cleanup-alert-runs` |
| `search_results_store` | By `expires_at` | Daily, 04:00 UTC | `cleanup-expired-search-results` |
| `search_sessions` | 12 months | Daily, 04:30 UTC | `cleanup-old-search-sessions` |
| `classification_feedback` | 24 months | Daily, 04:45 UTC | `cleanup-classification-feedback` |
| `conversations` | 24 months | Daily, 04:50 UTC | `cleanup-old-conversations` |
| `messages` | 24 months | Daily, 04:55 UTC | `cleanup-orphan-messages` |

## Recovery Procedure

### Scenario 1: Accidental Data Deletion (within 7 days)

1. **Assess scope** — Determine what data was lost and when the deletion occurred
2. **Access Supabase Dashboard** — Go to Project Settings → Backups
3. **Select restore point** — Choose a timestamp BEFORE the deletion
4. **Initiate PITR** — Click "Restore" and confirm
5. **Verify** — Check that the restored data is correct
6. **Post-recovery** — Re-apply any legitimate changes made after the restore point

```bash
# Verify data after restore
npx supabase db pull --schema public
```

### Scenario 2: Schema Corruption

1. **Identify the breaking migration** — Check `supabase/migrations/` git history
2. **Create rollback migration** — Write a reversal migration
3. **Apply via CLI:**
   ```bash
   npx supabase migration new rollback_corruption
   npx supabase db push --include-all
   ```
4. **Verify schema:**
   ```bash
   npx supabase db diff
   ```

### Scenario 3: Full Database Recovery

1. **Contact Supabase Support** (if PITR is insufficient)
2. **Use daily backup** from Supabase Dashboard → Backups
3. **Restore to new project** if needed (avoids overwriting current state)
4. **Migrate data** from restored project to production

## Environment-Specific Notes

### Production (Supabase Cloud)
- **Project ref:** `fqqyovlzdzimiwfofdjk`
- **Region:** South America East (sa-east-1)
- **Plan:** Pro (daily backups + PITR included)
- Backups are managed automatically — no manual intervention required

### Local Development
- No automated backups (use `npx supabase db dump` for manual snapshots)
- Reset with: `npx supabase db reset`

## Monitoring

- Supabase Dashboard shows backup status and history
- Failed backups trigger Supabase platform alerts (email to project owner)
- pg_cron job execution logs available via `SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 20;`

## Disaster Recovery Contacts

- **Supabase Support:** support@supabase.io (Pro tier — priority support)
- **Internal:** tiago.sasaki@gmail.com (project owner)
