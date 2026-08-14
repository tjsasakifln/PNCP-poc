# Observability — temporary, no PII

Retain only what is needed to decide removal of the bridge.

## Allowed

- Aggregated counts by `rule_id` (legacy path or `default-410`) and HTTP status.
- Process stderr: method + path **without** query string.
- Config/manifest hashes in response headers (`X-Bridge-Manifest-Hash`, `X-Bridge-Config-Hash`).

## Forbidden

- Query strings, request bodies, cookies, Authorization, emails, phones, names, CNPJ, CPF.
- Product analytics, Mixpanel, Stripe, auth events.
- Payload dumps.

## Retention

Process-local counters die with the process. If an operator later persists counts, retention is **35 days** (28-day window + 7 days) then delete. No warehouse.

## Removal

When the removal trigger in the manifesto fires, delete this file, the serve process, and any persisted counters with the rest of the bridge.
