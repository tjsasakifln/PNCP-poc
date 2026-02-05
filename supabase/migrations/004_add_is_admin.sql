-- ============================================================
-- Add is_admin column to profiles for admin user management
-- ============================================================
--
-- Hierarchy:
--   admin (is_admin = true) > master (plan_type = 'master') > other plans
--
-- Admin users can:
--   - All master capabilities (Excel, unlimited quota, etc.)
--   - Access /admin/* endpoints to manage users
--
-- Master users can:
--   - Full feature access (Excel, unlimited quota, 5 year history)
--   - Cannot manage other users

-- Add is_admin column
ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS is_admin boolean NOT NULL DEFAULT false;

-- Create index for fast admin lookups
CREATE INDEX IF NOT EXISTS idx_profiles_is_admin ON public.profiles(is_admin) WHERE is_admin = true;

-- Comment for documentation
COMMENT ON COLUMN public.profiles.is_admin IS 'True for system administrators who can manage users via /admin/* endpoints';
