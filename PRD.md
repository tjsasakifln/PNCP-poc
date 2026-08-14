# PRD — SmartLic legacy migration package

**Status:** decommissioning  
**Authority:** [ADR-STRAT-002](https://github.com/tjsasakifln/web-cfg/blob/main/docs/architecture/ADR-STRAT-002-confenge-canonical-public-surface.md)

SmartLic is not an active product, SaaS, subscription offering or inbound brand. This document specifies only the controlled migration package. ADR-STRAT-001 and #1262 are superseded.

## User

The migration team that must preserve useful public equity and evidence while consolidating the visitor experience into `confenge.com.br`.

## Required outcomes

- Export a reproducible inventory of URLs, impressions/clicks/queries, backlinks, public capabilities, data dependencies and provenance.
- Assign every relevant item MIGRATE, REDIRECT or RETIRE with owner and rationale.
- Preserve only temporary compatibility required for a safe cutover.
- Transfer selected UI/logic patterns to `web-cfg`, canonical facts to `extra-cli`, and commercial next actions to `warmbly`.
- Remove SmartLic navigation, CTAs, indexing and runtime after exit criteria are met.

## Non-goals

New public features, content campaigns, independent crawling/DataLake, monetization, billing, authentication expansion, SmartLic rebranding or permanent hosting.

## Acceptance

The migration is complete when [web-cfg #62](https://github.com/tjsasakifln/web-cfg/issues/62), [web-cfg #63](https://github.com/tjsasakifln/web-cfg/issues/63), [SmartLic #2115](https://github.com/tjsasakifln/SmartLic/issues/2115) and [SmartLic #2111](https://github.com/tjsasakifln/SmartLic/issues/2111) satisfy their exit criteria.
