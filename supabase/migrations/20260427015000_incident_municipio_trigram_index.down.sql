-- Rollback INCIDENT 2026-04-27: drop GIN trigram em municipio.

DROP INDEX IF EXISTS public.idx_psc_municipio_trgm;
