/**
 * Bundle size budget — hold-the-line check for First Load JS.
 *
 * Run locally: npx size-limit
 * CI: frontend-tests.yml "Check bundle size budget" — fails build if exceeded.
 *
 * ⚠️  Budget rationale (STORY-5.14, 2026-04-19):
 *  - Baseline medido em CI (main pós Wave #386): **1.64 MB gzipped** (agregado
 *    de `.next/static/chunks/**\/*.js`).
 *  - Limite original de 250 KB (DEBT-108) era irreal para o bundle agregado
 *    atual: Next.js 16 + Sentry + Framer Motion + Recharts + dnd-kit +
 *    Supabase SSR + Stripe Elements + Shepherd.js totalizam ~1.6 MB gzipped.
 *  - Budget atual é **hold-the-line** (baseline + ~7% head-room) para prevenir
 *    regressão, NÃO é alvo de produto.
 *  - Alvo de redução está tracked em STORY-5.14 (TD-FE-014): reduzir
 *    First Load JS para ≤ 600 KB em 90 dias via route-level code splitting
 *    + dynamic imports de rotas autenticadas (dashboard, pipeline, admin) +
 *    migração opportunística de Framer → CSS transitions em landing.
 */
module.exports = [
  {
    name: 'First Load JS (total)',
    path: '.next/static/chunks/**/*.js',
    gzip: true,
    limit: '1.75 MB',
  },
];
