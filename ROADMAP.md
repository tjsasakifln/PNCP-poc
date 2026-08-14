# ROADMAP — SmartLic migration and sunset

**Updated:** 2026-08-14  
**Status:** migration-only  
**Authority:** [ADR-STRAT-002](https://github.com/tjsasakifln/web-cfg/blob/main/docs/architecture/ADR-STRAT-002-confenge-canonical-public-surface.md)

SmartLic is a legacy migration source. It is not an inbound surface, product or public brand. ADR-STRAT-001 and #1262 are superseded.

## Critical path

1. Preserve Search Console, URL, backlink, capability and provenance evidence.
2. Classify each useful asset and URL as MIGRATE, REDIRECT or RETIRE in [web-cfg #62](https://github.com/tjsasakifln/web-cfg/issues/62) and [#63](https://github.com/tjsasakifln/web-cfg/issues/63).
3. Implement selected public capability in `web-cfg` over `extra-cli` contracts.
4. Maintain only the minimum reversible redirect/bridge runtime in [#2115](https://github.com/tjsasakifln/SmartLic/issues/2115).
5. Validate canonical tags, sitemaps, redirects, crawl/indexing and conversion.
6. Remove remaining runtime and archive the repository through [#2111](https://github.com/tjsasakifln/SmartLic/issues/2111).

## Exit criteria

No active SmartLic product/brand/CTA, no independent acquisition or canonical public URL, no permanent runtime, all retained data/code has an explicit owner, redirects are documented and monitored, and the repository is archived read-only.
