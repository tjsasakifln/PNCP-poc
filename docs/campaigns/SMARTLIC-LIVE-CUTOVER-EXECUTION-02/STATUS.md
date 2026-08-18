# SMARTLIC-LIVE-CUTOVER-EXECUTION-02

Status: `BLOCKED_SAFETY_CONFLICT`

Decision: **RETIRE** `smartlic.tech` as a public hostname (founder).
Canonical public surface: `confenge.com.br` (ADR-STRAT-002).

Not `CUTOVER_READY`. Not `SMARTLIC_RESTORED`. Not `PRODUCT_LIVE`.
No isolated bridge host. No DNS write. No first production 301.
Observation window not started. #2115 and #2111 remain OPEN.

## Why this is not an isolated-IPv4 residual

`smartlic.tech` / `www` / `api` / `app` no longer resolve (getaddrinfo empty;
DoH apex empty answers, www/api/app NXDOMAIN). The domain is still registered
(RDAP expiration 2027-02-07, NS still Cloudflare `jermaine`/`ryleigh`) but the
zone has no address records. Authorized Cloudflare token sees only
`confenge.com.br` (0 zones named `smartlic.tech`).

Resurrecting apex/www with a new IPv4 would recreate a SmartLic public surface
against the founder RETIRE and would risk writing `smartlic.tech` records into
the live `confenge.com.br` zone. `bridge.apply` now refuse-closes that path.

## Pins (unchanged)

- manifesto `9e5667c127fc5494f5849aece2234b13a1c1db10257a17274545019634506ca9`
- config `fd391e3667541953e6a830135c863f75452a27c879308fd0012d517740e537a4`
- inventory commit `8a2f4d5bce7e23d0308246ed45ed4d58752984ac`

`python3 -m bridge.generate --check` = `GENERATE_OK` redirects=11 default=410.
`python3 -m unittest discover -s bridge/tests` = OK.
Eleven CONFENGE destinations remain the pin targets; `https://confenge.com.br/` HTTPS 200.

## Live names

| Name | Now |
|---|---|
| `smartlic.tech` | no A; HTTPS/HTTP fail `gaierror` |
| `www.smartlic.tech` | NXDOMAIN |
| `api.smartlic.tech` | NXDOMAIN (not revived) |
| `confenge.com.br` | live Netlify HTTPS 200 |
| `api.confenge.com.br` | `159.195.18.88` (extra-cli/warmbly; still refused as bridge IPv4) |

## Apply

`python3 -m bridge.apply` → `BLOCKED_SAFETY_CONFLICT` / `decision=RETIRE` /
`hostname_retired=true` / `applied=false` / empty DNS plan.

It will not ask for an isolated IPv4 while apex+www have no addresses.
It will not mutate `confenge.com.br` even if that zone's token is exported.

## Single residual human action

Do not provision an isolated IPv4 and do not write `smartlic.tech` DNS.
Founder retired that hostname. Canonical public surface is `confenge.com.br`.
Do not insert `smartlic.tech` records into the `confenge.com.br` Cloudflare zone.
