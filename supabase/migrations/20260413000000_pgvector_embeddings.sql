-- ============================================================
-- Migration: 20260413000000_pgvector_embeddings
-- Story:     STORY-438 AC1
-- Purpose:   Enable pgvector, add embedding column, create HNSW index.
--            Uses text-embedding-3-small dimensions=256.
--            40K rows × 256 × 4 bytes ≈ 41MB + HNSW ≈ 20MB (safe for free tier).
-- Pre-condition: Verify storage before applying:
--   SELECT pg_size_pretty(pg_database_size(current_database()));
-- ============================================================

-- Enable pgvector extension (idempotent)
CREATE EXTENSION IF NOT EXISTS vector;

-- Add nullable embedding column (default NULL — backfill separately)
ALTER TABLE public.pncp_raw_bids
    ADD COLUMN IF NOT EXISTS embedding VECTOR(256);

COMMENT ON COLUMN public.pncp_raw_bids.embedding IS
    'Semantic embedding via text-embedding-3-small (dimensions=256). '
    'Generated from objeto_compra during ingestion when EMBEDDING_ENABLED=true. '
    'Backfill via backend/scripts/backfill_embeddings.py. '
    'STORY-438.';

-- HNSW index for approximate nearest-neighbor cosine search.
-- HNSW preferred over IVFFlat: no vacuum needed, consistent latency < 10ms.
-- m=16, ef_construction=64: good quality/speed balance for 40K-100K rows.
CREATE INDEX IF NOT EXISTS idx_pncp_raw_bids_embedding
    ON public.pncp_raw_bids
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

COMMENT ON INDEX idx_pncp_raw_bids_embedding IS
    'HNSW index for cosine similarity search on embeddings (STORY-438 AC1). '
    'No VACUUM needed. Latency < 10ms for 40K rows at m=16/ef_construction=64.';
