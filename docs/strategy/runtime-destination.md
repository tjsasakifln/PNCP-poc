# Runtime destination — sunset record

**Authority:** [CONFENGE ADR-STRAT-002](https://github.com/tjsasakifln/web-cfg/blob/main/docs/architecture/ADR-STRAT-002-confenge-canonical-public-surface.md)

SmartLic has no permanent runtime destination. FastAPI, Redis, ARQ, Supabase and Railway are historical implementation details and may be retained only when necessary for a reversible migration bridge. Warmbly is not a SmartLic hosting destination; it owns commercial action.

The only approved runtime end state is:

- public experience in `web-cfg` at `confenge.com.br`;
- canonical truth and `public_read_v1` in `extra-cli`;
- commercial action in Warmbly;
- SmartLic redirect/bridge removed after monitored cutover.
