# Redirect bridge (SmartLic#2115)

Isolated surface. Executes only the hash-pinned execute set from [web-cfg#62](https://github.com/tjsasakifln/web-cfg/issues/62).

| Pin | Value |
|---|---|
| Manifesto SHA-256 | `3c5a5b7aeb173a16cfb65c0314827d9022ba1b387901d1718e4fdfcbd0363023` |
| web-cfg commit (map pin) | `78b7ebb9f8c26b754e5571248d014be305fbcf40` |
| web-cfg counterpart | **OPEN** `feat/smartlic-equity-migration-62` |
| Supersedes | `c2cee8362321099205b76b11f89485d4248a00b8abbbda354d15964f6b316e0d` (same 11 ready 301s) |
| Rules | 11 URL-specific 301s + 54 HOLD fail-closed + default 410 |
| Owner | SmartLic#2115 |
| Cost | UNKNOWN |
| Expiry | 28 days after the first production 301 of this hash |
| Removal trigger | window complete + zero residual priority errors + #2111 archive gate |
| Live DNS/TLS cutover | engineering **CUTOVER_READY**; live apply **BLOCKED** (`docs/CUTOVER_READINESS.md`) |

```text
python3 -m bridge.generate
python3 -m unittest discover -s bridge/tests -v
python3 -m bridge.serve --host 127.0.0.1 --port 8765
```

Docs: `docs/CUTOVER.md`, `docs/RUNBOOK.md`, `docs/ROLLBACK.md`, `docs/OBSERVABILITY.md`.
