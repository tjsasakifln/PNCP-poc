# Rollback — one action

Restore the last known bridge map. Do **not** start FastAPI, Next.js, Redis, ARQ, Supabase, or any SmartLic application.

## Current last-known state

`bridge/generated/previous/bridge-map.json` is the **pre-bridge** map: zero 301s, default 410. That is the honest state before the first 301 of hash `c2cee8362321099205b76b11f89485d4248a00b8abbbda354d15964f6b316e0d`.

## Command

```text
python3 -m bridge.generate --rollback
# then reload serve.py (SIGTERM + start) or `caddy reload` if the terminator is up
```

One step. `generated/bridge-map.json` becomes a copy of `generated/previous/bridge-map.json`.

## After a successful production 301

Before emitting a new map:

```text
python3 -m bridge.generate --snapshot-previous
python3 -m bridge.generate
```

`--snapshot-previous` copies the live map to `previous/` so rollback returns to the last working 301 set, not to SmartLic.

## DNS / TLS rollback

If cutover pointed `smartlic.tech` at this bridge, restore the **previous DNS records** exactly (see `CUTOVER.md`): apex A `69.46.46.88` TTL 60; delete www A; recreate www CNAME `app.smartlic.tech.` TTL 300. That is a DNS change, not a product redeploy. This change does **not** perform that DNS change.

## Rehearsal

`bridge/tests/test_generate.py::RollbackTests` applies the ready map, rolls back to previous, and asserts a ready path returns 410 with no Location. `test_serve.py` confirms serve.py never starts a product runtime.
