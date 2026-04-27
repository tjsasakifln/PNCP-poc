# RES-BE-002: Hotfix Budget Temporal nas Top-5 Rotas por Tráfego

**Priority:** P0
**Effort:** M (3 dias)
**Squad:** @dev + @architect
**Status:** Ready
**Epic:** [EPIC-RES-BE-2026-Q2](EPIC-RES-BE-2026-Q2.md)
**Sprint:** Sprint 1 (2026-04-29 → 2026-05-05) — bloqueador de SEO-PROG-001..005 (rotas SSR→ISR exigem backend protegido)
**Dependências bloqueadoras:** [RES-BE-001](RES-BE-001-audit-execute-without-budget.md) (gate CI deve estar ativo para validar não-regressão)

---

## Contexto

A wave Googlebot de 2026-04-27 saturou o backend porque ~80% dos requests caíram em 5 rotas que faziam `.execute()` Supabase síncronos sem budget temporal. Hotfix PR #529 cobriu apenas `routes/empresa_publica.py:169` e `routes/contratos_publicos.py:450` — restam **32 callsites** nas top-5 rotas por tráfego previsto na próxima wave (estimado via análise de `sitemap.ts` + paths indexáveis):

| Rota | Callsites `.execute()` desprotegidos | Tráfego previsto |
|---|---|---|
| `backend/routes/mfa.py` | 10 | Auth flow (alta freq) |
| `backend/routes/referral.py` | 7 | Magnet SEO (Googlebot crawl) |
| `backend/routes/founding.py` | 4 | Marketing landing |
| `backend/routes/conta.py` | 4 | User dashboard (logged-in) |
| `backend/routes/sitemap_licitacoes.py` (+ outros sitemap) | 7 (total) | **Crítico** — Googlebot ataca sitemap primeiro |

Sem essa correção, **a janela de 7-14 dias antes da próxima onda Googlebot fecha** e o sistema reincide o P0. A correção é cirúrgica: wrappar cada `.execute()` em `_run_with_budget(..., budget=3.0, phase="route", source=route_name)` ou `asyncio.wait_for(coro, timeout=3.0)`. Padrão referência: `backend/pipeline/budget.py:28-93`.

Feature flag `ENABLE_BUDGET_WRAP=true` (default true em prod) permite rollback rápido se latência regredir 2x baseline.

---

## Acceptance Criteria

### AC1: Wrap `.execute()` em `routes/mfa.py` (10 callsites)

- [ ] Identificar 10 callsites via `backend/scripts/audit_execute_without_budget.py --output-md`
- [ ] Para cada callsite, aplicar pattern:
  ```python
  from pipeline.budget import _run_with_budget

  result = await _run_with_budget(
      asyncio.to_thread(lambda: supabase.from_("mfa_factors").select("*").eq("user_id", uid).execute()),
      budget=3.0,
      phase="route",
      source="mfa.list_factors",
  )
  ```
- [ ] Notar que `.execute()` Supabase Python SDK é **síncrono** — embrulhar em `asyncio.to_thread` dentro do `_run_with_budget` (Constitution: nunca bloquear event loop)
- [ ] Cada wrap recebe `source` único identificando rota+ação (e.g. `mfa.list_factors`, `mfa.enroll_factor`, `mfa.verify_challenge`)
- [ ] Lint clean (ruff + mypy) e testes existentes de `mfa.py` continuam passando

### AC2: Wrap `.execute()` em `routes/referral.py` (7), `founding.py` (4), `conta.py` (4)

- [ ] Mesma transformação aplicada nos 15 callsites combinados
- [ ] `source` labels:
  - referral: `referral.create_code`, `referral.list_invites`, `referral.redeem_code`, `referral.get_user_referral`, `referral.update_status`, `referral.delete`, `referral.stats`
  - founding: `founding.list_signups`, `founding.create_signup`, `founding.update_signup`, `founding.get_metrics`
  - conta: `conta.update_profile`, `conta.delete_account`, `conta.get_settings`, `conta.update_billing_email`
- [ ] (Ajustar nomes conforme funções reais; usar nome de função quando aplicável)

### AC3: Wrap `.execute()` em rotas `sitemap_*.py` (7 callsites — crítico Googlebot)

