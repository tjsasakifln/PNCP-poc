# Redirect bridge (SmartLic#2115)

Isolated surface. Executes only the hash-pinned execute set from [web-cfg#62](https://github.com/tjsasakifln/web-cfg/issues/62) / [PR #68](https://github.com/tjsasakifln/web-cfg/pull/68).

| Pin | Value |
|---|---|
| Manifesto SHA-256 | `c2cee8362321099205b76b11f89485d4248a00b8abbbda354d15964f6b316e0d` |
| web-cfg commit | `3f112bfbd9e6b042691e1c09812af00f42735adb` |
| Rules | 11 URL-specific 301s + default 410 |
| Owner | SmartLic#2115 |
| Cost | UNKNOWN |
| Expiry | 28 days after the first production 301 of this hash |
| Removal trigger | window complete + zero residual priority errors + #2111 archive gate |
| Live DNS/TLS cutover | **CUTOVER_READY** (see `docs/CUTOVER.md`; owner applies DNS/ACME) |

```text
python3 -m bridge.generate
python3 -m unittest discover -s bridge/tests -v
python3 -m bridge.serve --host 127.0.0.1 --port 8765
```

Docs: `docs/CUTOVER.md`, `docs/RUNBOOK.md`, `docs/ROLLBACK.md`, `docs/OBSERVABILITY.md`.
