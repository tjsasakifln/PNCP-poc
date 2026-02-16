# STORY-TD-004: Seguranca Restante e Documentacao DB

## Epic
Epic: Resolucao de Debito Tecnico v2.0 -- SmartLic/BidIQ (EPIC-TD-v2)

## Sprint
Sprint 1: Seguranca e Correcoes

## Prioridade
P1

## Estimativa
4h

## Descricao

Esta story fecha os gaps de seguranca de banco de dados restantes apos o Sprint 0 e documenta decisoes baseadas nos resultados das queries de verificacao V1-V5.

1. **Webhook INSERT policy (DB-05, MEDIUM, 1h)** -- `stripe_webhook_events` tem INSERT policy que nao limita a `service_role`. Qualquer usuario autenticado pode inserir eventos fake. Embora mitigado parcialmente pelo CHECK `'^evt_'` e `GRANT INSERT TO service_role`, a policy deve ser scoped corretamente. Migration 028.

2. **Admin.py default fix (DB-15, MEDIUM, 0.5h)** -- Se nao corrigido atomicamente na TD-001, corrigir `admin.py` `CreateUserRequest` default de `"free"` para `"free_trial"`. Dependente do resultado de TD-001.

3. **Documentacao/remocao de trigger DB-01 (MEDIUM, 2h)** -- Baseado no resultado das queries V1-V5: se coluna `status` NAO existe em `user_subscriptions`, o trigger `sync_profile_plan_type()` (migration 017) e dead code e deve ser removido com documentacao. Se existe, documentar o fluxo e garantir consistencia.

4. **DB-11: Consolidacao de `handle_new_user()` trigger (0.5h documentacao)** -- O trigger foi redefinido 4 vezes (migrations 001, 007, 016, 024). Documentar a evolucao e confirmar que versao 027 (da TD-001) e a versao canonica. Consolidacao completa sera feita quando trigger estabilizar.

## Itens de Debito Relacionados
- DB-05 (MEDIUM): `stripe_webhook_events` INSERT policy scope to service_role
- DB-15 (MEDIUM): admin.py CreateUserRequest default "free" -> "free_trial"
- DB-01 (MEDIUM): Missing `status` column em `user_subscriptions` -- trigger potencialmente dead code
- DB-11 (MEDIUM): `handle_new_user()` trigger redefinido 4 vezes -- documentar evolucao

## Criterios de Aceite

### Webhook Security (Migration 028)
- [x] INSERT em `stripe_webhook_events` com authenticated key FALHA (somente service_role pode inserir)
- [x] SELECT policy para authenticated permanece funcional (se existente)
- [ ] Stripe webhooks continuam processando normalmente apos correcao *(requires production deploy)*

### Admin Default
- [x] `admin.py` `CreateUserRequest` tem `plan_id` default como `"free_trial"` (nao `"free"`)
- [x] Admin cria usuario sem plan_id explicito -> profile com `plan_type = 'free_trial'`

### Trigger Documentacao
- [x] Resultado de V1 (coluna `status`) documentado — **COLUNA NAO EXISTE** (dead code confirmado)
- [x] Se `status` ausente: trigger `sync_profile_plan_type()` marcado como dead code com justificativa
- [ ] ~~Se `status` presente: fluxo documentado e consistencia verificada~~ N/A (status ausente)
- [x] Evolucao do trigger `handle_new_user()` documentada (5 versoes: 001, 007, 016, 024, 027)

## Testes Requeridos

| ID | Teste | Tipo | Prioridade |
|----|-------|------|-----------|
| SEC-T04 | INSERT em `stripe_webhook_events` com authenticated key FALHA | Integracao SQL | P1 |
| SEC-T05 | INSERT com `id` nao-`'^evt_'` FALHA por CHECK | Unitario | P1 |
| REG-T03 | Admin cria usuario sem erro de constraint | Integracao | P1 |

## Dependencias
- **Blocks:** STORY-TD-019 (backlog DB items)
- **Blocked by:** STORY-TD-001 (resultado das queries V1-V5 e estado pos-migration 027)

## Riscos
- **CR-06:** Consolidacao de trigger (DB-11) pode conflitar com extensoes. Fazer APOS signup validado.
- Risco de bloqueio funcional se webhook INSERT policy for muito restritiva -- testar processamento Stripe apos fix.

## Rollback Plan
- Migration 028 pode ser revertida independentemente de 027
- Se webhook processing falhar, restaurar policy original rapidamente

## Definition of Done
- [x] Codigo implementado e revisado
- [x] Testes passando (unitario + integracao SQL) — 36/36 passing (29 SEC + 7 REG)
- [ ] CI/CD green *(pending push)*
- [x] Documentacao atualizada (triggers, evolucao, decisoes) — 3 docs created
- [ ] Deploy em staging verificado *(requires migration 027 first — TD-001 dependency)*
- [ ] Webhook Stripe testado em producao apos deploy *(requires production deploy)*

## Artifacts Produced
- `backend/tests/test_webhook_rls_security.py` — 29 tests (SEC-T04, SEC-T05)
- `backend/tests/test_admin_default.py` — 7 tests (REG-T03)
- `docs/architecture/td004-trigger-evolution.md` — Trigger archaeology (DB-01, DB-11)
- `docs/architecture/ADR-TD004-webhook-rls-security.md` — ADR for webhook RLS
- `docs/architecture/ADR-TD004-trigger-consolidation.md` — ADR for trigger strategy
