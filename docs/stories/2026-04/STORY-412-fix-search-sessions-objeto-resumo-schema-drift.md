# STORY-412: Fix Schema Drift em `search_sessions.objeto_resumo`

**Priority:** P0 — Production Incident (Escalating)
**Effort:** S (0.5-1 day)
**Squad:** @data-engineer + @dev
**Status:** InReview
**Epic:** [EPIC-INCIDENT-2026-04-10](EPIC-INCIDENT-2026-04-10.md)
**Sentry Issue:** https://confenge.sentry.io/issues/7396988861/
**Sprint:** Emergencial (0-48h)

---

## Contexto

`backend/routes/analytics.py:313-315` e `:344` fazem SELECT da coluna `search_sessions.objeto_resumo`, mas **nenhuma migration em `supabase/migrations/`** define essa coluna — ou ela foi removida fora de versionamento, ou nunca foi criada via migration oficial.

**Impacto atual (2026-04-10):**
- 213 eventos no Sentry, status **Escalating**
- 2 usuários afetados nas últimas 30 min (`39b32b6f-***`, `285edd6e-***`)
- Último evento há 5 min
- Erro retornado: `{'message': 'column search_sessions.objeto_resumo does not exist', 'code': '42703'}`
- Endpoint afetado: `GET /v1/analytics/trial-value` (bloqueia trial analytics)

**Query ofensora (`backend/routes/analytics.py:313-315`):**
```python
query = db.table("search_sessions").select(
    "total_filtered, valor_total, objeto_resumo, created_at"
).eq("user_id", user_id)
```

**Uso adicional:** `:344` chama `top_session.get("objeto_resumo")`.

Este bug é **intrinsecamente ligado à STORY-414** (Schema Contract Gate) — o contract gate falhou em detectar a drift. As duas stories devem coordenar.

---

## Acceptance Criteria

### AC1: Investigação da causa raiz
- [ ] Auditar `supabase/migrations/` via `grep -rn "objeto_resumo" supabase/` — confirmar que nenhuma migration a cria
- [ ] Auditar git history via `git log -p --all -S "objeto_resumo"` — descobrir quando referência foi adicionada no código
- [ ] Verificar schema atual do Supabase em produção via `supabase db pull` ou SQL direto no dashboard
- [ ] Documentar no Dev Notes abaixo qual foi a causa: (a) coluna nunca criada, (b) removida sem migration, (c) adicionada via UI Supabase e não sincronizada

### AC2: Decisão de fix — **OPÇÃO C SELECIONADA** ✅
- [x] **Decisão @pm 2026-04-10:** Opção C — remover campo `objeto_resumo` do SELECT e do payload
- [x] **Investigação prévia confirmou:**
  - `grep -rn "objeto_resumo" frontend/` → **0 matches** (frontend não consome)
  - `grep -rn "objeto_resumo" backend/` → usado apenas em `analytics.py:314, 344`
  - Fallback já existe: `top_session.get("objeto_resumo") or "Oportunidade identificada"` (linha 344)
  - Git log: campo adicionado em commit `c20da562 feat(trial): implement trial-to-paid conversion flow (GTM-010)` — coluna nunca foi criada via migration, drift puro desde o dia 1
- [x] Aplicar fix em `backend/routes/analytics.py`:
  - Linha 313-315: remover `objeto_resumo` do SELECT → `"total_filtered, valor_total, created_at"`
  - Linha 344: trocar `top_session.get("objeto_resumo") or "Oportunidade identificada"` por `"Oportunidade identificada"` direto
- [ ] ~~**Opção A:** Criar migration `ALTER TABLE ... ADD COLUMN`~~ — **REJEITADA** (campo não usado no frontend)
- [ ] ~~**Opção B:** Alterar query para `search_params->>'objeto'`~~ — **REJEITADA** (complexidade desnecessária para campo descartável)

### AC3: Aplicar fix
- [x] Código ou migration aplicada via `supabase db push` (se for migration)
- [ ] Validação em staging primeiro: `railway logs --service smartlic-backend-staging --filter "42703"` deve retornar 0 após 10 min de tráfego
- [ ] Deploy para produção via hotfix (pode ser direto em `main` dado o P0)

### AC4: Testes de regressão
- [x] `backend/tests/test_trial_endpoints.py` — verificar se há teste cobrindo `get_trial_value` com campo `objeto_resumo`. Se não houver, adicionar.
- [x] Se houver teste falhando: **bloquear merge** até passar — 9 testes passando
- [x] Novo teste: mockar Supabase retornando dados sem `objeto_resumo` e validar fallback gracioso

