# SHIP-002: Feature-Gate Features Incompletas

**Status:** 🟢 Concluído
**Prioridade:** P0
**Sprint:** SHIP (Go-to-Market)
**Criado:** 2026-03-03
**Bloqueia:** SHIP-001

## Contexto

4 features incompletas (organizations, messages, alerts, partners) geram erros no Sentry
sem dar NENHUM valor ao usuário. Não têm frontend. Não têm testes de integração.
São 1.500+ linhas de código de rotas que causam PGRST205, APIError, e HTTPException
toda vez que cron jobs ou health checks tentam acessá-las.

### Sentry Issues Resolvidos por Esta Story

- BACKEND-27: `column conversations.first_response_at does not exist`
- BACKEND-25: `Could not find table 'public.organization_members'` (PGRST205)
- BACKEND-24: `GET /v1/organizations/me -> ERROR`
- BACKEND-1S: `HTTPException: Erro ao listar alertas`
- BACKEND-1R: `Error listing alerts for user`

## Acceptance Criteria

- [x] AC1: `config.py` — adicionar flags: `ORGANIZATIONS_ENABLED = bool(os.getenv("ORGANIZATIONS_ENABLED", "false").lower() == "true")`
- [x] AC2: `config.py` — adicionar flags: `MESSAGES_ENABLED`, `ALERTS_SYSTEM_ENABLED`, `PARTNERS_ENABLED` (todas `False` por padrão)
- [x] AC3: `routes/organizations.py` — early return 404 `{"detail": "Feature not available"}` quando `ORGANIZATIONS_ENABLED=False`
- [x] AC4: `routes/messages.py` — early return 404 quando `MESSAGES_ENABLED=False`
- [x] AC5: `routes/alerts.py` — early return 404 quando `ALERTS_SYSTEM_ENABLED=False`
- [x] AC6: `routes/partners.py` — early return 404 quando `PARTNERS_ENABLED=False`
- [x] AC7: `cron_jobs.py` — SLA check (`start_trial_sequence_task` e qualquer job que query `conversations.first_response_at`) faz early-return quando flag=False
- [x] AC8: `cron_jobs.py` — alert_runs job faz early-return quando `ALERTS_SYSTEM_ENABLED=False`
- [x] AC9: Frontend — remover/ocultar links para mensagens, alertas, organizações nos menus de navegação (se existirem)
- [x] AC10: Testes existentes continuam passando (flags não quebram nada)

## Implementação

Padrão simples por rota — NÃO deletar código, apenas guardar com flag:

```python
# No topo de cada router file:
from config import ORGANIZATIONS_ENABLED

@router.get("/organizations/me")
async def get_my_org(...):
    if not ORGANIZATIONS_ENABLED:
        raise HTTPException(status_code=404, detail="Feature not available")
    # ... código existente
```

## Notas

- NÃO deletar código. Apenas feature-gate.
- NÃO remover migrations. Elas são idempotentes e não fazem mal aplicadas.
- Quando tivermos clientes pedindo essas features, basta setar a env var para "true".
