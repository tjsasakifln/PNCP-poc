# Capability disposition — superseding #1262

**Status:** current migration register  
**Authority:** [CONFENGE ADR-STRAT-002](https://github.com/tjsasakifln/web-cfg/blob/main/docs/architecture/ADR-STRAT-002-confenge-canonical-public-surface.md)

The former KEEP + PRIORITIZE / KEEP + ADAPT / SUNSET / REPLACE / DEFER framework is replaced by a destination-first decision:

- **MIGRATE:** proven public utility moves to `web-cfg`; canonical facts/provenance stay in `extra-cli`; commercial action stays in Warmbly.
- **REDIRECT:** a legacy URL has a close, useful CONFENGE destination and receives an explicit monitored 301.
- **RETIRE:** duplicate, low-value, misleading or unsupported capability is removed with an appropriate status, never a blanket home redirect.
- **TEMPORARY BRIDGE:** only compatibility necessary for safe reversible cutover, with owner and expiry.

The evidence-backed portfolio and decisions are tracked in [web-cfg #63](https://github.com/tjsasakifln/web-cfg/issues/63).
