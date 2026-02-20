# CRIT-001: Alinhar Schema do Banco e Implementar Protecao Contra Drift

## Epic
Epic: Consistencia Estrutural do Sistema (EPIC-CRIT)

## Sprint
Sprint 1: Fundacao

## Prioridade
P0

## Estimativa
8h (4h migration + modelo Pydantic, 2h CI/health check, 2h testes)

## Descricao

O banco de producao esta em estado de drift silencioso. Duas migrations compartilham o prefixo `027_`, e a segunda (que adiciona `sources_json` e `fetched_at` a `search_results_cache`) nunca foi aplicada em producao. O codigo em `search_cache.py` referencia essas colunas extensivamente, mas a ausencia e mascarada por fallbacks como `row.get("fetched_at") or row.get("created_at")`.

O problema e mais profundo do que colunas faltantes: nao existe um modelo Pydantic que defina a tabela `search_results_cache` como single source of truth. O schema esta implicitamente distribuido entre 5 migrations (026, 027-cache, 031, 032) e dezenas de queries manuais em `search_cache.py`. Nao ha validacao em startup nem em CI que detecte divergencia entre schema esperado e schema real.

**Impacto concreto:**
- `sources_json` nunca foi persistido em producao -- cache entries nao registram fontes
- `fetched_at` nunca existiu -- TTL calculations caem no fallback `created_at`, potencialmente servindo dados mais velhos que o intendido
- Backfill UPDATEs nas migrations 031 e 032 referenciam `fetched_at` -- podem ter falhado silenciosamente em producao
- Migration 031 linha 21: `SET last_success_at = fetched_at` -- se `fetched_at` nao existe, o UPDATE falha sem afetar rows
- Migration 032 linha 53: `SET last_accessed_at = COALESCE(last_success_at, fetched_at, created_at)` -- idem

**Root cause:** Ausencia de guardrails contra drift -- nenhuma validacao automatica detecta migrations conflitantes ou colunas faltantes.

## Especialistas Consultados
- Data Engineer: Analise de migrations e dependencias entre colunas
- Architect: Design do health check de startup e modelo Pydantic como SSOT
- QA: Estrategia de testes de idempotencia e validacao de schema

## Evidencia da Investigacao

### Migrations conflitantes (prefixo duplicado `027_`)
- `supabase/migrations/027_fix_plan_type_default_and_rls.sql` (2026-02-15, commit `1d14de6`)
- `supabase/migrations/027_search_cache_add_sources_and_fetched_at.sql` (2026-02-17, commit `c1b80bc`)

### Colunas referenciadas em `search_cache.py` que dependem da migration nao-aplicada

**`sources_json` (6 referencias):**
- Linha 182: `"sources_json": sources,` (save_to_supabase upsert payload)
- Linha 213: `.select("results, total_results, sources_json, fetched_at, ...")` (get_from_supabase query)
- Linha 229: `"sources_json": row.get("sources_json"),` (response construction)
- Linha 716: `"cached_sources": data.get("sources_json") or ["pncp"],` (cache metrics)
- Linha 1425: `"params_hash, user_id, search_params, total_results, sources_json, "` (admin inspect query)
- Linha 1460: `"sources": row.get("sources_json", []),` (admin inspect response)

**`fetched_at` (4+ referencias diretas, 20+ transitivas via `get_cache_status()`):**
- Linha 183: `"fetched_at": now,` (save_to_supabase upsert payload)
- Linha 213: `.select("..., fetched_at, created_at, ...")` (get_from_supabase query)
- Linha 225: `row.get("fetched_at") or row.get("created_at")` (fallback que mascara a ausencia)
- Linha 1232: `.select("params_hash, priority, fetched_at, access_count, ...")` (health status query)

### Fallback que mascara o drift
- Linha 225: `fetched_at_str = row.get("fetched_at") or row.get("created_at")` -- se `fetched_at` nao existe na row retornada pelo Supabase, cai silenciosamente para `created_at`. Zero log, zero alerta.

