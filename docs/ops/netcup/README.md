> **SUPERSEDED (2026-08-14).** #2115 is **not** a Netcup SmartLic application. Do not install Next.js, FastAPI, Redis, ARQ, Caddy product units, or `/opt/smartlic` as a public runtime. Authorized remainder: hash-pinned 11 URL-specific 301s + default 410 in `bridge/`. See `bridge/docs/SUPERSEDED-NETCUP-PRODUCT.md` and `RUNTIME-AUTHORITY.md`.

# Runtime mínimo Netcup — #2115

**Status:** SUPERSEDED — historical evidence only.

The topology below (Caddy → Next :3000 / FastAPI :8000 / Redis / ARQ) described a product rebuild that is **forbidden**. `deploy/netcup/` was removed. Do not recreate it.

Historical target (do not execute):

```text
Caddy (TLS)
  → Next.js :3000
  → FastAPI :8000
      → extra-cli public_read_v1
```

Authorized bridge path: Caddy ACME SAN apex+www → `127.0.0.1:8765`. Status `CUTOVER_READY` in `bridge/docs/CUTOVER.md`. Do not restore this product topology.
