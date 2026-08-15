# CUTOVER_READINESS — SmartLic#2115 / PR #2133

**Recorded:** 2026-08-15  
**This document does not claim live cutover completed.**  
Engineering gates can be `CUTOVER_READY` while live DNS/TLS remains **BLOCKED**.

| Lane | Verdict |
|---|---|
| In-repo bridge (hash pin, 11 301s, default 410, tests, deploy kit) | **READY** |
| Live DNS / Cloudflare / TLS / ACME / first production 301 | **BLOCKED** |
| web-cfg#68 human accept + merge | **BLOCKED** |
| #2115 issue DoD (verified + observed + removed) | **BLOCKED** |

## READY

These are closed on PR #2133 HEAD. They are not production proof.

1. **Approved execute set** — exactly 11 URL-specific REDIRECT rows, all `status=ready`, all `expected_http=301`. 1244 RETIRE rows stay default 410. No `/*` → CONFENGE home, no `/consultoria-b2g/`.
2. **Hash pin unchanged** — manifesto SHA-256 `c2cee8362321099205b76b11f89485d4248a00b8abbbda354d15964f6b316e0d`. Config hash `c07c1a5dc99932ae0536380e904379418b6a16015c02ac3c80f36660ab79ea68`. Map still embeds original pin commit `3f112bfbd9e6b042691e1c09812af00f42735adb`. After web-cfg#68 rebase the same bytes live at `dad3414c7a0073d0c1860d19704cff7e2a6e3b24` (citation only — map not regenerated).
3. **Default 410** — unmapped paths, `/`, `/login`, `/signup`, `/planos`, `/pricing`, `/webhooks/*`, `/v1/*` return 410 with no `Location`.
4. **No wildcard / no chain** — validator rejects `*` and generic targets. Caddy `auto_https disable_redirects` so HTTP stays one 301 hop. Policy `hops=1` on ready rows.
5. **Query allowlist + PII stripped** — persist list from the manifesto (`utm_*`, `jornada`, `origem`, `route_family`, `cta_id`, `asset_id`, `correlation_id`, `tema`). `email` / `phone` / `name` / `cnpj` / `cpf` / `token` dropped. Caddy logs strip `?.*`.
6. **Non-root** — `DynamicUser=yes` (bridge), `User=caddy` (terminator). Firewall input drop; public TCP 22/80/443; `:8765` loopback only.
7. **TLS/ACME plan written, not applied** — Caddy HTTP-01, one SAN cert `smartlic.tech` + `www.smartlic.tech`, email from `$SMARTLIC_ACME_EMAIL`. No private key in Git.
8. **Rollback to 410-only** — `python3 -m bridge.generate --rollback` restores `generated/previous/` (zero 301s). Does not start SmartLic.
9. **No SmartLic runtime** — stdlib `python3 -m bridge.serve` only. No FastAPI / Next.js / Redis / ARQ / Supabase / Stripe / `deploy/netcup` product boot.
10. **11/11 CONFENGE targets re-proved live** — HTTPS GET ×2 on 2026-08-15: HTTP 200, host `confenge.com.br`, hops=0, no SmartLic brand, no soft-404. Runs agreed.
11. **Shipped tests + real entry** — `python3 -m bridge.generate --check` → `GENERATE_OK`. `python3 -m unittest discover -s bridge/tests -v` → 38 OK. `python3 -m bridge.serve` launched twice on loopback: ready path 301 + exact Location; `/login` and unmapped 410, no Location; config hash identical.

## BLOCKED

Do not apply DNS, Cloudflare, TLS, or ACME until a human owner fills the inputs below and explicitly authorizes the change.

1. **`$BRIDGE_PUBLIC_IPV4`** — no authorized public IPv4 exists in discovery. Apex still `69.46.46.88` (Railway).
2. **`$SMARTLIC_ACME_EMAIL`** — Let's Encrypt account contact. Empty in `bridge/deploy/env.example`. Not a secret, still owner-supplied.
3. **Cloudflare apply authorization** — NS remain `jermaine` / `ryleigh`. Token / zone id never committed. Owner must apply the records in `CUTOVER.md`.
4. **web-cfg#68** — still OPEN. In-repo 11-row accept is ready for a human. Pin bytes are frozen. Do not invent a new execute set if #68 later changes the hash.
5. **Live TLS covering apex+www** — 2026-08-15 read-only: apex cert SAN `smartlic.tech` only (expires 2026-09-16); `www.smartlic.tech` TLS hostname mismatch (`*.up.railway.app`). HTTP apex is Railway fallback **404** (`x-railway-fallback: true`).
6. **Observation window** — 28 days after the first production 301 of this hash. **Not started.**
7. **#2115 DoD** — “verified, observed and removed.” Observation and removal cannot happen without the forbidden live DNS step.
8. **Host install** — kit is in-repo only. No evidence this unit is running on any public IP.

## Exact human inputs

Owner fills `/etc/smartlic-bridge/env` (mode 0640) **on the chosen host**, then authorizes DNS:

```text
BRIDGE_PUBLIC_IPV4=<public IPv4 of the chosen host>
SMARTLIC_ACME_EMAIL=<ops contact for Let's Encrypt>
```

Also required before DNS:

| Input | Why |
|---|---|
| Human accept of the 11-row set on web-cfg#68 | Counterpart remains the authority for the execute set |
| Cloudflare API token + zone id (local only) | To PATCH apex A and replace www CNAME |
| Confirmation that `:80` on `$BRIDGE_PUBLIC_IPV4` reaches Caddy | ACME HTTP-01 |
| Explicit “apply DNS now” from the founder / owner | This repository must not mutate live DNS |

Optional (not blocking engineering, blocking GSC close-out later): Search Console Change-of-Address — **HUMAN ACTION**, not started, not this PR.

## Exact rollback

**Bridge config (one command, no product runtime):**

```text
python3 -m bridge.generate --rollback
# then SIGTERM + start `python3 -m bridge.serve`, or `caddy reload` if the terminator is up
```

That restores `generated/previous/` = pre-bridge **410-only** (zero 301s).

**DNS / TLS (only if cutover records were applied):**

1. PATCH apex **A** → `69.46.46.88` TTL **60**.
2. DELETE `www` **A**.
3. CREATE `www` **CNAME** `app.smartlic.tech.` TTL **300**, proxied=false.

That is the 2026-08-14/15 baseline. It returns visitors to the Railway fallback 404. It does **not** start SmartLic.

## Live baseline (read-only, 2026-08-15)

Do not treat these as a product runtime. They are the rollback target.

| Name | Observed |
|---|---|
| `smartlic.tech` A | `69.46.46.88` |
| `www.smartlic.tech` A | `69.46.46.117` (via `app.smartlic.tech` / Railway) |
| `api.smartlic.tech` A | `69.46.46.116` |
| `https://smartlic.tech/` | HTTP/2 **404** `x-railway-fallback: true` |
| `https://www.smartlic.tech/` | TLS SAN mismatch |
| DNS/TLS mutation this change | **none** |

## Next action (single)

Owner supplies `$BRIDGE_PUBLIC_IPV4` + `$SMARTLIC_ACME_EMAIL`, installs `bridge/deploy/`, accepts web-cfg#68, then applies the Cloudflare records in `CUTOVER.md`. Not before. Do not expand into #2111 removals from this file.