### Backfills que podem ter falhado silenciosamente
- `031_cache_health_metadata.sql` linha 21: `SET last_success_at = fetched_at` -- referencia `fetched_at` que pode nao existir
- `032_cache_priority_fields.sql` linha 53: `SET last_accessed_at = COALESCE(last_success_at, fetched_at, created_at)` -- idem

### Ausencia de modelo Pydantic
- `backend/models/__init__.py` documenta que modelos ORM sao deprecated (STORY-201)
- Nao existe `SearchResultsCacheRow` em nenhum arquivo do backend
- Schema da tabela definido implicitamente em 5 migrations (026, 027-cache, 031, 032) com 18 colunas total

### Colunas esperadas na tabela `search_results_cache` (18 total)
| # | Coluna | Tipo | Migration de origem |
|---|--------|------|---------------------|
| 1 | `id` | UUID PK | 026 |
| 2 | `user_id` | UUID FK | 026 |
| 3 | `params_hash` | TEXT | 026 |
| 4 | `search_params` | JSONB | 026 |
| 5 | `results` | JSONB | 026 |
| 6 | `total_results` | INTEGER | 026 |
| 7 | `created_at` | TIMESTAMPTZ | 026 |
| 8 | `sources_json` | JSONB | 027-cache (NAO APLICADA) |
| 9 | `fetched_at` | TIMESTAMPTZ | 027-cache (NAO APLICADA) |
| 10 | `last_success_at` | TIMESTAMPTZ | 031 |
| 11 | `last_attempt_at` | TIMESTAMPTZ | 031 |
| 12 | `fail_streak` | INTEGER | 031 |
| 13 | `degraded_until` | TIMESTAMPTZ | 031 |
| 14 | `coverage` | JSONB | 031 |
| 15 | `fetch_duration_ms` | INTEGER | 031 |
| 16 | `priority` | TEXT | 032 |
| 17 | `access_count` | INTEGER | 032 |
| 18 | `last_accessed_at` | TIMESTAMPTZ | 032 |

## Criterios de Aceite

### Migration corretiva (AC1-AC2)

- [ ] **AC1:** Criar migration idempotente `033_fix_missing_cache_columns.sql` com:
  - `ALTER TABLE search_results_cache ADD COLUMN IF NOT EXISTS sources_json JSONB NOT NULL DEFAULT '["pncp"]'::jsonb;`
  - `ALTER TABLE search_results_cache ADD COLUMN IF NOT EXISTS fetched_at TIMESTAMPTZ DEFAULT now() NOT NULL;`
  - `CREATE INDEX IF NOT EXISTS idx_search_cache_fetched_at ON search_results_cache(fetched_at);`
  - Incluir `SET statement_timeout = '30s';` como guardrail contra timeout em tabelas grandes
  - Comentario no topo explicando que esta migration corrige drift do prefixo `027_` duplicado

- [ ] **AC2:** Renomear `027_search_cache_add_sources_and_fetched_at.sql` para `027b_search_cache_add_sources_and_fetched_at.sql` com header `-- SUPERSEDED by 033_fix_missing_cache_columns.sql` e manter como registro historico (nao deletar)

### Modelo Pydantic como Single Source of Truth (AC3)

- [ ] **AC3:** Criar `backend/models/cache.py` com classe `SearchResultsCacheRow(BaseModel)` contendo todos os 18 campos da tabela como single source of truth:
  - Campos obrigatorios: `id` (UUID), `user_id` (UUID), `params_hash` (str), `search_params` (dict), `results` (list), `total_results` (int), `created_at` (datetime), `sources_json` (list), `fetched_at` (datetime)
  - Campos opcionais (nullable): `last_success_at`, `last_attempt_at`, `degraded_until`, `coverage`, `last_accessed_at`
  - Campos com default: `fail_streak` (int, default=0), `fetch_duration_ms` (int | None), `priority` (str, default="cold"), `access_count` (int, default=0)
  - Adicionar classmethod `expected_columns() -> set[str]` que retorna o set de nomes de colunas
  - Exportar de `backend/models/__init__.py`

