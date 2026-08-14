# SmartLic workflow authority

SmartLic is a legacy migration source under CONFENGE ADR-STRAT-002. Active
workflows may validate retained code, security, data-retention obligations and
the decommission plan. They must not deploy a SmartLic product or operate a
public SmartLic runtime.

Removed on 2026-08-14:

- Railway production and staging deployment;
- Railway environment parity and production-environment audit;
- SmartLic production smoke/health incident automation;
- Supabase/Railway backup, data-parity, sector-sync and load-test schedules;
- IndexNow submission for the retired public surface;
- SmartLic product Dockerfiles, Compose topology and production/staging env examples.

The runtime-authority guard scans executable paths. Historical material belongs
under `docs/` or `docs/archive/` and is not deployment authority.

Any temporary redirect bridge must first be approved in SmartLic #2115 and
web-cfg #62. Its allowlist entry must identify an owner, reason and expiry date.
