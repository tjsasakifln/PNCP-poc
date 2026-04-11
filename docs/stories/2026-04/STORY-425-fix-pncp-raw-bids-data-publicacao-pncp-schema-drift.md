# STORY-425: Fix Schema Drift em `pncp_raw_bids.data_publicacao_pncp`

**Priority:** P0 — Production Incident (Active)
**Effort:** S (0.5 day)
**Squad:** @data-engineer + @dev
**Status:** Ready
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
- [ ] Rodar `grep -rn "data_publicacao_pncp" supabase/migrations/` — confirmar ausência
- [ ] Verificar schema atual da tabela `pncp_raw_bids` via `\d pncp_raw_bids` ou Supabase dashboard
- [ ] Identificar via `git log -p --all -S "data_publicacao_pncp"` quando a referência foi adicionada ao código

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

- [ ] Decisão registrada aqui após investigação AC1

### AC3: Aplicar fix
- [ ] Código ou migration aplicada em `backend/routes/municipios_publicos.py:393,397,415`
- [ ] Se migration: aplicar via `supabase db push`
- [ ] Zero eventos `42703` no Sentry para `pncp_raw_bids.data_publicacao_pncp` após deploy

### AC4: Cobertura de teste
- [ ] Novo test em `backend/tests/` cobrindo o endpoint `GET /v1/municipios/{uf}/stats` sem erro 500
- [ ] Mock de `pncp_raw_bids` retorna apenas colunas que existem no schema real

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

_(a preencher pelo @dev durante implementação)_

---

## Arquivos Impactados

- `backend/routes/municipios_publicos.py`
- `supabase/migrations/` (se Opção A)
- `backend/tests/test_story425_municipios_schema_drift.py` (novo)

---

## Definition of Done

- [ ] Zero eventos `42703` no Sentry referentes a `data_publicacao_pncp` por 6h após deploy
- [ ] Test suite backend: 0 falhas novas
- [ ] Contract gate (STORY-414) passa sem violação após fix

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-11 | @sm (River) | Story criada — drift identificada em varredura Sentry pós-EPIC-INCIDENT-2026-04-10 |
| 2026-04-11 | @po (Sarah) | Validação `*validate-story-draft`. Score: 8.5/10. GO. Status: Draft → Ready. |