### AC5: Atualizar Schema Contract
- [x] **Opção C selecionada:** garantir que `CRITICAL_SCHEMA["search_sessions"]` em `backend/schemas/contract.py:35-75` **NÃO** lista `objeto_resumo` (remover se estiver listada)

### AC6: Verificação pós-deploy
- [ ] Monitorar Sentry issue 7396988861 por 6h — deve ficar em 0 eventos novos
- [ ] Dashboard Grafana/Prometheus: endpoint `/v1/analytics/trial-value` com error rate <0.1%
- [ ] Marcar issue 7396988861 como **Resolved** no Sentry

---

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `backend/routes/analytics.py` | Linhas 313-315 e 344 — ajustar query conforme decisão AC2 |
| `supabase/migrations/2026041000_restore_objeto_resumo_search_sessions.sql` | (Opção A) Nova migration criando coluna |
| `backend/schemas/contract.py` | Linhas 35-75 — atualizar `CRITICAL_SCHEMA["search_sessions"]` |
| `backend/tests/test_trial_endpoints.py` | Novo teste de regressão cobrindo campo ausente |
| `frontend/app/**` | Apenas se Opção C — remover consumo do campo se existir |

---

## Implementation Notes

- **Dependência implícita:** Se a coluna foi dropada como parte de uma migration de limpeza recente, isso sugere que a query em `analytics.py` está desatualizada. Preferir Opção B ou C nesse caso.
- **Se Opção A (recriar):** usar `TEXT NULL` (não `NOT NULL`) para não quebrar rows existentes. Backfill pode ser derivado de `search_params->>'objeto'` se a rota aceita esse campo.
- **Alternativa de long-term:** considerar usar `search_params` JSONB em vez de colunas planas para metadados de busca — evita migrations futuras.
- **Timing do deploy:** como é P0 ativamente escalando, pode fazer hotfix direto para `main` e skip da aprovação de sprint normal. Usar `fix/` branch e PR rápido com @architect review.

---

## Dev Notes (preencher durante implementação)

**Causa raiz (investigação @pm 2026-04-10):**
- Campo `objeto_resumo` foi introduzido no commit `c20da562 feat(trial): implement trial-to-paid conversion flow (GTM-010)` como parte do query de analytics
- **Nenhuma migration foi criada** para adicionar a coluna em `search_sessions` — drift puro do code vs schema
- Causa = opção (a) coluna nunca criada via migration — classic schema drift from code-first assumption
- Ver STORY-414 para fix do contract gate que deveria ter detectado isso

**Decisão selecionada: Opção C (@pm 2026-04-10)**
- Investigação mostrou zero uso no frontend
- Fallback `"Oportunidade identificada"` já existe em `analytics.py:344`
- Remover campo é mais simples, seguro e alinha com principle "don't add features that weren't requested"

<!-- @dev: preencher resto conforme implementar -->

---

## Verification

1. **Local:** reproduzir erro rodando `uvicorn backend.main:app` apontando para staging e chamando `curl http://localhost:8000/v1/analytics/trial-value` com JWT válido
2. **Staging:** após deploy, chamar endpoint 20x e verificar logs `railway logs --filter "42703"` = vazio
3. **Produção:** monitorar Sentry issue 7396988861 por 6h
4. **Schema contract:** `curl $PROD_URL/admin/schema-contract-status` (criado em STORY-414) deve retornar `passed: true`

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-10 | @sm (River) | Story criada a partir do incidente multi-causa |
| 2026-04-10 | @po (Sarah) | `*validate-story-draft` → verdict GO (9.5/10). Status Draft → Ready. |
| 2026-04-10 | @pm (Morgan) | Decisão AC2: **Opção C** (remover campo). Investigação confirmou zero uso no frontend e fallback já existente em `analytics.py:344`. AC4 ajustado — teste de regressão cobre `top_opportunity.title` com fallback literal. |
| 2026-04-10 | @dev | Implementation. `backend/routes/analytics.py:313-315` — SELECT sem `objeto_resumo`. Linha 344 — título literal `"Oportunidade identificada"`. `backend/tests/test_trial_endpoints.py` atualizado (9 passam) + novo teste de regressão que inspeciona `.select(...)` call_args para garantir que `objeto_resumo` nunca mais entra na query. Status Ready → InReview. |
