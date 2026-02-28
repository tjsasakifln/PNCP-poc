-- STORY-318: Split from 20260227120000_concurrency_safety.sql (Fix 2)
-- Pipeline Optimistic Locking — version column

ALTER TABLE pipeline_items
  ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1 NOT NULL;
