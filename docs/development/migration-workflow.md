# Database Migration Workflow - SmartLic/BidIQ

**Created:** 2026-02-12
**Story:** STORY-203 Track 4 - SYS-H03
**Purpose:** Standardized workflow for creating, testing, and deploying database migrations

## Overview

SmartLic/BidIQ uses Supabase for database management with migration-based schema versioning. All schema changes MUST be tracked as SQL migration files to ensure consistency across environments and enable rollback capabilities.

## Directory Structure

```
supabase/
├── migrations/
│   ├── 001_profiles_and_sessions.sql
│   ├── 002_monthly_quota.sql
│   ├── 003_atomic_quota_increment.sql
│   └── ...
└── config.toml                 # Supabase project configuration
```

## Migration File Naming Convention

**Format:** `NNN_descriptive_name.sql`

- **NNN** - Zero-padded sequential number (001, 002, 003, ...)
- **descriptive_name** - Snake_case description of the change
- **Extension** - Always `.sql`

**Examples:**
- `019_add_user_preferences.sql`
- `020_create_notifications_table.sql`
- `021_add_user_email_index.sql`

**Important:**
- Numbers must be sequential and unique
- Once deployed to production, NEVER modify or delete existing migrations
- To fix issues, create a NEW migration that reverts/corrects the problem

## Workflow Steps

### 1. Create New Migration

**Option A: Manual Creation**
```bash
# Navigate to migrations directory
cd supabase/migrations

# Find the next sequential number
ls -1 *.sql | tail -1  # Get last migration number

# Create new migration file
# Example: Next number is 020
touch 020_add_user_timezone.sql
```

**Option B: Using Supabase CLI (recommended)**
```bash
# Generate migration file with automatic numbering
npx supabase migration new add_user_timezone

# This creates: supabase/migrations/YYYYMMDDHHMMSS_add_user_timezone.sql
```

### 2. Write Migration SQL

**Template:**
```sql
-- Migration: [Number] - [Description]
-- Created: [Date]
-- Story: [Story ID if applicable]
-- Purpose: [Brief explanation]

-- ============================================================================
-- Schema Changes
-- ============================================================================

-- Example: Add new column
ALTER TABLE profiles
ADD COLUMN timezone VARCHAR(50) DEFAULT 'America/Sao_Paulo';

-- Example: Create index
CREATE INDEX idx_profiles_timezone ON profiles(timezone);

-- ============================================================================
-- Data Migration (if needed)
-- ============================================================================

-- Example: Update existing records
UPDATE profiles
SET timezone = 'America/Sao_Paulo'
WHERE timezone IS NULL;

-- ============================================================================
-- Permissions (if needed)
-- ============================================================================

-- Grant access to authenticated users
GRANT SELECT, UPDATE ON profiles TO authenticated;
```

**Best Practices:**
- Include descriptive comments
- Break complex migrations into logical sections
- Use transactions implicitly (each migration runs in a transaction)
- Test data migrations on sample datasets first
- Consider performance impact for large tables

### 3. Test Locally

**A. Start local Supabase instance:**
```bash
npx supabase start
```

**B. Apply migration:**
```bash
# Apply all pending migrations
npx supabase db push

# Or apply specific migration
npx supabase db push --file supabase/migrations/020_add_user_timezone.sql
```

**C. Verify changes:**
```bash
# Connect to local database
npx supabase db connect

# Or use psql directly
psql postgresql://postgres:postgres@localhost:54322/postgres

# Inspect schema
\d profiles          # Describe table
\di profiles         # List indexes
SELECT * FROM profiles LIMIT 5;  # Sample data
```

**D. Test application:**
```bash
# Update .env to point to local Supabase
SUPABASE_URL=http://localhost:54321
SUPABASE_SERVICE_ROLE_KEY=<local-service-role-key>

# Run backend tests
cd backend
pytest

# Run manual tests
uvicorn main:app --reload
```

### 4. Review Changes

**Create diff to verify:**
```bash
# Show schema changes
npx supabase db diff

# Compare local vs remote
npx supabase db diff --schema public --use-migra
```

**Checklist:**
- [ ] Migration file has descriptive name
- [ ] SQL is well-commented
- [ ] Tested on local Supabase instance
- [ ] No syntax errors
- [ ] Application tests pass with new schema
- [ ] Performance tested for large datasets (if applicable)
- [ ] Rollback plan documented (see section below)

### 5. Commit to Git

```bash
git add supabase/migrations/020_add_user_timezone.sql
git commit -m "feat(db): add user timezone column (STORY-XXX)"
git push origin <branch-name>
```

**Important:** All migrations MUST be committed to version control before deploying.

### 6. Deploy to Production

**A. Via Supabase Dashboard (Manual):**
1. Log in to https://app.supabase.com
2. Select project: `bidiq-production`
3. Navigate to **SQL Editor**
4. Copy migration SQL
5. Execute and verify success

