# Runtime mínimo Netcup — #2115

Topologia alvo:

```text
Caddy (TLS)
  → Next.js :3000   KEEP
  → FastAPI :8000   TEMPORARY adapter
      → extra-cli public_read_v1 (SELECT-only)  REPLACE do DataLake SmartLic
```

| Componente | Destino | Motivo |
|---|---|---|
| Next.js | KEEP | Superfície pública e patrimônio SEO |
| FastAPI | TEMPORARY | Adapter de apresentação até o cutover |
| Redis | TEMPORARY | Cache/rate-limit na transição |
| ARQ / workers | REMOVE after dependency | Ingestão e billing saem |
| Supabase | TEMPORARY store | Não é autoridade |
| Stripe | REMOVE after zero-use | #2111 |
| Railway | REMOVE | Produção atual responde `x-railway-fallback: true` (404) |

Scripts em `deploy/netcup/` são executáveis. Sem acesso SSH neste ciclo, o runbook é o artefato.

## Boot

1. `sudo ./deploy/netcup/install.sh`
2. Preencher `/etc/smartlic/smartlic.env` a partir do example.
3. Publicar release em `/opt/smartlic/releases/<sha>` e apontar `current`.
4. `systemctl enable --now caddy smartlic-adapter smartlic-web`
5. `./deploy/netcup/validate-env.sh && ./deploy/netcup/healthcheck.sh`

Rollback: `./deploy/netcup/rollback.sh <sha>`.

Backup: somente estado SmartLic (`/var/lib/smartlic/lead-outbox.jsonl` e env). Nunca dump do extra-cli.
