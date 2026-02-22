# CRIT-016 — Production Code Bugs (4 bugs do Sentry)

**Status:** completed
**Priority:** P2 — Production (24 eventos combinados, buscas falhando)
**Origem:** Análise Sentry (2026-02-21) — SMARTLIC-BACKEND-E, N, A + SMARTLIC-FRONTEND-2
**Componentes:** backend/consolidation.py, backend/search_pipeline.py, frontend/app/buscar/components/

---

## Contexto

4 bugs distintos identificados no Sentry, todos afetando a funcionalidade de busca em produção. Individualmente têm poucos eventos, mas juntos representam falhas que degradam a experiência do usuário.

---

## Bug 1: PNCPLegacyAdapter.code — NoneType access

**Sentry:** SMARTLIC-BACKEND-E — 6 eventos — `AttributeError: 'PNCPLegacyAdapter' has no attribute 'code'`
**Logger:** routes.search
**Severidade:** Alta — causa HTTPException 500 na busca

### Análise

**Arquivo:** `backend/consolidation.py`, linhas 294 e 570

```python
# Linha 294 — acessa .code sem verificar se fallback_adapter é None
fallback_code = self._fallback_adapter.code

# Linha 570
source_priority[adapter.code] = adapter.metadata.priority
```

A classe `PNCPLegacyAdapter` **tem** a property `.code` (definida em `pncp_client.py:2244`), mas o erro ocorre quando `self._fallback_adapter` é `None` — acessar `.code` em `None` gera o AttributeError.

### Fix

- [x] **AC1:** Adicionar null check antes de acessar `self._fallback_adapter.code` na linha 294
  - `getattr(self._fallback_adapter, "code", "unknown_fallback")`
- [x] **AC2:** Adicionar null check antes de acessar `adapter.code` na linha 570 (se adapter pode ser None)
  - `getattr(adapter, "code", code)` + `getattr(adapter, "metadata", None)` with None guard
- [x] **AC3:** Teste: consolidação com fallback_adapter=None não deve crashar
  - 5 tests in `test_crit_016_sentry_bugs.py::TestConsolidationNullCheck`

---

## Bug 2: Datetime naive vs aware — Comparação inválida

**Sentry:** SMARTLIC-BACKEND-N — 14 eventos — `TypeError: can't compare offset-naive and offset-aware datetimes`
**Logger:** routes.search
**Severidade:** Alta — causa HTTPException 500 na busca

### Análise

**Arquivo:** `backend/search_pipeline.py`, linhas 234 e 901

```python
# Linha 234 — ERRADO: utcnow() retorna datetime NAIVE (sem timezone)
data_timestamp = dt.utcnow().isoformat() + "Z"

# Linha 901 — ERRADO: datetime.now() retorna datetime NAIVE
"cached_at": datetime.now().isoformat() + "Z",
```

Outros pontos do código usam `datetime.now(timezone.utc)` (aware), causando incompatibilidade quando esses datetimes são comparados.

**Padrão correto** (já usado em filter.py:1718):
```python
agora = datetime.now(timezone.utc)
```

### Fix

- [x] **AC4:** Substituir `dt.utcnow()` por `datetime.now(timezone.utc)` na linha 234
  - `search_pipeline.py:233`: `datetime.now(_tz.utc).isoformat()`
- [x] **AC5:** Substituir `datetime.now()` por `datetime.now(timezone.utc)` na linha 901
  - `search_pipeline.py:900`: `datetime.now(_tz.utc).isoformat()`
- [x] **AC6:** Grep por `utcnow()` e `datetime.now()` (sem timezone) em todo o backend — corrigir todos
  - Fixed: `search_pipeline.py` (3 locations), `filter_stats.py` (3 locations)
  - Remaining `datetime.now()` in non-comparison contexts left as-is (scripts, reports, tests)
- [x] **AC7:** Teste: pipeline não gera TypeError em comparações de datetime
  - 5 tests in `test_crit_016_sentry_bugs.py::TestDatetimeAwareTimestamps`

---

## Bug 3: SourceConfig.get_available_sources — Método inexistente

**Sentry:** SMARTLIC-BACKEND-A — 3 eventos — `AttributeError: 'SourceConfig' has no attribute 'get_available_sources'`
**Logger:** routes.search
**Severidade:** Média — causa HTTPException 500 em configurações específicas

### Análise

**Arquivo:** `backend/source_config/sources.py`

O código chama `config.get_available_sources()` mas o método correto é `config.get_enabled_sources()` (definido na linha 454).

### Fix

