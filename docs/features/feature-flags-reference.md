# Feature Flags Reference

> **Auto-generated** — não editar manualmente.
> Gerado em: 2026-04-15 22:42 UTC
> Fonte: `config\features.py`
> Para regenerar: `cd backend && python scripts/generate_feature_flags_docs.py`

**Total:** 74 flags documentadas

## Geral

| Env Var | Tipo | Default | Descrição |
|---------|------|---------|-----------|
| `ENABLE_NEW_PRICING` | `bool` | `true` | Feature Flag: New Pricing Model (STORY-165) |
| `SCHEMA_CONTRACT_STRICT` | `bool` | `false` | STORY-414: Schema Contract Gate (Rollout faseado 14d) Default False in production (passive / log-only) so we do not block startup on transient PGRST002 errors; set to True on staging first and flip production only after a 7-14 day observation window. When True, a contract violation raises SystemExit at lifespan boot time. |

## LLM Arbiter Configuration (STORY-179 AC6)

| Env Var | Tipo | Default | Descrição |
|---------|------|---------|-----------|
| `LLM_ARBITER_ENABLED` | `bool` | `true` | — |
| `LLM_ARBITER_MODEL` | `str` | `gpt-4.1-nano` | — |
| `LLM_ARBITER_MAX_TOKENS` | `int` | `1` | — |
| `LLM_ARBITER_TEMPERATURE` | `float` | `0` | — |
| `OPENAI_TIMEOUT_S` | `float` | `5` | DEBT-SYS-008: Centralized LLM timeout (was hardcoded in llm_arbiter.py) GPT-4.1-nano p99 ≈ 1s; 5s = 5× p99. Prevents thread starvation on LLM hangs. Accepts OPENAI_TIMEOUT_S (preferred) or LLM_TIMEOUT_S (legacy alias). |
| `LLM_FUTURE_TIMEOUT_S` | `float` | `20` | DEBT-SYS-008: Per-future timeout for ThreadPoolExecutor LLM calls (filter/llm.py). Used by zero_match_batch, zero_match_individual, and arbiter phases. 20s = 4× p99 batch latency. Prevents thread starvation on LLM hangs. |
| `LLM_MAX_CONCURRENT` | `int` | `50` | STORY-4.1 (TD-SYS-014): Async runtime + Batch API. LLM_MAX_CONCURRENT caps the number of LLM calls in flight at any given time (previously hardcoded to ThreadPoolExecutor(max_workers=10)). |
| `LLM_BATCH_ENABLED` | `bool` | `false` | Offline Batch API gate — 24h SLA so not viable for /buscar, only for reclassify_pending_bids_job. Set to false to revert to live classification. |
| `LLM_BATCH_MIN_ITEMS` | `int` | `20` | — |
| `LLM_BATCH_POLL_INTERVAL_S` | `int` | `60` | — |
| `TERM_DENSITY_HIGH_THRESHOLD` | `float` | `0.05` | Term density thresholds (STORY-248 reviewed 2026-02-14 — kept unchanged) |
| `TERM_DENSITY_MEDIUM_THRESHOLD` | `float` | `0.02` | — |
| `TERM_DENSITY_LOW_THRESHOLD` | `float` | `0.01` | — |
| `QA_AUDIT_SAMPLE_RATE` | `float` | `0.10` | Filter QA |
| `ZERO_RESULTS_RELAXATION_ENABLED` | `bool` | `true` | Zero-results relaxation |
| `LLM_ZERO_MATCH_ENABLED` | `bool` | `true` | LLM Zero Match |
| `LLM_ZERO_MATCH_BATCH_SIZE` | `int` | `20` | — |
| `LLM_ZERO_MATCH_BATCH_TIMEOUT` | `float` | `5.0` | — |
| `FILTER_ZERO_MATCH_BUDGET_S` | `float` | `30` | — |
| `MAX_ZERO_MATCH_ITEMS` | `int` | `200` | — |
| `ZERO_MATCH_VALUE_RATIO` | `float` | `1.0` | — |
| `ASYNC_ZERO_MATCH_ENABLED` | `bool` | `false` | — |
| `ZERO_MATCH_JOB_TIMEOUT_S` | `int` | `120` | — |
| `LLM_FALLBACK_PENDING_ENABLED` | `bool` | `true` | — |
| `PARTIAL_DATA_SSE_ENABLED` | `bool` | `true` | — |
| `PENDING_REVIEW_TTL_SECONDS` | `int` | `86400` | — |
| `PENDING_REVIEW_MAX_RETRIES` | `int` | `3` | — |
| `PENDING_REVIEW_RETRY_DELAY` | `int` | `300` | — |
| `ITEM_INSPECTION_ENABLED` | `bool` | `true` | D-01: Item Inspection (Gray Zone) |
| `MAX_ITEM_INSPECTIONS` | `int` | `20` | — |
| `ITEM_INSPECTION_TIMEOUT` | `float` | `5` | — |
| `ITEM_INSPECTION_PHASE_TIMEOUT` | `float` | `15` | — |
| `ITEM_INSPECTION_CONCURRENCY` | `int` | `5` | — |
| `TRIAL_DURATION_DAYS` | `int` | `14` | STORY-264: Trial Duration |
| `TRIAL_EMAILS_ENABLED` | `bool` | `true` | — |
| `TRIAL_PAYWALL_ENABLED` | `bool` | `true` | — |
| `TRIAL_PAYWALL_DAY` | `int` | `7` | — |
| `TRIAL_PAYWALL_MAX_RESULTS` | `int` | `10` | — |
| `TRIAL_PAYWALL_MAX_PIPELINE` | `int` | `5` | — |
| `REFERRAL_EMAIL_ENABLED` | `bool` | `false` | SEO-PLAYBOOK §7.4 — Day-8 referral invitation email (opt-in, additive to the existing trial sequence). Default False to avoid disturbing production deliverability until validated end-to-end in staging. |
| `DAY3_ACTIVATION_EMAIL_ENABLED` | `bool` | `true` | SEO-PLAYBOOK §Day-3 Activation — conditional nudge for trial users that have not yet completed their first search (the "aha moment" predictor). Default False — flip on once the `first_analysis_viewed` signal is wired. |
| `SHARE_ACTIVATION_EMAIL_ENABLED` | `bool` | `false` | SEO-PLAYBOOK §7.1 / P6 — Day-3 share activation email. Triggered when a user has analyzed editais (opportunities_found > 0) but has NOT shared any analysis yet. Completes the viral loop: analyst analyzes → shares with decision maker → decision maker converts. Default False until validated. |
| `FEATURE_DISCOVERY_EMAILS_ENABLED` | `bool` | `true` | Zero-Churn P1 Frente 2B — Feature discovery emails (pipeline, excel, AI). 3 new emails on days 2, 5, 8 highlighting specific features. |
| `DATA_RETENTION_DAYS` | `int` | `30` | Zero-Churn P2 §2.2: Grace period data retention |
| `GRACE_DOWNLOAD_ENABLED` | `bool` | `true` | — |
| `TRIAL_EXTENSION_ENABLED` | `bool` | `true` | Zero-Churn P2 §8.2: Trial Extension as retention mechanism |
| `TRIAL_EXTENSION_MAX_DAYS` | `int` | `7` | — |
| `USD_TO_BRL_RATE` | `float` | `5.0` | DEBT-325: USD to BRL exchange rate for LLM cost estimation |
| `LLM_COST_ALERT_THRESHOLD` | `float` | `1.0` | DEBT-v3-S2 AC4: LLM cost alert threshold in USD per hour (default $1/h) |
| `VIABILITY_WEIGHT_MODALITY` | `float` | `0.30` | D-04: Viability Assessment |
| `VIABILITY_WEIGHT_TIMELINE` | `float` | `0.25` | — |
| `VIABILITY_WEIGHT_VALUE_FIT` | `float` | `0.25` | — |
| `VIABILITY_WEIGHT_GEOGRAPHY` | `float` | `0.20` | — |
| `METRICS_ENABLED` | `bool` | `true` | E-03: Prometheus Metrics |
| `METRICS_TOKEN` | `str` | `—` | — |
| `USER_FEEDBACK_ENABLED` | `bool` | `true` | D-05: User Feedback Loop |
| `USER_FEEDBACK_RATE_LIMIT` | `int` | `50` | — |
| `PROXIMITY_CONTEXT_ENABLED` | `bool` | `true` | SECTOR-PROX: Proximity Context |
| `PROXIMITY_WINDOW_SIZE` | `int` | `8` | — |
| `DEEP_ANALYSIS_RATE_LIMIT` | `int` | `20` | STORY-259: Bid Analysis |
| `BID_ANALYSIS_ENABLED` | `bool` | `true` | — |
| `AB_EXPERIMENTS_ENABLED` | `bool` | `false` | A/B Testing |
| `AB_ACTIVE_EXPERIMENTS` | `str` | `{}` | — |
| `TERM_SEARCH_LLM_AWARE` | `bool` | `false` | STORY-267: Term Search Quality Parity |
| `TERM_SEARCH_SYNONYMS` | `bool` | `false` | — |
| `TERM_SEARCH_VIABILITY_GENERIC` | `bool` | `false` | — |
| `TERM_SEARCH_FILTER_CONTEXT` | `bool` | `false` | — |
| `TERM_SEARCH_VALUE_RANGE_MIN` | `float` | `10000` | — |
| `TERM_SEARCH_VALUE_RANGE_MAX` | `float` | `50000000` | — |
| `TRIGRAM_FALLBACK_ENABLED` | `bool` | `true` | STORY-437: Trigram fuzzy fallback when FTS returns 0 results |
| `EMBEDDING_ENABLED` | `bool` | `false` | STORY-438: Semantic search via pgvector embeddings |
| `EMBEDDING_THRESHOLD` | `float` | `0.6` | — |
