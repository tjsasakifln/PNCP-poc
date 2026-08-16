# CUTOVER — SmartLic#2115 redirect bridge

**Status:** engineering `CUTOVER_READY`; live DNS/TLS/ACME **BLOCKED**. See `CUTOVER_READINESS.md`.

This file is the operator plan. `CUTOVER_READINESS.md` is the unambiguous READY vs BLOCKED record. Live DNS/TLS/ACME on a public IP is **owner-apply only** and is **not** performed from this repository. web-cfg `feat/smartlic-equity-migration-62` is the counterpart pin; this bridge consumes only that hash.

| Gate | Value |
|---|---|
| Pin | `9e5667c127fc5494f5849aece2234b13a1c1db10257a17274545019634506ca9` (map embeds `8a2f4d5bce7e23d0308246ed45ed4d58752984ac`) |
| Config hash | `fd391e3667541953e6a830135c863f75452a27c879308fd0012d517740e537a4` |
| Execute set | exactly 11 URL-specific 301s + 54 HOLD fail-closed + default 410 |
| TLS path | Caddy ACME, one SAN cert `smartlic.tech` + `www.smartlic.tech` |
| Proxy | `reverse_proxy 127.0.0.1:8765` only (`python3 -m bridge.serve`) |
| Target host | `https://confenge.com.br` (Netlify). Ready targets probed HTTPS 200 |
| Rollback | `python3 -m bridge.generate --rollback` → `generated/previous` 410-only |
| Probes | `bridge/tests` + `--probe-targets` + serve launch ×2 |
| Destination IP | parameterized `$BRIDGE_PUBLIC_IPV4` — none live in discovery |

## Baseline (2026-08-14, reconfirmed 2026-08-15T02:21Z)

Do not treat these A records as a product runtime. They are the rollback target.

| Name | Record | TTL | Data |
|---|---|---:|---|
| `smartlic.tech` NS | NS | 86400 | `jermaine.ns.cloudflare.com.` / `ryleigh.ns.cloudflare.com.` |
| `smartlic.tech` | A | 60 | `69.46.46.88` (Railway) |
| `www.smartlic.tech` | CNAME | 300 | `app.smartlic.tech.` → `1376dcda.up.railway.app.` → A `69.46.46.117` |
| `api.smartlic.tech` | CNAME | 300 | `1us7c4ob.up.railway.app.` → A `69.46.46.116` |
| `app.smartlic.tech` | CNAME | 300 | `1376dcda.up.railway.app.` (leave in place) |
| `smartlic.tech` TXT | TXT | — | `google-site-verification=Aw8-Y5ify3ORrRN69yYgmAehSdO-3G5O65yW5Y3VEto` (leave) |
| `smartlic.tech` MX | MX | — | `0 smartlic.tech.` (leave) |
| `smartlic.tech` AAAA | — | — | none |

HTTP/TLS at baseline:

- `https://smartlic.tech/` → Railway fallback **404** (`x-railway-fallback: true`). Cert SAN `smartlic.tech` only (LE, expires 2026-09-16).
- `https://www.smartlic.tech/` → **TLS SAN mismatch** (`*.up.railway.app`).
- `http://smartlic.tech/` → 301 → `https://smartlic.tech/` (Railway hop; will go away after cutover).
- `https://api.smartlic.tech/` → Railway fallback 404. Not inventoried; stays 410 if ever pointed here.
- Ready CONFENGE targets → HTTPS **200**.

No named Netcup reverse-proxy covering apex+www was found. `deploy/netcup` product topology stays removed.

## Architecture

```text
Cloudflare DNS
  smartlic.tech     A  $BRIDGE_PUBLIC_IPV4
  www.smartlic.tech A  $BRIDGE_PUBLIC_IPV4
        │
        ▼
Caddy :80 + :443
  ACME HTTP-01 → one cert SAN {smartlic.tech, www.smartlic.tech}
  auto_https disable_redirects   (HTTP is proxied: one 301 hop, no chain)
  reverse_proxy 127.0.0.1:8765
        │
        ▼
python3 -m bridge.serve   DynamicUser, loopback only
  11 ready paths → 301 Location=https://confenge.com.br/...
  everything else including /login /signup /pricing /webhooks /v1 → 410, no Location
```

Config: `bridge/generated/Caddyfile` (from `python3 -m bridge.generate`). Units and firewall: `bridge/deploy/`.

## DNS plan (do not apply without owner authorization)

Registrar/DNS: **Cloudflare** (`jermaine` / `ryleigh`). Apex TTL is already 60s.

### Cutover records

After the host is up (`smartlic-bridge` + Caddy running, `:80` reachable on `$BRIDGE_PUBLIC_IPV4` for ACME):

