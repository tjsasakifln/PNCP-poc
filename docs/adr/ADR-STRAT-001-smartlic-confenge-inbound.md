# ADR-STRAT-001 — SmartLic as CONFENGE inbound arm

| Field | Value |
|---|---|
| Status | SUPERSEDED |
| Date | 2026-08-13 |
| Superseded on | 2026-08-14 |
| Replacement | [web-cfg ADR-STRAT-002](https://github.com/tjsasakifln/web-cfg/blob/main/docs/architecture/ADR-STRAT-002-confenge-canonical-public-surface.md) |

## Historical decision

This ADR previously designated SmartLic as a public inbound surface consuming `extra-cli` `public_read_v1` and sending commercial actions to Warmbly.

## Superseding decision

CONFENGE now has one public surface: `confenge.com.br` in `web-cfg`. `extra-cli` remains the truth plane, Warmbly remains the action plane, and SmartLic is only a legacy migration source until archive. No new work may rely on the historical decision.

Issue #1262 is likewise superseded. Execution is tracked in [web-cfg #61](https://github.com/tjsasakifln/web-cfg/issues/61), [#62](https://github.com/tjsasakifln/web-cfg/issues/62), [#63](https://github.com/tjsasakifln/web-cfg/issues/63), SmartLic #2115 and #2111.
