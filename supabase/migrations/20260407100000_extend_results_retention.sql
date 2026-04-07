-- Zero-Churn P2 §2.2: Extend search results retention to 30 days for grace period downloads
-- Previous default was 24 hours, now 30 days to honor "dados salvos por 30 dias" promise

ALTER TABLE search_results_store
  ALTER COLUMN expires_at SET DEFAULT now() + INTERVAL '30 days';

-- Extend existing non-expired rows to 30 days from their creation
UPDATE search_results_store
SET expires_at = created_at + INTERVAL '30 days'
WHERE expires_at > now();