1. Create `www` **A** `$BRIDGE_PUBLIC_IPV4` TTL **300**.
2. Delete `www` **CNAME** `app.smartlic.tech.`
3. Update apex **A** `69.46.46.88` → `$BRIDGE_PUBLIC_IPV4` TTL **60**.
4. Do **not** change NS, TXT, MX, `api`, or `app`.

Cloudflare API (token never committed; owner pastes locally):

```text
# export CF_API_TOKEN=...   CF_ZONE_ID=...   BRIDGE_PUBLIC_IPV4=...
# 1) list records
curl -sS -H "Authorization: Bearer $CF_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records?name=smartlic.tech,www.smartlic.tech"

# 2) POST www A
curl -sS -X POST -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" \
  "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records" \
  --data "{\"type\":\"A\",\"name\":\"www\",\"content\":\"$BRIDGE_PUBLIC_IPV4\",\"ttl\":300,\"proxied\":false}"

# 3) DELETE www CNAME (use the record id from step 1)
# curl -sS -X DELETE -H "Authorization: Bearer $CF_API_TOKEN" \
#   "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records/$WWW_CNAME_ID"

# 4) PATCH apex A
# curl -sS -X PATCH -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" \
#   "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records/$APEX_A_ID" \
#   --data "{\"type\":\"A\",\"name\":\"smartlic.tech\",\"content\":\"$BRIDGE_PUBLIC_IPV4\",\"ttl\":60,\"proxied\":false}"
```

Keep **proxied=false** (grey cloud) so Caddy, not Cloudflare, terminates TLS and ACME HTTP-01 reaches the host.

### Exact rollback records

1. PATCH apex **A** → `69.46.46.88` TTL **60**.
2. DELETE `www` **A**.
3. CREATE `www` **CNAME** `app.smartlic.tech.` TTL **300**, proxied=false.

That restores the 2026-08-14 baseline. It does **not** start SmartLic.

## Owner-only apply (single remaining human action)

Fill `/etc/smartlic-bridge/env`:

```text
BRIDGE_PUBLIC_IPV4=<public IPv4 of the chosen host>
SMARTLIC_ACME_EMAIL=<ops contact for Let's Encrypt>
```

Then, on that host, follow `bridge/deploy/README.md` steps 1–8, apply the DNS plan above, wait for Caddy to issue the SAN cert, and verify:

```text
curl -sI https://smartlic.tech/glossario/reajuste
# 301 Location: https://confenge.com.br/reequilibrio-obras-publicas/
curl -sI https://smartlic.tech/login
# 410, no Location
curl -sI https://www.smartlic.tech/glossario/reajuste
# same 301 (valid SAN)
```

The 28-day observation window starts at the first production 301 of this hash — not before.

## Security

- Non-root: `DynamicUser=yes` (bridge), `User=caddy` (terminator).
- Firewall: input drop; public TCP 22/80/443; `:8765` loopback only.
- Logs: no query strings, cookies, Authorization, bodies, or PII.
- No private keys in Git. Caddy data dir `0700`.
- Unmapped + `/login` `/signup` `/pricing` `/webhooks` `/v1` → 410.

## Observability (removal trigger)

`GET /__bridge/health` returns hashes + process-local counts by `rule_id` / status. Retention if persisted: 35 days. Removal: window complete + zero residual priority errors + #2111 archive gate. Do not start #2111 from this change.

## Close-out

1. **PR/commits:** follow-up on #2135 (`chore/redirect-bridge-2115`) — consume web-cfg#97 pin `9e5667c1…` / `8a2f4d5b`. Do not mix with superseded `3c5a5b7a…` / `78b7ebb9`.
2. **Baseline:** table above (Cloudflare; apex `69.46.46.88`; www CNAME → `69.46.46.117`).
3. **Architecture/config:** Caddy → `127.0.0.1:8765`; generated Caddyfile + `bridge/deploy/*`.
4. **TLS/DNS/rollback:** this file.
5. **Probes:** unit tests + `--probe-targets` + serve ×2.
6. **Security:** non-root, firewall, no-PII logs, no keys in Git.
7. **Status:** engineering `CUTOVER_READY`; live cutover **BLOCKED** (`CUTOVER_READINESS.md`).
8. **Remaining human action:** owner supplies `$BRIDGE_PUBLIC_IPV4` + `$SMARTLIC_ACME_EMAIL`, drops the kit, accepts web-cfg#97 (11-row set including remapped payment-delay), applies the Cloudflare records above. `@devops` push of this branch if not yet on origin.
9. **Next action:** owner apply. Then first production 301 starts the 28-day window. Do not expand into #2111 removals.