- [ ] Identificar arquivos `backend/routes/sitemap_*.py` com `.execute()` desprotegido (estimativa: `sitemap_licitacoes.py`, `sitemap_orgaos.py`, `sitemap_cnpj.py`, etc.)
- [ ] Wrap cada callsite com `budget=5.0` (sitemap pode tolerar latência maior, mas não infinita)
- [ ] Testar com payload realista (e.g. 1000 IDs) que budget é suficiente em ambiente normal
- [ ] **Adicionar negative cache** (ver RES-BE-003 — coordenar entrega; aqui apenas TODO se RES-BE-003 não tiver mergeado ainda)

### AC4: Feature flag `ENABLE_BUDGET_WRAP`

- [ ] Em `backend/config.py`, adicionar:
  ```python
  ENABLE_BUDGET_WRAP: bool = os.getenv("ENABLE_BUDGET_WRAP", "true").lower() == "true"
  ```
- [ ] Helper em `backend/pipeline/budget.py`:
  ```python
  async def _maybe_wrap(coro, *, budget, phase, source):
      if config.ENABLE_BUDGET_WRAP:
          return await _run_with_budget(coro, budget=budget, phase=phase, source=source)
      return await coro
  ```
- [ ] Todos os 25 wraps das ACs 1-3 usam `_maybe_wrap` em vez de `_run_with_budget` direto (rollback flag-driven)
- [ ] Default `true` em produção (`railway variables --service bidiq-backend --set ENABLE_BUDGET_WRAP=true`)
- [ ] Documentar no `CLAUDE.md` seção "Critical Implementation Notes" como toggle de emergência

### AC5: Métrica Prometheus + Sentry

- [ ] Counter já existente `smartlic_pipeline_budget_exceeded_total{phase,source}` é incrementado quando budget estoura (já implementado em `_record_exceeded`)
- [ ] Adicionar Sentry `capture_message(level="warning")` no `_record_exceeded` quando `phase="route"` (rotas HTTP — sinal mais crítico que pipeline)
- [ ] Fingerprint `["route_budget_exceeded", source]` — dedup por rota
- [ ] Tag `source=<source_label>` permite filtro por rota no Sentry

### AC6: Testes timeout invariant

- [ ] Criar `backend/tests/test_route_timeout_invariants.py`:
  ```python
  @pytest.mark.asyncio
  @pytest.mark.timeout(10)
  async def test_mfa_list_factors_respects_budget(monkeypatch):
      """Slow Supabase client → request returns 504 within 3.5s, not Railway 120s wedge."""
      async def slow_execute(*args, **kwargs):
          await asyncio.sleep(5)  # > budget=3
      monkeypatch.setattr(...)
      # ...assert TimeoutError raised, counter incremented
  ```
- [ ] 5+ testes cobrindo: top route per módulo (mfa, referral, founding, conta, sitemap)
- [ ] Test garante counter `smartlic_pipeline_budget_exceeded_total{phase="route"}` incrementa
- [ ] Test garante feature flag `ENABLE_BUDGET_WRAP=false` desabilita wrap (resultado = await direto)

### AC7: Validação não-regressão via gate RES-BE-001

- [ ] Após implementação, rodar `python backend/scripts/audit_execute_without_budget.py --output-md` e confirmar que count desprotegido caiu de 54 → ~29 (54 - 25)
- [ ] Atualizar `backend/scripts/audit-baseline.json` na mesma PR (`--update-baseline`)
- [ ] Atualizar `docs/audit/execute-without-budget-{date}.md` com novo snapshot
- [ ] CI gate (RES-BE-001) deve passar verde no PR

### AC8: Smoke test sintético

- [ ] Criar `backend/tests/integration/test_route_smoke_budget.py` que:
  - Inicia FastAPI test client
  - Mocka Supabase client com `time.sleep(5)` em `.execute()`
  - Hit em `/api/mfa/list-factors` deve retornar erro estruturado (504 ou 503) em <4s, não wedge
- [ ] Mesmo teste para 1 rota de cada módulo afetado (5 testes)

---

## Scope

**IN:**
- Wrap de 25 callsites em mfa, referral, founding, conta, sitemap_*
- Feature flag `ENABLE_BUDGET_WRAP` em `config.py`
- Helper `_maybe_wrap` em `budget.py`
- Sentry warning em `_record_exceeded` para `phase="route"`
- Testes timeout invariant + smoke
- Atualização baseline RES-BE-001 + relatório

