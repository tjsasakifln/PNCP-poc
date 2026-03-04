# SHIP-006: Sentry Zero-Noise Baseline

**Status:** 🔴 Bloqueado
**Prioridade:** P1 (pós-deploy)
**Sprint:** SHIP (Go-to-Market)
**Criado:** 2026-03-03
**Depende de:** SHIP-001, SHIP-002, SHIP-003
**Tentativa de validação:** 2026-03-04

## Contexto

Após deploy de SHIP-001/002/003, verificar Sentry e resolver/arquivar TODOS os 24 issues
até chegar a **zero issues não resolvidos**. Isso cria uma baseline limpa para monitorar
erros reais de usuários pagantes — qualquer novo issue após baseline será um bug verdadeiro.

### 24 Issues Pré-Deploy (2026-03-03)

| ID | Issue | Cat | Esperado após deploy |
|----|-------|-----|---------------------|
| BACKEND-28 | ValidationError BuscaResponse | A | Resolved (CRIT-050) |
| BACKEND-29 | POST /v1/buscar ERROR | A | Resolved (CRIT-050) |
| BACKEND-26 | ConnectionError: Too many connections | C | Resolved (SHIP-003) |
| BACKEND-27 | conversations.first_response_at | B | Resolved (SHIP-002 gate) |
| BACKEND-25 | organization_members PGRST205 | B | Resolved (SHIP-002 gate) |
| BACKEND-24 | GET /v1/organizations/me ERROR | B | Resolved (SHIP-002 gate) |
| BACKEND-23 | Health incident status change | D | Resolved (SHIP-003) |
| BACKEND-20 | Failed to save health check | D | Resolved (SHIP-003) |
| BACKEND-12 | Incident detection failed | D | Resolved (SHIP-003) |
| BACKEND-22 | CircuitBreakerOpenError | D | Reduced (SHIP-003) |
| BACKEND-21 | Failed trial milestone | E | Resolved (SHIP-003) |
| BACKEND-1Y | PNCP API status=400 | F | Known, handled |
| BACKEND-1X | Failed trial email #7 | E | Resolved (SHIP-003) |
| BACKEND-1W | Failed trial email #4 | E | Resolved (SHIP-003) |
| BACKEND-1V | STARTUP GATE Supabase | D | Transient, archive |
| BACKEND-1T | RemoteProtocolError | D | Transient, archive |
| BACKEND-1S | HTTPException alertas | B | Resolved (SHIP-002 gate) |
| BACKEND-1R | Error listing alerts | B | Resolved (SHIP-002 gate) |
| BACKEND-1Q | Failed after 2 attempts | F | Known, archive |
| BACKEND-1P | PNCP API status=400 | F | Known, archive |
| FRONTEND-1 | failed to pipe response | G | Resolved (CRIT-052) |
| BACKEND-1K | ConnectionError PNCP | F | Known, archive |
| FRONTEND-4 | failed to pipe response | G | Resolved (CRIT-052) |
| BACKEND-1M | SSE generator abrupt finish | H | Resolved (CRIT-052) |

## Acceptance Criteria

### Verificação Pós-Deploy

- [ ] AC1: Esperar 30 minutos após deploy para estabilizar
- [ ] AC2: Abrir Sentry → Issues → Filter: `is:unresolved`
- [ ] AC3: Para cada issue da Categoria A (BuscaResponse): verificar que não reocorreu → Resolve
- [ ] AC4: Para cada issue da Categoria B (PGRST205/missing column): verificar resolved → Resolve
- [ ] AC5: Para cada issue da Categoria C (Redis pool): verificar resolved → Resolve
- [ ] AC6: Para cada issue da Categoria D (CB cascade): verificar reduced → Resolve ou Archive
- [ ] AC7: Para cada issue da Categoria E (trial emails): verificar resolved → Resolve
- [ ] AC8: Para cada issue da Categoria F (PNCP): Archive com nota "known external API behavior"
- [ ] AC9: Para cada issue da Categoria G (frontend pipe): verificar resolved → Resolve
- [ ] AC10: Para cada issue da Categoria H (SSE): verificar resolved → Resolve

### Baseline

- [ ] AC11: Sentry mostra **0 unresolved issues** ao final
- [ ] AC12: Screenshot da tela "0 issues" salvo como evidência
- [ ] AC13: Qualquer novo issue pós-baseline é tratado como bug real (não noise)

## Blocker

**Cannot proceed:** This story requires Sentry Dashboard access via auth token. The `sentry-cli` is installed but no `SENTRY_AUTH_TOKEN` or org/project config is available locally. Additionally, this story explicitly depends on SHIP-001/002/003 being deployed first.

**To unblock:**
1. Set `SENTRY_AUTH_TOKEN` in `.env` or configure `.sentryclirc`
2. Confirm SHIP-001/002/003 have been deployed
3. Wait 30 minutes post-deploy before validating

## Notas

- PNCP errors (F) são comportamento esperado da API externa — archive, não resolve
- Se algum issue da Cat A/B/C persistir, criar novo CRIT story para investigar
- CB issues (D) podem demorar para zerar se Supabase tiver instabilidade — OK arquivar
- Frontend Sentry config has `beforeSend` filter for SSE pipe errors (GTM-STAB-006 AC6)
