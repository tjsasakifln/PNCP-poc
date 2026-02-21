# CRIT-016 — Production Code Bugs (4 bugs do Sentry)

**Status:** pending
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

- [ ] **AC1:** Adicionar null check antes de acessar `self._fallback_adapter.code` na linha 294
- [ ] **AC2:** Adicionar null check antes de acessar `adapter.code` na linha 570 (se adapter pode ser None)
- [ ] **AC3:** Teste: consolidação com fallback_adapter=None não deve crashar

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

- [ ] **AC4:** Substituir `dt.utcnow()` por `datetime.now(timezone.utc)` na linha 234
- [ ] **AC5:** Substituir `datetime.now()` por `datetime.now(timezone.utc)` na linha 901
- [ ] **AC6:** Grep por `utcnow()` e `datetime.now()` (sem timezone) em todo o backend — corrigir todos
- [ ] **AC7:** Teste: pipeline não gera TypeError em comparações de datetime

---

## Bug 3: SourceConfig.get_available_sources — Método inexistente

**Sentry:** SMARTLIC-BACKEND-A — 3 eventos — `AttributeError: 'SourceConfig' has no attribute 'get_available_sources'`
**Logger:** routes.search
**Severidade:** Média — causa HTTPException 500 em configurações específicas

### Análise

**Arquivo:** `backend/source_config/sources.py`

O código chama `config.get_available_sources()` mas o método correto é `config.get_enabled_sources()` (definido na linha 454).

### Fix

- [ ] **AC8:** Encontrar a chamada a `get_available_sources()` e substituir por `get_enabled_sources()`
- [ ] **AC9:** Adicionar alias `get_available_sources = get_enabled_sources` como medida defensiva (deprecation warning)
- [ ] **AC10:** Teste: SourceConfig.get_enabled_sources() retorna lista de fontes habilitadas

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

- [ ] **AC11:** Adicionar fallback no ViabilityBadge: `const c = config[level] ?? config.baixa` (ou return null mais cedo)
- [ ] **AC12:** Revisar OperationalStateBanner e UfProgressGrid para o mesmo padrão
- [ ] **AC13:** Teste: ViabilityBadge com level=undefined não deve crashar

---

## Critérios Gerais

- [ ] **AC14:** Zero regressões nos testes existentes (baseline: ~35 fail backend, ~50 fail frontend)
- [ ] **AC15:** Testes cobrindo todos os 4 bugs (pelo menos 1 por bug)

## Arquivos Impactados

| Arquivo | Bug | Mudança |
|---------|-----|---------|
| `backend/consolidation.py:294,570` | Bug 1 | Null check antes de .code |
| `backend/search_pipeline.py:234,901` | Bug 2 | `datetime.now(timezone.utc)` |
| `backend/routes/search.py` ou caller | Bug 3 | `get_available_sources` → `get_enabled_sources` |
| `frontend/app/buscar/components/ViabilityBadge.tsx:61` | Bug 4 | Fallback para config undefined |

## Referências

- GTM-FIX-024 (PNCPLegacyAdapter) — criou o adapter
- GTM-FIX-031 (Datetime fixes) — corrigiu parte dos datetimes mas não todos
- GTM-RESILIENCE-D04 (Viability Assessment) — criou ViabilityBadge

## Definition of Done

- [ ] Todos os 4 bugs corrigidos
- [ ] Testes para cada bug
- [ ] Zero regressões
- [ ] Sentry issues marcados como resolvidos após deploy
