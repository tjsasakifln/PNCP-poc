# Runbook — ponte #2115

**Owner:** SmartLic#2115 operator (Gage / @devops for DNS).  
**Cost:** UNKNOWN until an invoice exists. Expected: DNS + TLS + a static 301/410 edge (cents to low dollars). Railway app cost should go to zero — do not keep the failed app as the bridge.  
**Manifesto SHA-256:** `c2cee8362321099205b76b11f89485d4248a00b8abbbda354d15964f6b316e0d`  
**web-cfg commit (map pin):** `3f112bfbd9e6b042691e1c09812af00f42735adb`  
**web-cfg commit (citation after #68 rebase):** `dad3414c7a0073d0c1860d19704cff7e2a6e3b24` (same manifesto bytes)

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
