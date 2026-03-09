#!/bin/bash
# DEBT-017/DB-029: Seed Stripe Price IDs for staging/dev environments
# Usage: ./scripts/seed-stripe-prices.sh
#
# Required environment variables:
#   DATABASE_URL              — PostgreSQL connection string
#   SMARTLIC_PRO_MONTHLY      — Stripe price ID for SmartLic Pro monthly
#   SMARTLIC_PRO_SEMIANNUAL   — Stripe price ID for SmartLic Pro semiannual
#   SMARTLIC_PRO_ANNUAL       — Stripe price ID for SmartLic Pro annual
#   CONSULTORIA_MONTHLY       — Stripe price ID for Consultoria monthly
#   CONSULTORIA_SEMIANNUAL    — Stripe price ID for Consultoria semiannual
#   CONSULTORIA_ANNUAL        — Stripe price ID for Consultoria annual

set -euo pipefail

if [ -z "${DATABASE_URL:-}" ]; then
    echo "ERROR: DATABASE_URL is required"
    exit 1
fi

echo "Seeding Stripe Price IDs..."

psql "$DATABASE_URL" \
    -v ON_ERROR_STOP=1 \
    -c "SET app.smartlic_pro_monthly = '${SMARTLIC_PRO_MONTHLY:-}';" \
    -c "SET app.smartlic_pro_semiannual = '${SMARTLIC_PRO_SEMIANNUAL:-}';" \
    -c "SET app.smartlic_pro_annual = '${SMARTLIC_PRO_ANNUAL:-}';" \
    -c "SET app.consultoria_monthly = '${CONSULTORIA_MONTHLY:-}';" \
    -c "SET app.consultoria_semiannual = '${CONSULTORIA_SEMIANNUAL:-}';" \
    -c "SET app.consultoria_annual = '${CONSULTORIA_ANNUAL:-}';" \
    -f supabase/seed/seed_stripe_prices.sql

echo "Done. Stripe Price IDs seeded for staging/dev."
