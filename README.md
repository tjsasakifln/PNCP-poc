# SmartLic — legacy migration source

> **Status:** sunset in progress. SmartLic is not an active product, brand, acquisition surface or independent public runtime.
>
> **Authoritative decision:** [web-cfg ADR-STRAT-002](https://github.com/tjsasakifln/web-cfg/blob/main/docs/architecture/ADR-STRAT-002-confenge-canonical-public-surface.md)

All useful public capability and search equity is being selectively migrated into [confenge.com.br](https://confenge.com.br). The target architecture is:

- `extra-cli`: canonical truth, identity, provenance and versioned `public_read_v1` contracts.
- `web-cfg`: sole public surface, tools, datasets, SEO and visitor journey.
- `warmbly`: commercial action and next-action orchestration.
- `SmartLic`: legacy migration source, reversible redirects and historical evidence until archive.

## Allowed work

Only inventory, evidence preservation, MIGRATE/REDIRECT/RETIRE mapping, compatibility shims, reversible bridge operations, security/availability necessary for migration and decommissioning.

## Forbidden work

No new SmartLic product features, pages, brand investment, SaaS/billing motion, crawler/DataLake, public CTA, independent SEO program or permanent runtime.

## Execution

- [web-cfg #61 — canonical program](https://github.com/tjsasakifln/web-cfg/issues/61)
- [web-cfg #62 — URL/equity migration](https://github.com/tjsasakifln/web-cfg/issues/62)
- [web-cfg #63 — asset harvest](https://github.com/tjsasakifln/web-cfg/issues/63)
- [SmartLic #2111 — decommission](https://github.com/tjsasakifln/SmartLic/issues/2111)
- [SmartLic #2115 — temporary migration bridge](https://github.com/tjsasakifln/SmartLic/issues/2115)

Historical strategy remains available in Git history. ADR-STRAT-001 and #1262 are superseded.
