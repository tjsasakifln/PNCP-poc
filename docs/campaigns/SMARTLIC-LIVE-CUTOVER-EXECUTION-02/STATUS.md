# SMARTLIC-LIVE-CUTOVER-EXECUTION-02

Status: `BLOCKED_SAFETY_CONFLICT`

Not `CUTOVER_READY`. Not `SMARTLIC_RESTORED`. Not `PRODUCT_LIVE`.
No first production 301 of pin
`fd391e3667541953e6a830135c863f75452a27c879308fd0012d517740e537a4`.
Observation window not started. #2115 and #2111 remain OPEN.

## Pins (origin/main includes #2151 `df9141d3`)

- manifesto `9e5667c127fc5494f5849aece2234b13a1c1db10257a17274545019634506ca9`
- config `fd391e3667541953e6a830135c863f75452a27c879308fd0012d517740e537a4`
- inventory commit `8a2f4d5bce7e23d0308246ed45ed4d58752984ac`

`python3 -m bridge.generate --check` ×2 = `GENERATE_OK` redirects=11 default=410.
`python3 -m unittest discover -s bridge/tests` ×2 + post-change suite = OK.
Eleven CONFENGE destinations HTTPS 200 via shipped `probe_targets`.

## Authorized routes exhausted (presence only)

| Route | Present |
|---|---|
| process env `BRIDGE_PUBLIC_IPV4` / `SMARTLIC_ACME_EMAIL` / `CF_API_TOKEN` / `CF_ZONE_ID` | no |
| `/etc/smartlic-bridge/env` | no |
| GitHub repo secrets with those names | no |
| official CLI secret stores (`op`, `pass`, `sops`, `vault`, `wrangler`, `cloudflared`) | no |
| SSH config / known hosts | no |
| public IPv4 bindable on this host | no (`:80`/`:443` PermissionError; WSL2; no docker/caddy) |

## DNS/TLS baseline (unchanged)

| Name | Record | Data |
|---|---|---|
| `smartlic.tech` | A 60 | `69.46.46.88` (Railway) |
| `www.smartlic.tech` | CNAME 300 | `app.smartlic.tech.` → `69.46.46.117` |
| `api.smartlic.tech` | CNAME | `1us7c4ob.up.railway.app.` → `69.46.46.116` (not mutated) |

Apex TLS SAN `smartlic.tech` only. www TLS SAN mismatch (`*.up.railway.app`).
Public 11 ready paths: Railway fallback **404**. Not 301.

## What is running

Loopback `python3 -m bridge.serve --host 127.0.0.1 --port 8765`:
11/11 HEAD+GET 301 + pinned Location + config hash; HOLD/RETIRE/auth/API/malicious 410 no Location;
two restart cycles identical; `generate --rollback` rehearsal 410-only; no product runtime.

Shipped `python3 -m bridge.apply` fail-closes without secrets, refuses `api.smartlic.tech`,
refuses product commands, and refuses to set `observation_started_at` from loopback/fixture/mock.

## Safety conflict

Already-configured SSH reaches extra-cli/warmbly production `159.195.18.88`
(`api.confenge.com.br` on :80/:443; docker warmbly stack). `bridge.apply` now
refuses that IPv4. `/opt/smartlic` product tree was not started. nginx was not
edited. DNS was not pointed at this host.

## Single residual human action

Write `/etc/smartlic-bridge/env` (mode 0640) on an **isolated** public IPv4 host
that is **not** `159.195.18.88`, with `BRIDGE_PUBLIC_IPV4=<that isolated IPv4>`
and `SMARTLIC_ACME_EMAIL=<ops contact>`, export `CF_API_TOKEN` and `CF_ZONE_ID`
in the apply shell, then re-run `python3 -m bridge.apply`.
