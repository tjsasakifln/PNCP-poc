# STORY-283: Phantom Sources & Stale Config Cleanup

**Priority:** P1
**Effort:** 0.5 day
**Squad:** @dev
**Fundamentacao:** Logs de producao 2026-02-26 (warnings constantes)
**Status:** COMPLETED

## Problemas Observados em Producao

### 1. Licitar Digital — Fonte Fantasma
```
WARNING: Licitar Digital enabled but LICITAR_API_KEY not set
Sources with pending credentials: ['Licitar']
```
- `source_config/sources.py`: config completo (URL, timeout, rate limit)
- `clients/licitar_client.py`: **arquivo vazio (0 bytes)**
- Nunca teve API key configurada
- **Status: JA CORRIGIDO** — default alterado para `enabled=False`

### 2. Unknown Plan IDs
```
Unknown plan_id 'free' in database, using conservative defaults
Unknown plan_id 'master' in database, using conservative defaults
Loaded 3 plan capabilities from database: ['free', 'master', 'smartlic_pro']
```
- `quota.py` so reconhece `smartlic_pro` e planos legacy (consultor_agil, maquina, sala_guerra)
- `free` e `master` existem na tabela `plan_capabilities` no Supabase
- Nao estao mapeados no `PLAN_CONFIGS` dict
- Warning polui logs a cada busca

### 3. Co-occurrence Triggers Orphans
```
Co-occurrence trigger 'padronizacao' in sector 'vestuario' does not match any keyword prefix — may never fire
Co-occurrence trigger 'rede' in sector 'informatica' does not match any keyword prefix — may never fire
```
- `sectors_data.yaml`: triggers definidos mas sem keyword correspondente
- Warning emitido no startup do worker (a cada restart)
- Funcional mas polui logs

## Acceptance Criteria

### AC1: Mapear plan_ids 'free' e 'master' no quota.py
- [x] Adicionar `free` ao `PLAN_CAPABILITIES` com limites adequados:
  - `max_searches_per_month = 10`
  - `max_history_days = 7`
  - `allow_excel = false`
  - `search_priority = "LOW"`
- [x] Adicionar `master` com limites maximais:
  - `max_searches_per_month = 99999`
  - `max_history_days = 99999`
  - `allow_excel = true`
  - `search_priority = "HIGH"`
- [x] Mantidos no `PLAN_CAPABILITIES` dict (decisao: manter ambos)
- [x] **Decisao PO:** manter `free`/`master` — `free` para limitado, `master` para admin

### AC2: Deletar arquivo vazio licitar_client.py
- [x] `rm backend/clients/licitar_client.py`
- [x] Verificar que nenhum import referencia o arquivo
- [x] Manter config em sources.py (desabilitado) para futura integracao

### AC3: Corrigir co-occurrence triggers orphans
- [x] `sectors_data.yaml` vestuario: removido trigger "padronizacao" (coberto por exclusions)
- [x] `sectors_data.yaml` informatica: adicionado "rede" e "redes" as keywords
- [x] `sectors.py` validacao alinhada com test (prefix OR substring match)
- [x] Validar: zero warnings no startup apos fix

### AC4: Limpar logs de startup
- [x] Apos fixes, zero WARNINGs de co-occurrence orphans
- [x] `Sources with pending credentials` ja condicionado a lista nao vazia

## Files Modified

| File | Change |
|------|--------|
| `backend/quota.py` | Mapped 'free' + 'master' plan_ids in PLAN_CAPABILITIES + PLAN_NAMES |
| `backend/clients/licitar_client.py` | **DELETED** (was empty) |
| `backend/sectors_data.yaml` | Removed 'padronizacao' trigger, added 'rede'/'redes' keywords |
| `backend/sectors.py` | Aligned validation: prefix OR substring match |
| `backend/tests/test_story283_phantom_cleanup.py` | 24 tests covering all ACs |

## Test Results

- 24 new tests: all pass
- 111 related tests (plan_capabilities + quota + story283): all pass
- Zero regressions from STORY-283 changes
