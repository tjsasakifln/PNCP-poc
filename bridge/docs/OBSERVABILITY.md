# Observability — temporary, no PII

Retain only what is needed to decide removal of the bridge. This is not
an analytics product. Recording is a post-`resolve()` side effect and
must not change status or Location.

## Allowed

- One structured stderr/JSONL record per resolved request:
  `ts`, `manifesto_sha256`, `config_sha256`, `action` (family),
  `path_class`, `status`, `latency_ms`. Optional: `hops`, `critical_url`
  for known catalog / named paths only.
- Aggregated counts by family, path class, critical URL, and HTTP status.
- Process-local first-301 timestamp bound to the config hash. Scope is
  `process-local` unless SMARTLIC-002 writes a live apex/www
  `first-production-301`. Loopback 301s never start the 28-day window.
- Config/manifest hashes in response headers (`X-Bridge-Manifest-Hash`,
  `X-Bridge-Config-Hash`).
- `GET /__bridge/health` (also `/__bridge/metrics`): hashes + process-local
  counts + `window` summary. No query echo. `noindex`.
- `--records-file` JSONL, `--metrics-file` / `--export-file` on stop, and
  `python3 -m bridge.observe --records … --export …` for web-cfg ingest.

## Forbidden

- Query values, request bodies, cookies, Authorization, emails, phones,
  names, CNPJ, CPF, raw client IP, full User-Agent.
- Product analytics, Mixpanel, Prometheus, OpenTelemetry, Stripe, auth events.
- Payload dumps. IP hashing as a persistent identifier.
- Treating loopback/fixture 301 as production `first-production-301`.
- Convenience 301 to home on unexpected 404. Count the 404; keep 410/fail-closed.

## Caddy terminator

Access log strips the URI query and deletes Cookie, Authorization,
User-Agent, `remote_ip`, and `client_ip`.

## Retention

Process-local counters die with the process. Any on-disk window artifact
states **35 days** (28-day window + 7 days) then delete. No warehouse.

## Signals

`export.signals` is the evaluable set:

- `window_started` — live production first-301 of this config hash only.
- `rollback` — unexpected 404, 5xx, hops>1, errors, or target-health FAIL.
- `removal` — `HOLD_WINDOW_NOT_STARTED` | `HOLD_RESIDUAL` | `WAIT_WINDOW`
  | `READY_FOR_REVIEW`. Review is human; this module does not remove DNS.

Target health is `UNOBSERVED` until an operator supplies probe results.
The serve path does not fetch CONFENGE on each request.

## Removal

When the removal trigger in the manifesto fires, delete this file, the
serve process, JSONL/export files, and any persisted counters with the
rest of the bridge.
