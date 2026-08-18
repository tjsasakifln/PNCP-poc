# REMOVAL_CRITERIA — SMARTLIC-REDIRECT-BRIDGE-CUTOVER-01

Owner: SmartLic#2115
Config: `fd391e3667541953e6a830135c863f75452a27c879308fd0012d517740e537a4`
Manifesto: `9e5667c127fc5494f5849aece2234b13a1c1db10257a17274545019634506ca9`
Observation window: 28 days after the **first production 301** of this hash (live apex/www only; loopback does not start the window).

## Keep the bridge until all are true

1. Observation window complete (28 days from first live 301 of this hash).
2. Zero residual priority errors: no ready-row 5xx/chain/loop/soft-404; no HOLD/RETIRE 301.
3. Critical backlinks (if any become known) point at CONFENGE or are accepted as retired.
4. SmartLic#2111 archive gate is ready (this campaign does not execute #2111).

## Removal trigger (from the pinned map)

Remove smartlic.tech bridge only after: 28-day observation of this hash, zero residual priority 404/5xx/chain, critical backlinks (if any become known) point at CONFENGE or are accepted as retired, and SmartLic#2111 archive gate.

## Logs to keep (minimum, no PII)

- status, path family / path class, referrer host if present
- manifesto/config hashes
- no query values, cookies, Authorization, emails, CNPJ, bodies, client IP

Retention of any persisted window artifact: 35 days then delete.

## What to delete at removal

- public A records pointing at the bridge host
- Caddy unit + `/var/lib/caddy` (private keys never in Git)
- `python3 -m bridge.serve` unit
- this campaign directory after the final record is archived in #2111

Railway/app SmartLic must stay **off** `smartlic.tech` / `www`. `api.smartlic.tech` is not recovered.
