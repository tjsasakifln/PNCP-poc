# Runbook — ponte #2115

**Owner:** SmartLic#2115 operator (Gage / @devops for DNS).  
**Cost:** UNKNOWN until an invoice exists. Expected: DNS + TLS + a static 301/410 edge (cents to low dollars). Railway app cost should go to zero — do not keep the failed app as the bridge.  
**Manifesto SHA-256:** `9e5667c127fc5494f5849aece2234b13a1c1db10257a17274545019634506ca9`  
**web-cfg commit (map pin):** `8a2f4d5bce7e23d0308246ed45ed4d58752984ac`  
**web-cfg counterpart:** **OPEN** PR #97 on `feat/smartlic-equity-migration-62`  
**Config hash:** `fd391e3667541953e6a830135c863f75452a27c879308fd0012d517740e537a4`  
**Supersedes:** `3c5a5b7aeb173a16cfb65c0314827d9022ba1b387901d1718e4fdfcbd0363023` / `78b7ebb9` (payment-delay remapped onto `/conteudos/atraso-pagamento-contrato-publico-suspender/`)

## What this is

A dedicated redirect process. It loads `bridge/generated/bridge-map.json` (11 URL-specific 301s, default 410). It is not SmartLic, not FastAPI, not Next.js, not a Netcup product rebuild.

## Commands

```text
python3 -m bridge.generate                 # validate pin + emit generated/
python3 -m bridge.generate --check         # same + hash self-check
python3 -m bridge.generate --probe-targets # also require live 200 on CONFENGE targets
python3 -m unittest discover -s bridge/tests -v
python3 -m bridge.serve --host 127.0.0.1 --port 8765
```

`generated/Caddyfile` is the TLS terminator: ACME SAN `smartlic.tech` + `www.smartlic.tech`, reverse-proxy **only** to `127.0.0.1:8765`. It must never proxy `:8000` or `:3000`. Units and firewall: `bridge/deploy/`.

## Observation window

Starts at the first production 301 of this hash. Duration: **28 days**. Not started (engineering `CUTOVER_READY`; owner has not applied DNS).

### Investigate if

- Any ready target returns unexpected 404/5xx (threshold: 1 confirmed request).
- Redirect chain (>1 Location hop) or loop on a ready row.
- Soft 404 on a ready target.
- TLS/DNS failure on `smartlic.tech` after cutover.
- Lead persist path down on CONFENGE (`/.netlify/functions/lead`).
- GSC clicks on the 11 legacy paths drop to zero for 14 consecutive days while impressions remain, after 7-day indexing lag.

### Rollback if

- TLS or DNS outage > 30 minutes on the bridge host after cutover.
- ≥1 ready row loops or chains.
- ≥1 ready CONFENGE target 5xx for > 15 minutes.
- Lead persist path down during the window.

Rollback = one command, see `ROLLBACK.md`. It does **not** redeploy SmartLic.

## Expiry and removal trigger

- Review 28 days after cutover, then weekly until removal.
- Remove `smartlic.tech` hosting/DNS only after: window complete, zero residual priority errors, later-discovered critical backlinks accepted or remapped, SmartLic#2111 archive gate.
- Temporary exceptions expire. Kill switch = `generated/previous/` (410-only pre-bridge map).

## Cutover — CUTOVER_READY (owner apply)

Named path, rollback, probes and pin are closed. Exact Cloudflare records and the remaining human commands are in `CUTOVER.md`. Do not change DNS from this checkout without owner authorization.
