# Deploy kit — Caddy TLS terminator → local `bridge.serve`

Minimum path. No FastAPI, Next.js, Redis, ARQ, Supabase, or Railway product runtime.

```text
Internet :80/:443
    → Caddy (ACME SAN: smartlic.tech + www.smartlic.tech)
        → 127.0.0.1:8765  python3 -m bridge.serve
            → 11 URL-specific 301  |  HOLD/RETIRE/unmapped 410
```

## Host

Any public IPv4 the owner names as `BRIDGE_PUBLIC_IPV4`. This environment did not find a live Netcup SmartLic unit or an already-authorized bridge IP. Do not restore `/opt/smartlic` product units.

## Install (on the host, after owner supplies the IP)

1. Create users/dirs. Caddy's distro package already has `caddy`. The bridge unit uses `DynamicUser=yes`.
2. Copy the repo's `bridge/` tree to `/opt/smartlic-bridge/bridge` (so `python3 -m bridge.serve` works with `PYTHONPATH=/opt/smartlic-bridge`).
3. `python3 -m bridge.generate --check` on the host. Confirm `GENERATE_OK` and hashes:
   - manifesto `9e5667c127fc5494f5849aece2234b13a1c1db10257a17274545019634506ca9`
   - config `fd391e3667541953e6a830135c863f75452a27c879308fd0012d517740e537a4`
4. `install -d -o caddy -g caddy -m 0700 /var/lib/caddy`
5. `install -m 0644 bridge/generated/Caddyfile /etc/caddy/Caddyfile`
6. `install -d -m 0750 /etc/smartlic-bridge && cp bridge/deploy/env.example /etc/smartlic-bridge/env` and fill `SMARTLIC_ACME_EMAIL` + `BRIDGE_PUBLIC_IPV4`.
7. Install units from this directory. `systemctl enable --now smartlic-bridge caddy-bridge` (or the distro `caddy` unit pointing at the same Caddyfile).
8. Apply `nftables.conf`. Confirm `ss -lntp` shows `:8765` on `127.0.0.1` only; `:80`/`:443` on the public address.
9. **Do not change public DNS yet.** Rehearse locally:
   `curl -sI -H 'Host: smartlic.tech' http://127.0.0.1:8765/glossario/reajuste`
10. Owner applies DNS + waits for ACME. Exact records: `../docs/CUTOVER.md`.

## TLS

- Issuer: Let's Encrypt via Caddy ACME HTTP-01 (port 80 must reach this host after DNS).
- Names: `smartlic.tech` and `www.smartlic.tech` on **one** certificate (SAN).
- Renewal: Caddy's built-in scheduler; no cron, no committed key.
- Permissions: `/var/lib/caddy` mode `0700`, user `caddy`. Never `git add` that directory.

## Least privilege

| Process | User | Listen | Capabilities |
|---|---|---|---|
| `bridge.serve` | DynamicUser (non-root) | `127.0.0.1:8765` | none |
| Caddy | `caddy` | `:80`, `:443` | `CAP_NET_BIND_SERVICE` only |

Firewall input policy drop; public TCP 22/80/443 only.

## Logs

Caddy stdout filter deletes URI query, Cookie, Authorization. `serve.py` logs method + path without query. Do not persist bodies.

## Rollback

`python3 -m bridge.generate --rollback` then `systemctl reload caddy-bridge` (or restart `smartlic-bridge`). That is 410-only. It does not start SmartLic.
