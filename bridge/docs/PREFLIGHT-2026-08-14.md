# Preflight — 2026-08-14T21:07:04Z

Dated evidence for SmartLic#2115. UNKNOWN remains UNKNOWN. This is not a DNS/TLS cutover.

## Manifesto pin

| Field | Value |
|---|---|
| Source | `tjsasakifln/web-cfg` commit `3f112bfbd9e6b042691e1c09812af00f42735adb` (PR #68, OPEN) |
| Path | `data/migration/smartlic-confenge/manifesto.v1.json` |
| SHA-256 | `c2cee8362321099205b76b11f89485d4248a00b8abbbda354d15964f6b316e0d` |
| Recomputed locally | **match** |
| Entries | 1255 (11 REDIRECT ready, 1244 RETIRE / expected 410) |

## DNS (getent / getaddrinfo)

| Name | A | Notes |
|---|---|---|
| `smartlic.tech` | `69.46.46.88` | Railway range |
| `www.smartlic.tech` | `69.46.46.117` | aliases `1376dcda.up.railway.app` |
| `api.smartlic.tech` | `69.46.46.116` | aliases `1us7c4ob.up.railway.app` |
| `confenge.com.br` | `75.2.60.5`, `99.83.231.61` | Netlify |
| NS / SOA / MX / TXT | UNKNOWN | `dig` not installed in this environment |

## HTTP

| URL | Result |
|---|---|
| `https://smartlic.tech/` | HTTP/2 **404** `server: railway-hikari` `x-railway-fallback: true` |
| `https://smartlic.tech/blog/aditivos-contratuais-o-que-sao-como-monitorar` | same Railway fallback 404 |
| `https://smartlic.tech/login` | same |
| `https://smartlic.tech/planos` | same |
| `https://smartlic.tech/v1/health` | same |
| `https://smartlic.tech/sitemap.xml` | same |
| `http://smartlic.tech/` | **301** → `https://smartlic.tech/` |
| `https://www.smartlic.tech/` | TLS fail (curl exit 60) |
| `https://api.smartlic.tech/` | Railway fallback 404 |
| `https://api.smartlic.tech/health/live` | Railway fallback 404 |
| `https://confenge.com.br/` | **200** Netlify |
| 6 ready CONFENGE targets | **200** Netlify (see below) |
| `https://www.confenge.com.br/` | **301** → `https://confenge.com.br/` |

Ready CONFENGE targets observed 200: `/aditivos-obras-publicas/`, `/atrasos-prorrogacao-obras-publicas/`, `/conteudos/matriz-de-riscos-reequilibrio-economico-financeiro/`, `/medicoes-glosas-obras-publicas/`, `/reequilibrio-obras-publicas/`, `/conteudos/atraso-pagamento-contrato-publico-suspender/`.

## TLS

| Host | Result |
|---|---|
| `smartlic.tech` | OK, SAN `smartlic.tech` only |
| `www.smartlic.tech` | **FAIL** — certificate hostname mismatch (`*.up.railway.app`) |
| `api.smartlic.tech` | OK, SAN `api.smartlic.tech` |
| `confenge.com.br` | OK, SAN `confenge.com.br` + `www.confenge.com.br` |
| `www.confenge.com.br` | OK, same SAN |

## Reverse proxy / named bridge

**UNKNOWN / not authorized / not deployed.** No named proxy covering `smartlic.tech` + `www` with a valid SAN. Cutover remains **BLOCKED**.

## Jobs / deployments still active

| Item | Observation |
|---|---|
| Railway apex/www/api | still answering as edge fallback; product health **not** a goal |
| `deploy/netcup` product topology | **removed** on `main` by #2132; must not be restored |
| Live GSC / backlinks | UNKNOWN (donor extract 2026-04-27 only) |
| Secrets / PII export | not performed (not required for this bridge) |

## Decision

Implement the in-repo hash-pinned 301/410 bridge. Do **not** change live DNS/TLS in this change. External cutover stays BLOCKED until a named reverse-proxy + certificate covering apex+www + rollback record exist.

Successor write-up (2026-08-15): `CUTOVER.md` names that path and records status `CUTOVER_READY`. This dated preflight is unchanged evidence.
