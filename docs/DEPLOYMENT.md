# SmartLic deployment — migration bridge only

**Status:** legacy; no permanent production destination  
**Authority:** [CONFENGE ADR-STRAT-002](https://github.com/tjsasakifln/web-cfg/blob/main/docs/architecture/ADR-STRAT-002-confenge-canonical-public-surface.md)

Do not deploy SmartLic as a product, public brand or acquisition surface. Railway, Supabase, FastAPI, Redis and ARQ describe historical infrastructure only.

A deployment is allowed solely when it is the minimum reversible bridge needed to preserve a validated redirect, export migration evidence, contain a security/availability incident or complete decommissioning. The change must identify owner, expiry, rollback and exit criterion in #2115 or #2111.

Canonical public deployment belongs to `web-cfg` at `confenge.com.br`; truth services belong to `extra-cli`; commercial action belongs to Warmbly.
