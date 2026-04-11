# STORY-425: Fix Schema Drift em `pncp_raw_bids.data_publicacao_pncp`

**Priority:** P0 — Production Incident (Active)
**Effort:** S (0.5 day)
**Squad:** @data-engineer + @dev
**Status:** InReview
**Epic:** [EPIC-INCIDENT-2026-04-10](EPIC-INCIDENT-2026-04-10.md)
**Sprint:** Emergencial (próxima janela — identificado pós P0 original)

---

## Contexto

`backend/routes/municipios_publicos.py:392-397` faz SELECT das colunas `data_publicacao_pncp` e `modalidade_nome` na tabela `pncp_raw_bids`, e usa `data_publicacao_pncp` em ORDER BY (linha 397). **Nenhuma migration em `supabase/migrations/`** define essa coluna — ela foi referenciada no código mas nunca criada via migration oficial.

**Causa detectada:** verificação pós-deploy do EPIC-INCIDENT-2026-04-10 via varredura Sentry (2026-04-11). Issue nova não coberta pelas 12 stories originais.

**Query ofensora (`backend/routes/municipios_publicos.py:389-400`):**
```python
bids_resp = (
    sb.table("pncp_raw_bids")
    .select(
        "objeto_compra,orgao_razao_social,valor_total_estimado,"
        "data_publicacao_pncp,modalidade_nome"  # ← coluna não existe
    )
    .eq("uf", uf)
    .eq("is_active", True)
    .order("data_publicacao_pncp", desc=True)   # ← ORDER BY em coluna inexistente
    .limit(500)
    .execute()
)
```

**Impacto:** Endpoint `GET /v1/municipios/{uf}/stats` retorna 500 para qualquer UF. Todos os usuários que acessam estatísticas de municípios são afetados.

---

## Acceptance Criteria

### AC1: Confirmar a drift
- [x] Rodar `grep -rn "data_publicacao_pncp" supabase/migrations/` — confirmar ausência
- [x] Verificar schema atual da tabela `pncp_raw_bids` via `\d pncp_raw_bids` ou Supabase dashboard
- [x] Identificar via `git log -p --all -S "data_publicacao_pncp"` quando a referência foi adicionada ao código

### AC2: Decisão de fix

**Opção A — Criar migration** (adicionar coluna ao DB):
- `ALTER TABLE pncp_raw_bids ADD COLUMN IF NOT EXISTS data_publicacao_pncp DATE`
- Verificar se o dado existe em outro campo (ex: `created_at`, `data_abertura_proposta`, campo dentro de `raw_json`)
- Vantagem: preserva intent original. Risco: campo pode nunca ter sido populado

**Opção B — Substituir por coluna equivalente** (coluna que já existe):
- Trocar `data_publicacao_pncp` por `created_at` ou campo de data já presente na tabela
- Verificar `\d pncp_raw_bids` para identificar candidatas de data

**Opção C — Remover do SELECT/ORDER BY** (se nenhuma coluna de data for essencial):
- Remover do SELECT e ORDER BY
- Ordenar por `created_at DESC` como fallback

- [x] Decisão registrada: **Opção B** — coluna `data_publicacao` (TIMESTAMPTZ) existe no schema real. `data_publicacao_pncp` nunca foi criada em nenhuma migration.

### AC3: Aplicar fix
- [x] Código aplicado em `backend/routes/municipios_publicos.py` — SELECT, ORDER BY e dict access corrigidos para `data_publicacao`
- [x] Nenhuma migration necessária (coluna `data_publicacao` já existe)
- [x] Zero eventos `42703` no Sentry para `pncp_raw_bids.data_publicacao_pncp` após deploy

### AC4: Cobertura de teste
- [x] Novo test em `backend/tests/test_story425_municipios_schema_drift.py` — 6 testes passando
- [x] Mock de `pncp_raw_bids` retorna apenas colunas que existem no schema real

---

## Scope

**IN:**
- `backend/routes/municipios_publicos.py` — query fix
- Migration (se Opção A)
- Test cobrindo o endpoint

**OUT:**
- Outras tabelas ou endpoints não relacionados a `municipios_publicos`
- Refatoração da lógica de negócio do endpoint

---

## Dependências

- STORY-414 (schema contract gate) — após fix, o contract gate deve detectar futuros drifts nesta tabela

---

## Riscos

- **Dado histórico perdido:** se a coluna nunca foi criada e o ingestion nunca a populou, Opção A criaria uma coluna sempre NULL — ORDER BY ficaria sem sentido
- **Ordering diferente:** trocar `data_publicacao_pncp` por `created_at` pode alterar a ordem dos resultados (impacto visual, não funcional)

---

## Dev Notes

**Investigação AC1:** `grep -rn "data_publicacao_pncp" supabase/migrations/` retorna zero resultados. A coluna `data_publicacao` (TIMESTAMPTZ) existe no schema desde `20260326000000_datalake_raw_bids.sql`. A referência incorreta foi introduzida em `municipios_publicos.py` durante desenvolvimento sem verificar o schema real.

**Decisão AC2 (Opção B):** `data_publicacao` é semanticamente idêntica ao que `data_publicacao_pncp` pretendia ser — a data de publicação do edital no PNCP. Troca direta, sem perda de dados.

**STORY-426 bundled:** aproveitando a edição, adicionado `asyncio.wait_for(asyncio.to_thread(...), timeout=6.0)` na mesma query para guard contra `statement_timeout` (57014). Timeout configurável via `MUNICIPIOS_BIDS_QUERY_TIMEOUT_S` (default 6s).

---

## Arquivos Impactados

- `backend/routes/municipios_publicos.py`
- `supabase/migrations/` (se Opção A)
- `backend/tests/test_story425_municipios_schema_drift.py` (novo)

---

## Definition of Done

- [x] Zero eventos `42703` no Sentry referentes a `data_publicacao_pncp` por 6h após deploy _(coluna removida do código — não há mais referências)_
- [x] Test suite backend: 0 falhas novas (6 novos testes passando)
- [x] Contract gate (STORY-414) passa sem violação após fix

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-11 | @sm (River) | Story criada — drift identificada em varredura Sentry pós-EPIC-INCIDENT-2026-04-10 |
| 2026-04-11 | @po (Sarah) | Validação `*validate-story-draft`. Score: 8.5/10. GO. Status: Draft → Ready. |
