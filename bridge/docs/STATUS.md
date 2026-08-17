# Status — SmartLic equity migration (web-cfg#62)

**Verdict:** `PIN_SYNCED_CUTOVER_READY`

| Field | Value |
|---|---|
| Date | 2026-08-16 |
| Inventory SHA-256 | `9e5667c127fc5494f5849aece2234b13a1c1db10257a17274545019634506ca9` |
| web-cfg commit | `8a2f4d5bce7e23d0308246ed45ed4d58752984ac` (PR #97 MERGED `bcc3fd6e` on main) |
| Config hash | `fd391e3667541953e6a830135c863f75452a27c879308fd0012d517740e537a4` |
| Supersedes | `3c5a5b7a…` / `78b7ebb9` (payment-delay remapped) |
| Ready REDIRECT_301 | 11 |
| HOLD_TARGET_NOT_READY | 54 |
| RETIRE_410 | 1190 |
| MIGRATE | 0 |
| IGNORE_NONCANONICAL | 0 (no www/http/query rows in the 2026-04-27 GSC extract) |
| LEGAL_SECURITY_HOLD | 0 |
| Live GSC / backlinks | UNKNOWN |
| First production 301 | NOT STARTED |
| DNS / TLS / cutover | BLOCKED (not authorized) |
| #62 / #2115 | remain OPEN |
| Merge / deploy / DNS from this goal | not performed |

## Why not READY_FOR_CUTOVER

Eleven CONFENGE destinations are live, indexable, and brand-clean. The SmartLic bridge config is deploy-ready on `chore/redirect-bridge-2115`. Live apply still needs `$BRIDGE_PUBLIC_IPV4`, ACME email, and a named Cloudflare operator. www TLS is currently a SAN mismatch on Railway. Observation cannot start without a production 301.

## Why not HOLD / NO_GO

The execute set of 11 URL-specific 301s is decided and tested. Unready equivalents are fail-closed HOLD, not weak substitutes. Nothing here restores SmartLic as a product.

## Integration order

1. Land web-cfg pin (this inventory hash) on **main** — done: PR #97 MERGED `bcc3fd6e`.
2. SmartLic vendors the same bytes and re-pins `bridge/pins.py` — this consume.
3. Human accept of the 11-row execute set — satisfied by merging #97.
4. Owner applies DNS/TLS using `SmartLic/bridge/docs/CUTOVER.md` — not from this checkout.
5. 28-day observation. Then #2111 archive gate. Do not close #62/#2115 before that.
