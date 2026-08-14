# CLAUDE.md

## Authoritative scope

SmartLic is a legacy migration source being sunset. Read [CONFENGE ADR-STRAT-002](https://github.com/tjsasakifln/web-cfg/blob/main/docs/architecture/ADR-STRAT-002-confenge-canonical-public-surface.md) before any change.

- `confenge.com.br` / `web-cfg` is the sole public brand and visitor surface.
- `extra-cli` owns canonical facts, identity, provenance and versioned public-read contracts.
- `warmbly` owns commercial action.
- SmartLic work is limited to asset inventory, migration, redirects, compatibility necessary for cutover, incident containment and decommissioning.

Do not add product features, new indexable pages, SmartLic CTAs/brand, billing/SaaS, crawler/DataLake, independent analytics growth loops or permanent runtime. Prefer deleting or freezing scope once migration evidence is preserved.

Every pull request must name its MIGRATE/REDIRECT/RETIRE decision, destination owner, rollback and exit criterion. ADR-STRAT-001 and #1262 are superseded.
