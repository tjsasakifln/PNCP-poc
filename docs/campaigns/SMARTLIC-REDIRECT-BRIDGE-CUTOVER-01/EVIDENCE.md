# EVIDENCE — SMARTLIC-REDIRECT-BRIDGE-CUTOVER-01

Recorded: 2026-08-18T03:16:50Z
Branch: `goal/smartlic-redirect-cutover-20260818`
Canonical consume: SmartLic #2135 MERGED on `main` (`7b9e9da6`); this campaign continues that pin, it does not duplicate the execute set.
Open PRs touching bridge/: none implementing a second map. #2150 is closeout docs only.

## Hashes

| Pin | Value |
|---|---|
| manifesto SHA-256 | `9e5667c127fc5494f5849aece2234b13a1c1db10257a17274545019634506ca9` |
| config SHA-256 | `fd391e3667541953e6a830135c863f75452a27c879308fd0012d517740e537a4` |
| web-cfg inventory commit | `8a2f4d5bce7e23d0308246ed45ed4d58752984ac` |
| schema / version | `smartlic-url-map-v2` / `v2` |
| redirects / holds / retire | 11 / 54 / 1190 |
| persist allowlist | `utm_source, utm_medium, utm_campaign, utm_content, utm_term, jornada, origem, route_family, cta_id, asset_id, correlation_id, tema` |
| web-cfg main inventory.v2.sha256 | `9e5667c127fc5494f5849aece2234b13a1c1db10257a17274545019634506ca9` (no drift) |

generate --check ×2: `GENERATE_OK`. Pin comparison: PASS (15 fields).

## Tests

`python3 -m unittest discover -s bridge/tests -q` ×2 — **118 OK / 118 OK**. See scratch `bridge-tests.log`.
`bridge/tests/test_cutover_campaign.py` drives shipped `generate_main`, `policy.resolve`, `python3 -m bridge.serve`, `probe_targets` + GET+HEAD, and asserts campaign artifact hashes equal `bridge.pins`.

## Targets

`PASS` — 11 compiled ready rows GET+HEAD on `confenge.com.br`; shipped `probe_targets` also PASS. No loop/chain/soft-404.

## Canary

serve ×2 `PASS` via `python3 -m bridge.serve`. Caddy: `CADDY_ABSENT`. caddy binary not on PATH; accepted fallback is serve ×2 + assert_terminator_safe

## Deploy

Live DNS/TLS/ACME **not applied**. Credentials absent (`BRIDGE_PUBLIC_IPV4`, `SMARTLIC_ACME_EMAIL`, `CF_API_TOKEN`, `CF_ZONE_ID`). Railway remains on apex/www. `api.smartlic.tech` untouched.

## Verdict

**CUTOVER READY**

## Residual risk

- No authorized $BRIDGE_PUBLIC_IPV4 in this environment; founder file keeps the placeholder.
- Caddy binary absent here; terminator safety is covered by generate assert_terminator_safe + serve ×2.
- Observation window not started (no live production 301).
- www TLS SAN mismatch on Railway is expected until cutover.
- api.smartlic.tech remains Railway CNAME; not in this cutover.