**OUT:**
- Wrap dos outros ~29 callsites residuais (escopo Sprint 2 — pode virar story RES-BE-002b ou ser absorvido por RES-BE-003)
- Negative cache (RES-BE-003)
- Bulkhead (RES-BE-010)
- Circuit breaker (RES-BE-012)

---

## Definition of Done

- [ ] 25 callsites wrappados com `_maybe_wrap`
- [ ] Feature flag `ENABLE_BUDGET_WRAP` documentada em CLAUDE.md
- [ ] `audit-baseline.json` atualizado, gate CI verde
- [ ] Cobertura testes ≥85% nas linhas tocadas (medir via `pytest --cov=backend/routes/mfa,backend/routes/referral,backend/routes/founding,backend/routes/conta,backend/routes/sitemap_licitacoes`)
- [ ] Sem regressão em testes existentes (5131+ passing, 0 failures)
- [ ] Suite tempo total CI <8min mantido
- [ ] Sentry capture configurado e validado em staging (warning visível)
- [ ] CodeRabbit review clean (CRITICAL=0, HIGH=0)
- [ ] PR review por @architect (Aria) + @qa (Quinn) com verdict PASS
- [ ] Deploy staging passa smoke test sintético sem wedge
- [ ] Rollback runbook validado (toggle flag → request volta ao comportamento pre-wrap em <2min)

---

## Dev Notes

### Paths absolutos

- `/mnt/d/pncp-poc/backend/routes/mfa.py` — 10 callsites a wrappar
- `/mnt/d/pncp-poc/backend/routes/referral.py` — 7 callsites
- `/mnt/d/pncp-poc/backend/routes/founding.py` — 4 callsites
- `/mnt/d/pncp-poc/backend/routes/conta.py` — 4 callsites
- `/mnt/d/pncp-poc/backend/routes/sitemap_licitacoes.py` (e siblings) — 7 callsites (total)
- `/mnt/d/pncp-poc/backend/pipeline/budget.py` — adicionar `_maybe_wrap`
- `/mnt/d/pncp-poc/backend/config.py` — adicionar flag
- `/mnt/d/pncp-poc/backend/tests/test_route_timeout_invariants.py` (novo)
- `/mnt/d/pncp-poc/backend/tests/integration/test_route_smoke_budget.py` (novo)

### Padrão de wrap canônico

```python
import asyncio
from pipeline.budget import _maybe_wrap

# Antes (vulnerável):
result = supabase.from_("mfa_factors").select("*").eq("user_id", uid).execute()

# Depois (protegido):
result = await _maybe_wrap(
    asyncio.to_thread(
        lambda: supabase.from_("mfa_factors")
        .select("*")
        .eq("user_id", uid)
        .execute()
    ),
    budget=3.0,
    phase="route",
    source="mfa.list_factors",
)
```

**Atenção:** Supabase Python SDK 2.x é síncrono — `to_thread` é mandatório, senão wrap não tem efeito.

### Budgets por rota

| Rota | Budget | Justificativa |
|---|---|---|
| mfa.* | 3.0s | Auth path, latência baixa esperada |
| referral.* | 3.0s | Lookups simples |
| founding.* | 3.0s | Lookups + insert simples |
| conta.* | 3.0s | User-facing dashboard |
| sitemap_* | 5.0s | Queries agregadas, mas não devem exceder |

Se algum endpoint genuinamente precisa >5s, levantar com @architect — provavelmente sinal de query mal otimizada (deferir para RES-BE-009 triage).

### Frameworks de teste

- pytest 8.x + pytest-asyncio
- File location: `backend/tests/test_route_timeout_invariants.py`, `backend/tests/integration/test_route_smoke_budget.py`
- Marks: `@pytest.mark.timeout(10)` (estes testes simulam slowness, precisam folga)
- Fixtures: usar `monkeypatch` para mockar Supabase client (não criar fixture global; isolado por teste)
- Auth: `app.dependency_overrides[require_auth]` para bypass (padrão CLAUDE.md)

### Convenções

- Não alterar response model das rotas (apenas wrap interno)
- Logger usa `logger.warning(...)` em path de timeout — Sentry captura via integração existente
- Type hints obrigatórios

