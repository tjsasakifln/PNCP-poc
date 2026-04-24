# SEN-HOUSEKEEP-001: Sentry — Resolve issues stale (sem eventos há 7+ dias)

**Status:** Ready
**Origem:** PO Validation Report (2026-04-23) — spawn de SEN-FE-003/004/005/007 + fingerprints stale de SEN-FE-006
**Prioridade:** P3 — Baixo (housekeeping, não bloqueia roadmap)
**Complexidade:** XS (Extra Small) — <1h
**Owner:** @qa (via Sentry UI) ou @dev (via API)
**Tipo:** Housekeeping

---

## Problema

10 issues Sentry estão `unresolved` mas não recebem eventos há 7-17 dias. Alguns foram fixados por deploys colaterais (HOTFIX-001 fixou o `[mes]-[ano]` params). Outros param sem fix documentado.

Deixar "unresolved" polui dashboard e dificulta triagem de issues realmente live.

**Política:** se issue não recebe evento há 7+ dias em produção com tráfego estável, marcar `Resolved`. Se reaparecer em 14d, Sentry reabre automaticamente (fingerprint regression).

---

## Issues a resolver

| Sentry ID | Título | Last event | Fix attribution |
|-----------|--------|-----------|----------------|
| 7405579958 | InvariantError `/observatorio/[mes]-[ano]` | 2026-04-14 | HOTFIX-001 AC2 (Done 2026-04-13) |
| 7401546943 | slug conflict setor !== cnpj | 2026-04-10 | Unknown — likely deploy colateral |
| 7404786498 | EvalError unsafe-eval na home | 2026-04-11 | Unknown — likely 3rd-party retirado |
| 7374345723 | TypeError total_oportunidades undefined | 2026-04-10 | Unknown — likely null guard adicionado |
| 7397346898 | InvariantError RSC text/plain /login | 2026-04-08 | Unknown |
| 7387910087 | Error: Connection closed. (/) | 2026-04-06 | Browser lifecycle noise |
| 7389359900 | Error: Connection closed. | — | Browser lifecycle noise |
| 7389229679 | Error: Connection closed. | — | Browser lifecycle noise |
| 7408117240 | TypeError: terminated | 2026-04-13 | Browser lifecycle noise |
| 7406303366 | AbortError: signal is aborted without reason | 2026-04-13 | Browser lifecycle noise |

---

## Critérios de Aceite

- [ ] **AC1:** Para cada issue, verificar via Sentry API `GET /api/0/issues/{id}/` que `lastSeen` permanece >7d sem novos eventos
- [ ] **AC2:** Marcar `Resolved` via Sentry UI ou API `PUT /api/0/issues/{id}/ -d '{"status":"resolved"}'`
- [ ] **AC3:** Registrar a ação em `docs/sessions/2026-04/2026-04-23-sentry-housekeeping.md` com IDs + timestamp do resolve
- [ ] **AC4:** Se qualquer issue tiver evento nos últimos 72h antes de executar, NÃO resolver — criar story fix específica
- [ ] **AC5:** 14 dias pós-resolve: re-check. Se Sentry reabriu (evento novo), criar story fix e investigar regressão

### Anti-requisitos

- NÃO usar "Ignore" no Sentry — pode silenciar regressão permanentemente
- NÃO resolver issue que teve evento nas últimas 72h — risco de mascarar bug ativo

---

## Referência de implementação

```bash
TOKEN=$(grep SENTRY_AUTH_TOKEN .env | cut -d= -f2)
for ID in 7405579958 7401546943 7404786498 7374345723 7397346898 7387910087 7389359900 7389229679 7408117240 7406303366; do
  # Verify staleness
  curl -s -H "Authorization: Bearer $TOKEN" "https://sentry.io/api/0/issues/$ID/" | jq -r '.lastSeen'
  # Resolve
  curl -X PUT -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    "https://sentry.io/api/0/issues/$ID/" -d '{"status":"resolved"}'
done
```

---

## Riscos

- **R1 (Baixo):** Issue marcado resolved que na verdade volta a acontecer. **Mitigação:** Sentry reabre automaticamente em 14d se fingerprint exato volta

## Dependências

Nenhuma.

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-23 | @po | Story criada consolidando 4 NO-GO (SEN-FE-003/004/005/007) + 6 fingerprints stale. Status Ready direto (housekeeping trivial) |
