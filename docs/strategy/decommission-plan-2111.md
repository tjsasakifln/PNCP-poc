# #2111 decommission plan — inventory only (non-destructive)

**Issue:** [SmartLic#2111](https://github.com/tjsasakifln/SmartLic/issues/2111)  
**Date:** 2026-08-15  
**Authority:** ADR-STRAT-002 + `RUNTIME-AUTHORITY.md`  
**Companion:** commerce-wave-1 freeze in `saas-sunset-inventory-2111.md` (does not replace this file)

This is a **plan**. Nothing listed here is removed, disabled in production, or archived by this change. Live process / secret / store presence is **UNKNOWN** unless a 2026-08-15 observation is cited. Railway / FastAPI / Next.js / Supabase / Redis / ARQ / Stripe are **not** to be restored.

Classes (only these):

| Class | Meaning |
|---|---|
| `MIGRATE` | Useful equity/capability has a destination owner elsewhere; move evidence, then retire here after proof |
| `RETIRE` | No destination; delete only after zero-use evidence |
| `KEEP_UNTIL_REDIRECT_WINDOW` | Required for #2115 observation / rollback / legal retention; remove only after the 28-day window + #2111 archive gate |
| `UNKNOWN` | Not invented. Needs a live read before class can be tighter |

Destination owners when known: `web-cfg` (public surface), `extra-cli` (facts / public_read), `Warmbly` (commercial action), `archive` (read-only evidence).

Campaign class mapping (ADR-STRAT-002 execute; does not replace the shipped tokens above):

| Shipped class | Campaign class | When |
|---|---|---|
| `KEEP_UNTIL_REDIRECT_WINDOW` | `KEEP_TEMP_BRIDGE` | Item is required for the #2115 bridge, DNS/TLS rollback, or 28-day observation |
| `KEEP_UNTIL_REDIRECT_WINDOW` | `LEGAL_RETENTION` | Item is required for fiscal / LGPD / PII / existing-customer cancel only |
| `MIGRATE` | `MIGRATED` | Destination owner already holds the capability; local copy is evidence only |
| `MIGRATE` | `MIGRATE` | Harvest/transfer still open (web-cfg#63 / extra-cli) |
| `RETIRE` | `RETIRE` | No destination; delete only after zero-use evidence |
| `UNKNOWN` | `UNKNOWN` | Fail closed — do not invent a tighter class |

## 1. Jobs

Source: `backend/jobs/queue/config.py`, `backend/jobs/cron/`, `backend/jobs/queue/jobs.py`. Live ARQ/pg_cron execution: **UNKNOWN** (Railway worker not probed; do not start it).

| Item | Class | Destination | Notes |
|---|---|---|---|
| `bridge/` stdlib serve + Caddy units | KEEP_UNTIL_REDIRECT_WINDOW | SmartLic#2115 | Only authorized remaining runtime. Not started in production. |
| Ingestion crawls (`ingestion_*`, `contracts_*`, enrichers, IBGE backfill) | RETIRE | extra-cli owns public-read facts if any survive harvest (web-cfg#63) | DataLake / crawler must not become a permanent SmartLic runtime |
| `pncp_canary`, `synthetic_monitor`, `cron_monitoring_job`, `db_pool_monitor` | RETIRE | — | Product health. Forbidden to restore. |
| `daily_digest_job`, `email_alerts_job`, `new_bids_notifier`, `predictive_alert_job`, `competitive_alert_*` | RETIRE | Warmbly if a later inbound product wants alerts; not proven | SaaS retention loops |
| `trial_emails`, `trial_risk_detection`, `founders_auto_disable`, billing loops (reconciliation, predunning, revenue share, stripe events purge) | RETIRE | — | Commerce sunset. Wave 1 already 410'd new checkout. |
| `gsc_sync_job`, `seo_snapshot`, `seo_coverage_manifest`, `indice_municipal` | RETIRE | web-cfg#62 for GSC/equity; do not keep SmartLic SEO jobs | |
| `llm_batch_poll` / LLM summary ARQ functions | RETIRE | — | Product feature |
| `session_cleanup`, `data_retention`, `network_events_cleanup`, `auth_cleanup` | KEEP_UNTIL_REDIRECT_WINDOW | archive | Legal/PII hygiene while stores still exist. Do not delete the *policy*; delete the *job* only after stores are gone. |
| `send_lead_magnet`, `monthly_report_job`, `subcontract_discovery` | RETIRE | Warmbly (commercial) if a later product exists | |
| pg_cron: `purge-old-bids`, `cleanup-search-cache`, `cleanup-search-store`, DEBT-009 retention jobs | KEEP_UNTIL_REDIRECT_WINDOW | archive | Leave scheduled until tables are dropped. Live run state UNKNOWN. |
| GitHub Actions product CI (backend/frontend/e2e/SEO) | RETIRE | — | After zero-use. Keep `redirect-bridge.yml` until #2115 removal. |
| `.github/workflows/redirect-bridge.yml` | KEEP_UNTIL_REDIRECT_WINDOW | SmartLic#2115 | |

## 2. Secrets / credentials (names only)

Values are not printed. Live existence in Railway / GitHub / Stripe / Supabase dashboards: **UNKNOWN**.

| Name family | Class | Destination | Notes |
|---|---|---|---|
| `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, Stripe price IDs | KEEP_UNTIL_REDIRECT_WINDOW | archive (fiscal) then RETIRE | Needed to verify / cancel existing customers until zero-use. Do not rotate into a new product. |
| `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `NEXT_PUBLIC_SUPABASE_*` | KEEP_UNTIL_REDIRECT_WINDOW | extra-cli if any table is harvested; else archive | Required for LGPD export/delete and retention jobs |
| `REDIS_URL` | RETIRE | — | Cache / ARQ. No bridge dependency. |
| `OPENAI_API_KEY` | RETIRE | — | Product LLM |
| `SENTRY_DSN`, Mixpanel tokens | RETIRE | — | After last legal retention of incident evidence |
| Resend / `RESEND_*` / `EMAIL_*` | RETIRE | — | Trial/billing mail |
| `GSC_SERVICE_ACCOUNT_JSON` | MIGRATE | web-cfg#62 | GSC Change-of-Address + 28-day watch. Transfer ownership; do not keep a SmartLic GSC growth loop. |
| Google OAuth / Sheets refresh tokens (Fernet) | RETIRE | — | Product export |
| Railway tokens / project tokens | RETIRE | — | Do not use to redeploy |
| Cloudflare token | KEEP_UNTIL_REDIRECT_WINDOW | #2115 owner (local only) | DNS apply/rollback. Never commit. |
| `$SMARTLIC_ACME_EMAIL` | KEEP_UNTIL_REDIRECT_WINDOW | #2115 | Contact, not a key |
| GitHub Actions org/repo secrets listed in `DISASTER-RECOVERY.md` | KEEP_UNTIL_REDIRECT_WINDOW | archive | Inventory at archive time; live count UNKNOWN |

## 3. Stores

| Store | Class | Destination | Notes |
|---|---|---|---|
| `pncp_raw_bids` (~400d policy) | MIGRATE then RETIRE | extra-cli `public_read` if harvest (web-cfg#63) says so; else archive snapshot | Do not keep as SmartLic DataLake |
| `pncp_supplier_contracts` (no purge; “SEO permanent”) | MIGRATE then RETIRE | extra-cli / web-cfg harvest | Reclassify after #63. Not a reason to keep SmartLic runtime. |
| `enriched_entities`, `indice_municipal` | MIGRATE or RETIRE | extra-cli if unique; else RETIRE | UNKNOWN uniqueness |
| `profiles`, `events_processed`, billing/plan tables | KEEP_UNTIL_REDIRECT_WINDOW | archive + fiscal retention | Needed for existing-customer cancel / tax. Live row counts UNKNOWN. |
| `search_sessions`, `search_results_*`, pipeline kanban | RETIRE | — | Product |
| `messages` / `conversations` (365d) | KEEP_UNTIL_REDIRECT_WINDOW | archive | Support PII until retention + LGPD tickets close |
| `trial_email_log` (180d) | RETIRE | — | After wave-1 freeze + zero sends |
| Redis (L1/L2 cache, ARQ, rate limits) | RETIRE | — | |
| Railway volumes / logs | RETIRE | archive if incident evidence required | Live UNKNOWN |
| Mixpanel / Sentry projects | RETIRE | archive export if needed | |
| Git repo (this) | KEEP_UNTIL_REDIRECT_WINDOW | GitHub archive read-only | #2111 DoD |

## 4. Domains / DNS / TLS

Observed 2026-08-15 (read-only). Not changed.

| Name | Observed | Class | Destination |
|---|---|---|---|
| `smartlic.tech` A `69.46.46.88` | Railway fallback HTTP 404 `x-railway-fallback: true`; cert SAN apex only, expires 2026-09-16 | KEEP_UNTIL_REDIRECT_WINDOW | #2115 bridge, then retire the name or park after window |
| `www.smartlic.tech` → `69.46.46.117` | TLS SAN mismatch | KEEP_UNTIL_REDIRECT_WINDOW | Same |
| `api.smartlic.tech` → `69.46.46.116` | Railway fallback 404 (prior) | RETIRE | Not inventoried for 301. Stays 410 if ever pointed at the bridge. |
| `app.smartlic.tech` | CNAME Railway | RETIRE | Leave until www rollback no longer needs it |
| TXT google-site-verification, MX `0 smartlic.tech.` | Present (2026-08-14 baseline) | KEEP_UNTIL_REDIRECT_WINDOW | GSC + mail. Do not delete during window. |
| `confenge.com.br` | Canonical public | MIGRATE (already) | web-cfg |
| `smartlic.tech` email (`tiago@smartlic.tech`) | UNKNOWN live use | UNKNOWN | Decide mailbox separately; not this PR |

## 5. Webhooks

| Item | Class | Destination | Notes |
|---|---|---|---|
| `POST /webhooks/stripe` + handlers (checkout, subscription, invoice, founding, product/price) | KEEP_UNTIL_REDIRECT_WINDOW | Stripe dashboard then RETIRE | Existing subscriptions (if any) still need cancel/invoice events. Live delivery count UNKNOWN. |
| Outgoing webhook dispatcher (`jobs.queue.jobs` / `webhooks/outgoing.py`) | RETIRE | — | Product integration |
| Trial-email webhook HMAC | RETIRE | — | |
| GitHub webhooks on this repo | KEEP_UNTIL_REDIRECT_WINDOW | — | CI for the bridge |

## 6. Billing

Wave 1 (`SAAS_COMMERCE_ENABLED` default false, PR #2120) already 410s new checkout / signup / trial extend. Residual:

| Item | Class | Destination | Notes |
|---|---|---|---|
| New checkout / founding / intel-report / setup-intent / period change | RETIRE | — | Already frozen in code. Live flag on Railway: UNKNOWN |
| `POST /billing-portal`, `POST /api/subscriptions/cancel` | KEEP_UNTIL_REDIRECT_WINDOW | Stripe customer portal / Warmbly if a later commercial relationship exists | Existing customer only |
| Stripe customer / subscription objects | KEEP_UNTIL_REDIRECT_WINDOW | Stripe + fiscal archive | Live customer count UNKNOWN. Do not invent revenue. |
| Plan catalog / `plan_billing_periods` | RETIRE | — | After last subscription is gone |
| Frontend `/planos` `/pricing` `/signup` | RETIRE | web-cfg (no SmartLic CTA) | Bridge default 410; do not 301 to CONFENGE home |

## 7. Auth

| Item | Class | Destination | Notes |
|---|---|---|---|
| Supabase Auth (email/password, JWT) | KEEP_UNTIL_REDIRECT_WINDOW | archive + LGPD | Needed for export/delete until users are notified/closed |
| `POST /auth/signup` | RETIRE | — | Wave 1 410 |
| Frontend `supabase.auth.signUp` residual | RETIRE | — | Still in tree; do not restore hosting to “fix” it |
| Google OAuth provisioning | RETIRE | — | |
| MFA / recovery | KEEP_UNTIL_REDIRECT_WINDOW | archive | Existing accounts only |
| Admin role / `ADMIN_USER_IDS` | KEEP_UNTIL_REDIRECT_WINDOW | — | Until stores are dropped |
| Recommended ops (not done here): `disable_signup` in Supabase | KEEP_UNTIL_REDIRECT_WINDOW | — | Owner action; live setting UNKNOWN |

## 8. PII retention

Policy source: `docs/operations/data-retention-policy.md` (2026-06-15). Live purge health: UNKNOWN.

| Record | Policy | Class | After-window action |
|---|---|---|---|
| `profiles` (email, name, plan) | Not in the temporal purge table | KEEP_UNTIL_REDIRECT_WINDOW | LGPD export/delete, then drop |
| `messages` / conversations | 365d hard-delete | KEEP_UNTIL_REDIRECT_WINDOW | Run final purge, then drop |
| `trial_email_log` | 180d | RETIRE | Final purge, then drop |
| `stripe_webhook_events` | 90d | KEEP_UNTIL_REDIRECT_WINDOW | Fiscal overlap; then drop |
| `search_sessions` / results | 1h/7d / 12h TTL | RETIRE | |
| `pncp_raw_bids` | 400d | MIGRATE then RETIRE | Harvest first (web-cfg#63) |
| Mixpanel / Sentry | vendor policy | RETIRE | Export if a legal hold exists (UNKNOWN) |
| Bridge access logs | path-only; no query/PII | KEEP_UNTIL_REDIRECT_WINDOW | 35 days if persisted; none live today |
| LGPD `/me/export` and delete endpoints | documented in product | KEEP_UNTIL_REDIRECT_WINDOW | Honor requests until Auth is gone. Open ticket count: UNKNOWN |

## Zero-use evidence plan

Nothing is removed until the corresponding proof is written into #2111. “Code exists” and “PR merged” are not proof.

| Family | Proof before RETIRE / archive | How to collect (read-only first) | Fail closed |
|---|---|---|---|
| Jobs | No successful ARQ / pg_cron / GitHub product-workflow run for **14 consecutive days** after the bridge window starts, **or** worker process confirmed absent | Railway metrics / `cron.job_run_details` / Actions run list. If the worker is already gone, capture “service missing” — do not start it to prove absence. | Any unexpected run → investigate; do not delete |
| Secrets | Provider last-used = none for **14 days**, and no code path reachable on a live host | Stripe dashboard, Supabase auth logs, GitHub secret access (if any), Railway var list. Live reads need owner login. | UNKNOWN stays UNKNOWN |
| Stores | No new writes for the table’s SLA window; harvest/export complete when class is MIGRATE | `max(updated_at)` per table via service-role **read**; #63 harvest receipt | New writes → KEEP |
| Domains | After 28-day #2115 window: GSC 0 priority errors on the 11 paths; no critical backlink left on SmartLic | web-cfg#62 monitoring. Backlinks today: UNKNOWN | Residual click/error → extend window |
| Webhooks | Stripe delivery count 0 **or** only `customer.subscription.deleted` while draining | Stripe Developers → Webhooks | Unexpected `checkout.session.completed` → do not remove |
| Billing | Zero open subscriptions + invoices settled + `events_processed` idle | Stripe + `profiles.plan_type` read. Customer count UNKNOWN | Any paid residual → KEEP_UNTIL_REDIRECT_WINDOW |
| Auth | `disable_signup` on; no new `profiles` for 14 days; LGPD tickets 0 | Supabase Auth settings + table count | New user → investigate residual OAuth/signUp |
| PII | Retention jobs ran (or stores dropped); export/delete log empty | `data_retention:last_run:*` if Redis still exists; else SQL counts | Legal hold → KEEP |

## What this change does **not** do

- Does not delete jobs, secrets, stores, domains, webhooks, or hosting.
- Does not disable Stripe, Supabase, or Railway.
- Does not apply DNS.
- Does not close #2111.

## Next action

Keep stores/secrets/webhooks classified `KEEP_UNTIL_REDIRECT_WINDOW` until #2115 produces the first production 301 of hash `c2cee8362321099205b76b11f89485d4248a00b8abbbda354d15964f6b316e0d` and the 28-day window completes. Then execute the zero-use table above, family by family, on #2111 — never as a side effect of the bridge PR.

## Execution 2026-08-15 (post-#2133, no live cutover)

Classification started. Product feature freeze remains permanent. Repo **not** archived.

| Family | Campaign class | Removed this run? | Why |
|---|---|---|---|
| `bridge/` serve + Caddy + `redirect-bridge.yml` | `KEEP_TEMP_BRIDGE` | no | Only authorized remaining runtime; not installed on a public IP |
| Ingestion / DataLake / crawler / SEO jobs | `RETIRE` | no | Code remains in tree as evidence; no SmartLic worker was started; Railway deploys already disabled (#2132) |
| Product health canaries / LLM / trial mail | `RETIRE` | no | Same — do not start a worker to prove absence |
| Redis / OpenAI / Sentry / Mixpanel / Resend / Railway tokens | `RETIRE` | no | Live last-used UNKNOWN without owner dashboard login |
| Cloudflare token / `$SMARTLIC_ACME_EMAIL` | `KEEP_TEMP_BRIDGE` | no | Required for cutover/rollback; values ABSENT in this environment |
| Stripe secrets + existing-customer cancel / billing portal | `LEGAL_RETENTION` | no | Fiscal + residual cancel; new checkout already 410 |
| Supabase Auth / profiles / messages / LGPD export | `LEGAL_RETENTION` | no | PII obligations until tickets close |
| `pncp_raw_bids` / supplier contracts | `MIGRATE` | no | extra-cli / web-cfg#63 harvest not proven complete |
| `confenge.com.br` public surface | `MIGRATED` | n/a | Already owned by web-cfg (#68 merged) |
| `smartlic.tech` apex/www DNS+TLS | `KEEP_TEMP_BRIDGE` | no | Rollback target; still Railway fallback 404 |
| `api` / `app` Railway names | `RETIRE` | no | Leave `app` until www rollback no longer needs the CNAME |
| Product CI (backend/frontend/e2e/SEO/k6) | `RETIRE` | no | 14-day zero-use clock starts after first production 301; not started |
| `backend/start.sh` FastAPI/Redis/ARQ | `RETIRE` | no | File is residue, not a live process. Do not execute it |

Nothing was deleted from stores, secrets, or hosting in this run. Proven-unused **runtime** remains dead: no Railway/FastAPI/Next.js/Supabase/Redis/workers revived; no crawler/DataLake/public API as a permanent SmartLic process.
