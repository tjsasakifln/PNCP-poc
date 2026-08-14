# SmartLic architecture — legacy boundary

**Status:** decommissioning  
**Authority:** [CONFENGE ADR-STRAT-002](https://github.com/tjsasakifln/web-cfg/blob/main/docs/architecture/ADR-STRAT-002-confenge-canonical-public-surface.md)

## Current canonical system

| Plane | Owner |
|---|---|
| Truth, identity and provenance | `extra-cli` |
| Public pages, tools, SEO and conversion | `web-cfg` at `confenge.com.br` |
| Commercial action | Warmbly |
| Legacy migration source | SmartLic |

The SmartLic codebase is historical donor material, not a reference architecture for new development. Its frontend, FastAPI services, Redis/ARQ jobs and Supabase dependencies may be read to migrate proven capability or kept temporarily for a reversible bridge. No new canonical fact, crawler, public feature, brand or permanent runtime belongs here.

All retained capability requires an explicit MIGRATE/REDIRECT/RETIRE owner and an exit criterion.