### Health check de startup (AC4)

- [ ] **AC4:** Adicionar health check de schema em `main.py` no evento `startup` que:
  - Executa `SELECT column_name FROM information_schema.columns WHERE table_name = 'search_results_cache'`
  - Compara resultado contra `SearchResultsCacheRow.expected_columns()`
  - Se colunas faltantes: loga `CRITICAL` com lista de colunas faltantes, mas NAO crasha (graceful degradation)
  - Se colunas extras (no banco mas nao no modelo): loga `WARNING`
  - Se match perfeito: loga `INFO` com "Schema validation passed for search_results_cache"
  - Health check protegido por try/except para nao bloquear startup em caso de DB indisponivel

### Validacao CI contra migrations duplicadas (AC5)

- [ ] **AC5:** Criar `backend/scripts/validate_migrations.py` que:
  - Lista todos os arquivos em `supabase/migrations/` que matcham `\d{3}_.*\.sql`
  - Extrai prefixo numerico de cada um
  - Falha com exit code 1 se qualquer prefixo aparece mais de uma vez
  - Imprime lista de conflitos encontrados
  - Pode ser executado standalone: `python backend/scripts/validate_migrations.py`
  - Adicionar step no GitHub Actions CI workflow (`.github/workflows/tests.yml`) que executa este script

### Backfill de dados existentes (AC6-AC8)

- [ ] **AC6:** Na migration 033, incluir backfill de `sources_json`:
  ```sql
  UPDATE search_results_cache
  SET sources_json = '["pncp"]'::jsonb
  WHERE sources_json IS NULL;
  ```

- [ ] **AC7:** Na migration 033, incluir backfill de `fetched_at`:
  ```sql
  UPDATE search_results_cache
  SET fetched_at = created_at
  WHERE fetched_at IS NULL;
  ```

- [ ] **AC8:** Na migration 033, re-executar backfills das migrations 031 e 032 que podem ter falhado:
  ```sql
  -- Re-run 031 backfill (may have failed if fetched_at didn't exist)
  UPDATE search_results_cache
  SET last_success_at = fetched_at,
      last_attempt_at = fetched_at
  WHERE last_success_at IS NULL AND fetched_at IS NOT NULL;

  -- Re-run 032 backfill (may have failed if fetched_at/last_success_at were NULL)
  UPDATE search_results_cache
  SET last_accessed_at = COALESCE(last_success_at, fetched_at, created_at)
  WHERE last_accessed_at IS NULL;
  ```

### Documentacao (AC9)

- [ ] **AC9:** Atualizar `supabase/docs/SCHEMA.md` para incluir tabela `search_results_cache` com todas as 18 colunas, suas types, defaults, e migration de origem

### Validacao runtime em queries (AC10-AC12)

- [ ] **AC10:** Todas as queries Supabase em `search_cache.py` que fazem `.select(...)` devem referenciar apenas colunas presentes em `SearchResultsCacheRow.expected_columns()`. Adicionar comentario `# Columns validated against SearchResultsCacheRow` em cada query.

- [ ] **AC11:** Adicionar validacao em `_get_from_supabase()` (search_cache.py) que:
  - Apos receber row do Supabase, verifica se campos esperados estao presentes
  - Se campo faltante: loga `WARNING` com nome do campo e usa default do modelo Pydantic
  - Nunca crasha -- fallback gracioso para cada campo

- [ ] **AC12:** Adicionar validacao em `_save_to_supabase()` (search_cache.py) que:
  - Antes do upsert, filtra o dict de payload para conter apenas keys presentes em `SearchResultsCacheRow.expected_columns()`
  - Loga `WARNING` se alguma key do payload nao esta no modelo (indica drift no codigo)
  - Loga `WARNING` se o modelo espera keys que nao estao no payload (indica campo faltante)