---

## Risk & Rollback

| Trigger | Ação |
|---|---|
| p99 latency rotas afetadas > 2x baseline pós-deploy | `railway variables --service bidiq-backend --set ENABLE_BUDGET_WRAP=false`; rollback effective em ~30s |
| Counter `smartlic_pipeline_budget_exceeded_total{phase="route"}` >0.5/min sustained | Identificar source via label, ajustar budget para 5s ou 7s para essa rota específica |
| Wrap quebra teste existente (false positive em mock) | Ajustar mock conforme padrões CLAUDE.md `app.dependency_overrides[require_auth]` |
| Sentry flood (>100 events/min) | Aumentar fingerprint dedup ou subir threshold; não desabilitar wrap |
| Supabase client async wrapper (futuro upgrade SDK 3.x) torna `to_thread` desnecessário | Refator coordenado: substituir `asyncio.to_thread(lambda: ...)` por await direto; gate RES-BE-001 não detecta diferença |

**Rollback completo:** revert PR. Feature flag permite rollback parcial sem revert.

---

## Dependencies

**Entrada:**
- [RES-BE-001](RES-BE-001-audit-execute-without-budget.md) — gate CI deve estar ativo
- `backend/pipeline/budget.py::_run_with_budget` (existente)

**Saída (esta story bloqueia):**
- [RES-BE-003](RES-BE-003-negative-cache-failure-paths.md) — negative cache aplicado nas mesmas rotas
- [RES-BE-010](RES-BE-010-bulkheads-critical-routes.md) — bulkheads complementam budgets
- [RES-BE-012](RES-BE-012-circuit-breaker-supabase.md) — breaker downstream do budget
- **EPIC-SEO-PROG-2026-Q2** stories SEO-PROG-001..005 (cnpj, orgaos, itens, observatorio, fornecedores) exigem backend protegido em staging

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | ✓/✗ | Notes |
|---|---|---|---|
| 1 | Clear and objective title | ✓ | "Hotfix Budget Temporal nas Top-5 Rotas por Tráfego" — escopo claro e cirúrgico. |
| 2 | Complete description | ✓ | Conecta wave Googlebot 2026-04-27 → 80% requests em 5 rotas → 32 callsites; tabela quantitativa. |
| 3 | Testable acceptance criteria | ✓ | 8 ACs testáveis; AC6 fornece pseudocódigo de teste; AC8 smoke test sintético. |
| 4 | Well-defined scope | ✓ | IN/OUT explícitos; OUT delimita 29 callsites residuais (defer Sprint 2). |
| 5 | Dependencies mapped | ✓ | Entrada RES-BE-001 (gate CI); saída RES-BE-003, 010, 012 + bloqueia EPIC-SEO-PROG. |
| 6 | Complexity estimate | ✓ | M (3 dias) realista para 25 callsites + flag + tests + smoke. |
| 7 | Business value | ✓ | "Janela 7-14 dias antes próxima onda Googlebot fecha" — urgência traduzida em prazo. |
| 8 | Risks documented | ✓ | 5 cenários incluindo Supabase SDK 3.x async upgrade (forward-looking); rollback via feature flag <30s. |
| 9 | Criteria of Done | ✓ | 10 itens incluindo rollback runbook validado em <2min — pragmático. |
| 10 | Alignment with PRD/Epic | ✓ | Métrica #1 EPIC ("smartlic_route_timeout_total = 0 sob 5x carga") testada por AC6. |

### Required Fixes

Nenhuma — story pronta para implementação.

### Observations

- AC2 lista nomes de funções "(Ajustar nomes conforme funções reais; usar nome de função quando aplicável)" — flexibilidade adequada para @dev refinar.
- Tabela de budgets por rota (mfa=3s, sitemap=5s) calibrada com base empírica.
- Padrão `_maybe_wrap` cria abstração reutilizável — bom design, não over-engineering.
- Atenção do @dev: confirmar Supabase SDK Python 2.x ainda síncrono no momento da implementação; AC2 wraps via `asyncio.to_thread` dependem disso.

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — top-5 rotas anti-reincidência P0 | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). Hotfix Sprint 1 cirúrgico, feature flag de rollback. Status: Draft → Ready. | @po (Pax) |
