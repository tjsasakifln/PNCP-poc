# ROLLBACK — SMARTLIC-REDIRECT-BRIDGE-CUTOVER-01

Do **not** start FastAPI, Next.js, Redis, ARQ, Supabase, Stripe, or any SmartLic application.

## Config (always available)

```text
python3 -m bridge.generate --rollback
# then SIGTERM + start `python3 -m bridge.serve`, or `systemctl reload caddy-bridge`
```

Restores `bridge/generated/previous/` (zero 301s, default 410). Manifesto hash stays
`9e5667c127fc5494f5849aece2234b13a1c1db10257a17274545019634506ca9`. Live ready config was `fd391e3667541953e6a830135c863f75452a27c879308fd0012d517740e537a4`.
This is the pre-bridge fail-closed map.

## DNS / TLS (only if the founder applied cutover records)

1. PATCH apex **A** `smartlic.tech` → `69.46.46.88` TTL **60**, proxied=false.
2. DELETE `www` **A**.
3. CREATE `www` **CNAME** `app.smartlic.tech.` TTL **300**, proxied=false.
4. Do **not** change NS, TXT, MX, `api`, or `app`.

```text
# export CF_API_TOKEN=... CF_ZONE_ID=...   # local only; never commit
curl -sS -X PATCH -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records/$APEX_A_ID" \
  --data '{"type":"A","name":"smartlic.tech","content":"69.46.46.88","ttl":60,"proxied":false}'
curl -sS -X DELETE -H "Authorization: Bearer $CF_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records/$WWW_A_ID"
curl -sS -X POST -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records" \
  --data '{"type":"CNAME","name":"www","content":"app.smartlic.tech.","ttl":300,"proxied":false}'
```

That restores the 2026-08-14/15 Railway fallback 404. It does **not** start SmartLic.

## Immediate rollback if

- A ready Location/canonical differs from the pin
- Redirect chain, loop, or wildcard
- Unapproved path 301s instead of 410
- TLS invalid
- 5xx on canary
- Soft-404 / generic destination
- Secret or SmartLic product identity reappears

## Canary rehearsal of config rollback

`bridge/tests/test_generate.py::RollbackTests` and `bridge.preflight.run_local_blackbox`
apply the ready map, roll back, and require every ready path to return 410 with no Location.