### Script de validacao standalone (AC13)

- [ ] **AC13:** Criar `backend/scripts/validate_schema.py` que pode ser executado contra qualquer ambiente:
  - Aceita parametro `--database-url` ou usa `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` do .env
  - Executa `SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_name = 'search_results_cache'`
  - Compara contra `SearchResultsCacheRow` modelo
  - Reporta: colunas faltantes, colunas extras, type mismatches, default mismatches
  - Exit code 0 se OK, exit code 1 se divergencia encontrada
  - Output formatado em tabela legivel

### Idempotencia da migration (AC14)

- [ ] **AC14:** Migration 033 deve ser segura para executar multiplas vezes:
  - Todos os `ALTER TABLE` usam `ADD COLUMN IF NOT EXISTS`
  - Todos os `CREATE INDEX` usam `IF NOT EXISTS`
  - UPDATEs de backfill usam `WHERE ... IS NULL` (nao sobrescrevem dados validos)
  - Testar executando a migration 2x em sequencia sem erro

### Zero regressoes (AC15)

- [ ] **AC15:** Todos os testes existentes em `test_search_cache.py` devem passar apos as mudancas, sem alteracao nos mocks ou assertions existentes. Baseline: verificar count atual antes de comecar.

### Integridade do modelo (AC16)

- [ ] **AC16:** `SearchResultsCacheRow` deve ter 100% de cobertura de teste:
  - Teste de instanciacao com todos os campos
  - Teste de instanciacao com apenas campos obrigatorios (opcionais como None)
  - Teste de `expected_columns()` retorna exatamente 18 nomes
  - Teste de validacao Pydantic rejeita tipos errados

## Testes Obrigatorios

| ID | Teste | Tipo | Prioridade |
|----|-------|------|-----------|
| MIG-T01 | Migration 033 executa sem erro em banco limpo (pos-026) | Integracao SQL | P0 |
| MIG-T02 | Migration 033 executa sem erro em banco que ja tem as colunas (idempotencia) | Integracao SQL | P0 |
| MIG-T03 | Migration 033 executada 2x em sequencia sem erro | Integracao SQL | P0 |
| MOD-T01 | `SearchResultsCacheRow` instancia com todos os 18 campos | Unitario | P0 |
| MOD-T02 | `SearchResultsCacheRow` instancia com apenas campos obrigatorios | Unitario | P0 |
| MOD-T03 | `SearchResultsCacheRow.expected_columns()` retorna set com 18 elementos | Unitario | P0 |
| MOD-T04 | `SearchResultsCacheRow` rejeita `total_results` como string (validacao Pydantic) | Unitario | P1 |
| HC-T01 | Health check de startup detecta coluna faltante e loga CRITICAL | Unitario | P0 |
| HC-T02 | Health check de startup passa com schema correto e loga INFO | Unitario | P0 |
| HC-T03 | Health check de startup sobrevive a DB indisponivel (nao crasha) | Unitario | P0 |
| CI-T01 | `validate_migrations.py` detecta prefixo `027_` duplicado e retorna exit code 1 | Unitario | P0 |
| CI-T02 | `validate_migrations.py` passa com migrations sem conflito (exit code 0) | Unitario | P1 |
| VAL-T01 | `validate_schema.py` detecta coluna faltante no banco | Integracao | P1 |
| VAL-T02 | `validate_schema.py` reporta schema alinhado (exit code 0) | Integracao | P1 |
| REG-T01 | Todos os testes pre-existentes em `test_search_cache.py` passam sem modificacao | Regressao | P0 |
| RUN-T01 | Validacao runtime em `_get_from_supabase()` loga WARNING para campo faltante | Unitario | P0 |
| RUN-T02 | Validacao runtime em `_save_to_supabase()` filtra keys desconhecidas | Unitario | P0 |

## Definicao de Pronto

