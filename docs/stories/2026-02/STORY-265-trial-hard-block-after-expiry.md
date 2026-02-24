# STORY-265 — Bloqueio Hard do Trial: Garantir Corte Total Após 7 Dias

**Status:** TODO
**Sprint:** GTM-TRIAL
**Priority:** P0 — Segurança/Revenue
**Estimate:** 5 SP
**Squad:** team-bidiq-backend + frontend

---

## Contexto

Com a STORY-264 liberando acesso completo durante o trial, é **crítico** garantir que o bloqueio após 7 dias seja absoluto e robusto. Hoje o bloqueio existe em `check_quota()` (quota.py:664-677), mas precisa ser auditado e reforçado em todos os pontos de acesso: busca, pipeline, Excel, resumos IA.

## Objetivo

Auditar e reforçar todos os pontos de controle para garantir que após 7 dias de trial, **nenhuma funcionalidade** esteja acessível sem plano pago.

## Acceptance Criteria

### Backend — Auditoria de Pontos de Bloqueio

- [ ] **AC1**: `POST /buscar` — Verificar que `check_quota()` é chamado ANTES de iniciar qualquer processamento; trial expirado retorna 403 com mensagem clara
- [ ] **AC2**: `POST /pipeline` — Verificar que trial expirado não pode adicionar itens ao pipeline
- [ ] **AC3**: `GET /pipeline` — Trial expirado pode VER o pipeline (read-only) mas não modificar (incentiva conversão mostrando o que já salvou)
- [ ] **AC4**: `POST /v1/download-excel` — Verificar que trial expirado não pode gerar Excel
- [ ] **AC5**: `POST /v1/first-analysis` — Trial expirado não pode iniciar análise
- [ ] **AC6**: `GET /sessions` — Trial expirado pode ver histórico (read-only, incentiva conversão)

### Backend — Middleware de Bloqueio

- [ ] **AC7**: Criar decorator `@require_active_plan` que encapsula a verificação de plan ativo (trial válido OU plano pago) para uso em endpoints que devem ser bloqueados
- [ ] **AC8**: Decorator retorna HTTP 403 com body: `{"error": "trial_expired", "message": "...", "upgrade_url": "/planos"}`
- [ ] **AC9**: Endpoints read-only (GET /pipeline, GET /sessions, GET /me) NÃO usam o decorator — permanecem acessíveis

### Backend — Expiração Precisa

- [ ] **AC10**: Constante `TRIAL_DURATION_DAYS` (de STORY-264) usada consistentemente em todo o backend
- [ ] **AC11**: `check_quota()` usa comparação timezone-aware (`datetime.now(timezone.utc)`) — auditar que não há comparação naive
- [ ] **AC12**: Logs estruturados quando trial é bloqueado: `logger.info("trial_blocked", user_id=..., expired_at=..., days_overdue=...)`

### Frontend — UX de Bloqueio

- [ ] **AC13**: Quando API retorna 403 com `error: "trial_expired"`, frontend mostra `TrialConversionScreen` automaticamente (não apenas um toast)
- [ ] **AC14**: Botão "Buscar" desabilitado visualmente quando trial expirado (com tooltip explicativo)
- [ ] **AC15**: Pipeline em modo read-only: drag-and-drop desabilitado, botão "Adicionar" desabilitado, banner no topo explicando
- [ ] **AC16**: Download Excel desabilitado com mensagem "Ative seu plano para exportar"

### Testes

- [ ] **AC17**: Teste de integração: criar usuário → simular 8 dias passados → verificar bloqueio em TODOS os endpoints mutáveis
- [ ] **AC18**: Teste que read-only endpoints (GET /pipeline, GET /sessions) continuam funcionando com trial expirado
- [ ] **AC19**: Teste que decorator `@require_active_plan` retorna 403 correto
- [ ] **AC20**: Teste frontend: mock API 403 trial_expired → TrialConversionScreen aparece
- [ ] **AC21**: Teste que plano pago NÃO é afetado pelo decorator (bypass correto)

---

## Notas Técnicas

- **Read-only como incentivo à conversão**: Usuário com trial expirado vê suas oportunidades salvas no pipeline e histórico de buscas — isso funciona como "sunk cost" que motiva upgrade
- **Não confundir com grace period**: Grace period (3 dias) existe apenas para planos pagos com subscription gap. Trial expirado = bloqueio imediato
- O decorator `@require_active_plan` é uma camada adicional sobre `check_quota()` — NÃO substitui, reforça
- Pipeline read-only requer verificação no frontend (backend já bloqueia POST/PATCH/DELETE via quota)

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `backend/quota.py` | Auditar check_quota(), criar require_active_plan decorator |
| `backend/routes/search.py` | Verificar chamada a check_quota |
| `backend/routes/pipeline.py` | Adicionar require_active_plan em POST/PATCH/DELETE |
| `backend/routes/sessions.py` | Verificar que GET permanece acessível |
| `backend/tests/test_trial_block.py` | NOVO — testes de bloqueio completo |
| `frontend/app/buscar/page.tsx` | Handler 403 trial_expired |
| `frontend/app/buscar/hooks/useSearch.ts` | Detectar 403 trial_expired |
| `frontend/app/pipeline/page.tsx` | Modo read-only |
| `frontend/__tests__/trial-block.test.tsx` | NOVO — testes de bloqueio frontend |
