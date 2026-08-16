# Integration order — web-cfg#62 ↔ SmartLic#2115

Exact sequence. Do not invert. Do not merge or apply DNS from the implementer checkout.

1. **web-cfg pin.** Commit `data/migrations/smartlic-url-map/inventory.v2.json` (and the byte-identical `data/migration/smartlic-confenge/manifesto.v1.json`) on `feat/smartlic-equity-migration-62` at `8a2f4d5bce7e23d0308246ed45ed4d58752984ac` (PR #97, OPEN). Record SHA-256 `9e5667c127fc5494f5849aece2234b13a1c1db10257a17274545019634506ca9`. Supersedes `3c5a5b7a…` / `78b7ebb9`.
2. **SmartLic consume.** On `chore/redirect-bridge-2115`, copy those bytes to `bridge/manifest/manifesto.v1.json`, set `PINNED_SHA256` to that digest, set `PINNED_COMMIT` to `8a2f4d5bce7e23d0308246ed45ed4d58752984ac`, regenerate `bridge/generated/` via `python3 -m bridge.generate`. Config hash is computed, not typed: `fd391e3667541953e6a830135c863f75452a27c879308fd0012d517740e537a4`.
3. **Human accept.** Review the 11 ready 301s (including remapped `/blog/orgaos-risco-atraso-pagamento-licitacao` → `/conteudos/atraso-pagamento-contrato-publico-suspender/`) and the 54 HOLD fail-closed list. web-cfg#62 / PR #97 and SmartLic#2115 stay OPEN.
4. **Owner cutover.** Only after a named host (`$BRIDGE_PUBLIC_IPV4`) and ACME email exist. Commands live in `SmartLic/bridge/docs/CUTOVER.md`. This goal does not run them.
5. **Observe 28 days** from the first production 301 of this hash. Then review removal → #2111. Do not archive the SmartLic repo before that gate.

Rebuild: `python3 scripts/legacy_equity/build_inventory.py`  
Tests: `python3 -m pytest tests/legacy_equity scripts/migration/tests -q`

## Consume record 2026-08-16 (SMARTLIC-001)

| Field | Value |
|---|---|
| `origin/main` | `f0230b5a2fd7012e0071f5e4ff7ad973c9b8047a` (HEAD already based; no rebase) |
| Inventory source | GitHub raw `web-cfg@8a2f4d5b` — not the local `web-cfg` checkout (`3ae70c6b` / `feat/web-030-visible-parity`) |
| Inventory SHA-256 | `9e5667c127fc5494f5849aece2234b13a1c1db10257a17274545019634506ca9` |
| Config SHA-256 | `fd391e3667541953e6a830135c863f75452a27c879308fd0012d517740e537a4` (computed by `python3 -m bridge.generate`) |
| Execute set | 11 REDIRECT_301 + 54 HOLD fail-closed + default 410 |
| Payment-delay row | `/blog/orgaos-risco-atraso-pagamento-licitacao` → `/conteudos/atraso-pagamento-contrato-publico-suspender/` |
| Unittest | `python3 -m unittest discover -s bridge/tests -q` → 50 OK ×2 |
| Serve black-box | `python3 -m bridge.serve` ×2: 11×301 + 54×410 + `/` `/login` unmapped 410, identical hashes |
| Import audit | stdlib `bridge.serve` only; no FastAPI/Next/Redis/ARQ/Supabase/billing/auth/workers |
| Merge / DNS / TLS / issue close | **not performed** |

Residual human gates: WEB-017 / human accept of the 11-row set; merge of web-cfg#97; `$BRIDGE_PUBLIC_IPV4` + ACME email; DNS/TLS apply; live SmartLic 301/410; 28-day window; #2115 / #2111 / web-cfg#62 remain OPEN.