- [ ] Migration 033 criada, testada localmente, e aplicada em producao via `npx supabase db push`
- [ ] `SearchResultsCacheRow` existe em `backend/models/cache.py` com 18 campos
- [ ] Health check de startup logando resultado em producao (verificar logs Railway)
- [ ] `validate_migrations.py` executando no CI e detectando o prefixo `027_` duplicado (ou duplicata ja resolvida)
- [ ] `validate_schema.py` executado contra producao com exit code 0
- [ ] `SCHEMA.md` atualizado com tabela `search_results_cache` completa
- [ ] Todos os 17 testes obrigatorios passando
- [ ] Zero regressoes em `test_search_cache.py`
- [ ] PR aprovado e merged

## Riscos e Mitigacoes

| # | Risco | Probabilidade | Impacto | Mitigacao |
|---|-------|--------------|---------|-----------|
| R1 | Producao tem NULL em `sources_json`/`fetched_at` apos backfill | Alta | Medio | Backfill UPDATEs usam defaults seguros (`'["pncp"]'`, `created_at`). Validacao runtime protege leitura. |
| R2 | Migration 033 faz timeout em tabelas grandes | Baixa | Alto | `SET statement_timeout = '30s'`. Se timeout: executar backfills em batches de 1000 rows. |
| R3 | Codigo em `search_cache.py` quebra se modelo Pydantic e restritivo demais | Media | Medio | Modelo usa `Optional` para campos nullable. Validacao runtime loga WARNING, nao crasha. |
| R4 | Health check de startup causa lentidao no boot | Baixa | Baixo | Query e rapida (information_schema). Timeout de 5s no health check. |
| R5 | Backfills de 031/032 ja executaram parcialmente -- re-run pode conflitar | Media | Baixo | Todos os backfills usam `WHERE ... IS NULL` -- nao sobrescrevem dados existentes. |
| R6 | Renomear migration 027 confunde Supabase migration history | Media | Medio | Manter arquivo original (nao deletar), apenas adicionar header de superseded. Migration 033 e a correcao real. |

## Arquivos Envolvidos

| Arquivo | Acao | Descricao |
|---------|------|-----------|
| `supabase/migrations/033_fix_missing_cache_columns.sql` | Novo | Migration corretiva com ADD COLUMN IF NOT EXISTS + backfills |
| `supabase/migrations/027_search_cache_add_sources_and_fetched_at.sql` | Modificado | Renomear para `027b_` + header SUPERSEDED |
| `backend/models/cache.py` | Novo | `SearchResultsCacheRow` Pydantic model (18 campos) |
| `backend/models/__init__.py` | Modificado | Exportar `SearchResultsCacheRow` |
| `backend/main.py` | Modificado | Adicionar health check de schema no startup event |
| `backend/search_cache.py` | Modificado | Validacoes runtime em `_get_from_supabase()` e `_save_to_supabase()` |
| `backend/scripts/validate_migrations.py` | Novo | Script CI para detectar prefixos de migration duplicados |
| `backend/scripts/validate_schema.py` | Novo | Script standalone para comparar schema esperado vs real |
| `supabase/docs/SCHEMA.md` | Modificado | Documentar tabela `search_results_cache` com 18 colunas |
| `.github/workflows/tests.yml` | Modificado | Adicionar step para `validate_migrations.py` |
| `backend/tests/test_crit001_schema_alignment.py` | Novo | 17 testes obrigatorios |

## Dependencias

- **Blocks:** CRIT-002 (necessita schema alinhado antes de adicionar status tracking)
- **Blocks:** CRIT-003 (necessita modelo Pydantic como base para novas features de cache)
- **Blocked by:** Nada -- esta story pode iniciar imediatamente
- **Relacionada:** STORY-TD-001 (foi quem criou a migration 027 que colidiu)
- **Relacionada:** GTM-FIX-010 (criou a segunda migration 027 com `sources_json`/`fetched_at`)
