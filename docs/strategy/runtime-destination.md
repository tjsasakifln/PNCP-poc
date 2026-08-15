# Runtime destination — sunset record

**Authority:** [CONFENGE ADR-STRAT-002](https://github.com/tjsasakifln/web-cfg/blob/main/docs/architecture/ADR-STRAT-002-confenge-canonical-public-surface.md)

SmartLic has no permanent runtime destination. FastAPI, Redis, ARQ, Supabase and Railway are historical implementation details and may be retained only when necessary for a reversible migration bridge. Warmbly is not a SmartLic hosting destination; it owns commercial action.

The only approved runtime end state is:

- public experience in `web-cfg` at `confenge.com.br`;
- canonical truth and `public_read_v1` in `extra-cli`;
- commercial action in Warmbly;
- SmartLic redirect/bridge removed after monitored cutover.

The only authorized #2115 remainder is the isolated hash-pinned bridge in `bridge/` (11 URL-specific 301s + default 410). Docs that still call #2115 a Netcup FastAPI/Next runtime are SUPERSEDED — see `bridge/docs/SUPERSEDED-NETCUP-PRODUCT.md`. Engineering status: `CUTOVER_READY`. Live DNS/TLS/ACME: **BLOCKED** until the owner supplies `$BRIDGE_PUBLIC_IPV4` + `$SMARTLIC_ACME_EMAIL` (`bridge/docs/CUTOVER_READINESS.md`).
