-- ============================================================
-- SmartLic: Update plans to new pricing tiers
-- Migration: 005_update_plans_to_new_tiers
-- Date: 2026-02-05
-- ============================================================

-- Deactivate old plans (keep free and master)
UPDATE public.plans
SET is_active = false
WHERE id IN ('pack_5', 'pack_10', 'pack_20', 'monthly', 'annual');

-- Insert new plans (or update if they exist)
INSERT INTO public.plans (id, name, description, max_searches, price_brl, duration_days, is_active) VALUES
  ('consultor_agil', 'Consultor Ágil', '50 buscas por mês, 30 dias de histórico, Resumo executivo IA básico', 50, 297.00, 30, true),
  ('maquina', 'Máquina', '300 buscas por mês, 1 ano de histórico, Exportar Excel, API básica', 300, 597.00, 30, true),
  ('sala_guerra', 'Sala de Guerra', '1000 buscas por mês, 5 anos de histórico, Alertas automáticos, API completa', 1000, 1497.00, 30, true)
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  max_searches = EXCLUDED.max_searches,
  price_brl = EXCLUDED.price_brl,
  duration_days = EXCLUDED.duration_days,
  is_active = EXCLUDED.is_active;

-- Verify the changes
-- SELECT id, name, price_brl, is_active FROM public.plans ORDER BY price_brl;