- [x] **AC8:** Encontrar a chamada a `get_available_sources()` e substituir por `get_enabled_sources()`
  - No call found in current codebase (likely from a dynamic or deployed path)
- [x] **AC9:** Adicionar alias `get_available_sources = get_enabled_sources` como medida defensiva (deprecation warning)
  - Added with `warnings.warn(DeprecationWarning)` in `source_config/sources.py`
- [x] **AC10:** Teste: SourceConfig.get_enabled_sources() retorna lista de fontes habilitadas
  - 4 tests in `test_crit_016_sentry_bugs.py::TestSourceConfigDeprecation`

---

## Bug 4: Frontend — `Cannot read properties of undefined (reading 'bg')`

**Sentry:** SMARTLIC-FRONTEND-2 — 1 evento — `TypeError: Cannot read properties of undefined (reading 'bg')`
**Rota:** /buscar
**Severidade:** Baixa — 1 evento, mas pode aumentar com mais tráfego

### Análise

**Arquivo:** `frontend/app/buscar/components/ViabilityBadge.tsx`, linha 98

```typescript
// Linha 61 — pode ser undefined se level não é "alta"|"media"|"baixa"
const c = config[level];

// Linha 62 — guard existe mas pode não cobrir todos os casos
if (!c) return null;

// Linha 98 — se c for undefined (guard falhou), .bg causa TypeError
className={`... ${c.bg}`}
```

O `config` object tem keys `alta`, `media`, `baixa`. Se `level` chega como valor inesperado (null, undefined, string diferente), `config[level]` é undefined.

**Mesmo padrão em risco:**
- `OperationalStateBanner.tsx:84` — `${config.bg}`
- `UfProgressGrid.tsx:140` — `${config.bg}`

### Fix

- [x] **AC11:** Adicionar fallback no ViabilityBadge: `const c = config[level] ?? config.baixa` (ou return null mais cedo)
  - `const c = config[level] ?? config["baixa"]`
- [x] **AC12:** Revisar OperationalStateBanner e UfProgressGrid para o mesmo padrão
  - `OperationalStateBanner.tsx`: `stateConfig[state] ?? stateConfig.degraded`
  - `UfProgressGrid.tsx`: `statusConfigs[status.status] ?? statusConfigs.pending`
- [x] **AC13:** Teste: ViabilityBadge com level=undefined não deve crashar
  - 14 tests in `crit-016-sentry-bugs.test.tsx` (6 ViabilityBadge + 4 OperationalStateBanner + 4 UfProgressGrid)

---

## Critérios Gerais

- [x] **AC14:** Zero regressões nos testes existentes (baseline: ~35 fail backend, ~50 fail frontend)
- [x] **AC15:** Testes cobrindo todos os 4 bugs (pelo menos 1 por bug)
  - Backend: 14 tests (5 Bug1 + 5 Bug2 + 4 Bug3)
  - Frontend: 14 tests (6 Bug4-ViabilityBadge + 4 Bug4-OperationalState + 4 Bug4-UfProgressGrid)

## Arquivos Impactados

| Arquivo | Bug | Mudança |
|---------|-----|---------|
| `backend/consolidation.py:294,570` | Bug 1 | `getattr()` fallback antes de .code |
| `backend/search_pipeline.py:233,900,1993` | Bug 2 | `datetime.now(_tz.utc).isoformat()` |
| `backend/filter_stats.py:77,103,124` | Bug 2 | `datetime.now(timezone.utc)` |
| `backend/source_config/sources.py:467` | Bug 3 | `get_available_sources()` alias + deprecation warning |
| `frontend/app/buscar/components/ViabilityBadge.tsx:61` | Bug 4 | `?? config["baixa"]` fallback |
| `frontend/app/buscar/components/OperationalStateBanner.tsx:78` | Bug 4 | `?? stateConfig.degraded` fallback |
| `frontend/app/buscar/components/UfProgressGrid.tsx:133` | Bug 4 | `?? statusConfigs.pending` fallback |
| `backend/tests/test_crit_016_sentry_bugs.py` | All | 14 backend tests |
| `frontend/__tests__/crit-016-sentry-bugs.test.tsx` | Bug 4 | 14 frontend tests |

## Referências

- GTM-FIX-024 (PNCPLegacyAdapter) — criou o adapter
- GTM-FIX-031 (Datetime fixes) — corrigiu parte dos datetimes mas não todos
- GTM-RESILIENCE-D04 (Viability Assessment) — criou ViabilityBadge

## Definition of Done

- [x] Todos os 4 bugs corrigidos
- [x] Testes para cada bug
- [x] Zero regressões
- [ ] Sentry issues marcados como resolvidos após deploy