**B. Via Supabase CLI (Recommended):**
```bash
# Link to production project (first time only)
npx supabase link --project-ref fqqyovlzdzimiwfofdjk

# Push migrations to production
npx supabase db push --linked

# Verify applied migrations
npx supabase migration list --linked
```

**C. Via Railway (if backend deployment triggers migrations):**
```bash
# If your backend has migration auto-apply on startup
railway up

# Monitor logs
railway logs --tail
```

**Post-Deployment Verification:**
```bash
# Test production endpoints
curl https://bidiq-backend-production.up.railway.app/health

# Check database via Supabase Studio
# Navigate to: https://app.supabase.com/project/fqqyovlzdzimiwfofdjk/editor
```

## Rollback Procedures

### Scenario 1: Migration Not Yet Deployed

**Solution:** Delete the migration file and create a corrected version.

```bash
# Remove incorrect migration
git rm supabase/migrations/020_incorrect_migration.sql

# Create corrected version
touch supabase/migrations/020_corrected_migration.sql
# ... edit file ...
git add supabase/migrations/020_corrected_migration.sql
git commit -m "fix(db): correct migration 020"
```

### Scenario 2: Migration Deployed to Production

**Solution:** Create a new "reverse" migration.

**Example - Rollback "add column":**
```sql
-- Migration: 021 - Rollback user timezone column
-- Reverses: 020_add_user_timezone.sql

ALTER TABLE profiles
DROP COLUMN timezone;

DROP INDEX IF EXISTS idx_profiles_timezone;
```

**Important:** NEVER delete or modify deployed migrations. Always move forward with new migrations.

### Scenario 3: Data Corruption

**Solution:** Restore from Supabase backup.

```bash
# Via Supabase Dashboard:
# 1. Go to: Project Settings > Database > Backups
# 2. Select backup timestamp before migration
# 3. Click "Restore"

# Or contact Supabase support for point-in-time recovery
```

## Common Migration Patterns

### Add Column
```sql
ALTER TABLE table_name
ADD COLUMN column_name TYPE DEFAULT value;
```

### Rename Column
```sql
ALTER TABLE table_name
RENAME COLUMN old_name TO new_name;
```

### Change Column Type
```sql
ALTER TABLE table_name
ALTER COLUMN column_name TYPE new_type USING column_name::new_type;
```

### Add Index
```sql
CREATE INDEX idx_table_column ON table_name(column_name);

-- Unique index
CREATE UNIQUE INDEX idx_table_column_unique ON table_name(column_name);

-- Partial index
CREATE INDEX idx_active_users ON profiles(id) WHERE is_active = true;
```

### Create Table
```sql
CREATE TABLE IF NOT EXISTS new_table (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add RLS policies
ALTER TABLE new_table ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own records"
ON new_table FOR SELECT
USING (auth.uid() = user_id);
```

### Create Function/Trigger
```sql
-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger on table
CREATE TRIGGER update_profiles_updated_at
BEFORE UPDATE ON profiles
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();
```

## Troubleshooting

### Error: "Migration already applied"
**Cause:** Migration file was previously applied.
**Solution:** Create a new migration with a higher number.

### Error: "Syntax error in SQL"
**Cause:** Invalid SQL syntax.
**Solution:** Test migration locally first using `npx supabase db push`.

### Error: "Permission denied"
**Cause:** Insufficient database privileges.
**Solution:** Use service role key for migrations, not anon key.

### Performance Issues After Migration
**Cause:** Missing indexes or inefficient queries.
**Solution:**
```sql
-- Add index to improve query performance
CREATE INDEX CONCURRENTLY idx_column ON table(column);

-- Analyze table statistics
ANALYZE table_name;
```

## Resources

- **Supabase Migrations Guide:** https://supabase.com/docs/guides/cli/managing-environments
- **Supabase Local Development:** https://supabase.com/docs/guides/cli/local-development
- **PostgreSQL ALTER TABLE:** https://www.postgresql.org/docs/current/sql-altertable.html
- **Migration Best Practices:** https://docs.gitlab.com/ee/development/database/migration_style_guide.html

## Current Migrations Log

| # | File | Story | Status | Deployed |
|---|------|-------|--------|----------|
| 001 | profiles_and_sessions.sql | Initial | ✅ Deployed | 2026-01-15 |
| 002 | monthly_quota.sql | STORY-169 | ✅ Deployed | 2026-01-20 |
| 003 | atomic_quota_increment.sql | Issue #189 | ✅ Deployed | 2026-01-25 |
| 004 | add_is_admin.sql | - | ✅ Deployed | 2026-01-28 |
| 005 | update_plans_to_new_tiers.sql | STORY-170 | ✅ Deployed | 2026-02-01 |
| ... | ... | ... | ... | ... |
| 019 | rpc_performance_functions.sql | STORY-202 | ✅ Deployed | 2026-02-10 |

**Update this table when deploying new migrations.**

---

**Last Updated:** 2026-02-12
**Maintained By:** DevOps Team
**Review Cycle:** Quarterly
