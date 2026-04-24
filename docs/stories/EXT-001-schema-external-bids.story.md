# EXT-001: Schema `external_bids` — Fundação Supabase

**Status:** Ready
**Origem:** EPIC-EXT-001 — Fontes Externas de Licitações
**Prioridade:** P0 — Fundação (todas as outras stories dependem desta)
**Complexidade:** M (Medium) — ~8h
**Sprint:** EXT-sprint-01
**Owner:** @data-engineer + @architect
**Tipo:** Database / Infrastructure

---

## Problema

O SmartLic não tem tabela para armazenar licitações vindas de fontes externas (fora do PNCP). A tabela `pncp_raw_bids` é específica para dados do PNCP e não pode ser reutilizada para fontes heterogêneas com schema diferente.

Precisamos de uma fundação de storage com:
- Schema unificado para fontes heterogêneas (Querido Diário, BNC, IPM, etc.)
- Deduplicação robusta intra-fonte e cross-fonte
- Full-text search em português (análogo ao `search_datalake` RPC existente)
- RLS adequado para service_role escrever, anon ler

---

## Critérios de Aceite

- [ ] **AC1:** Migration `supabase/migrations/YYYYMMDDHHMMSS_create_external_bids.sql` criada com todos os campos especificados e paired `*.down.sql`
- [ ] **AC2:** `UNIQUE(source_name, external_id)` enforced — insert duplicado retorna conflict sem erro
- [ ] **AC3:** `UNIQUE(content_hash) WHERE content_hash IS NOT NULL` enforced — dedup cross-fonte funciona
- [ ] **AC4:** GIN index `idx_external_bids_objeto_fts` em `to_tsvector('portuguese', objeto)` presente
- [ ] **AC5:** Índices compostos `(uf, data_publicacao DESC)` e `(is_active, data_publicacao DESC)` presentes
- [ ] **AC6:** RLS policies: anon pode SELECT WHERE is_active=true; service_role tem acesso completo
- [ ] **AC7:** RPC `search_external_bids(query text, filters jsonb)` funcional — retorna resultados com full-text search e filtros de uf, data_inicio, data_fim, modalidade_codigo
- [ ] **AC8:** Teste de integração `pytest tests/test_external_bids_schema.py` cobrindo: insert, upsert conflict, dedup hash, RPC básica
- [ ] **AC9:** `npx supabase db push` aplica migration sem erros em environment de dev

### Anti-requisitos

- Não reutilizar nem alterar `pncp_raw_bids` — são tabelas separadas com propósitos distintos
- Não adicionar colunas de classificação LLM (setor, viabilidade) agora — são adicionadas em story posterior se necessário
- Não criar endpoint de API agora — a integração no search pipeline é EXT-007

---

## Schema Completo

```sql
CREATE TABLE external_bids (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_name      TEXT NOT NULL,
  source_priority  INT NOT NULL,
  external_id      TEXT NOT NULL,
  content_hash     TEXT,
  orgao_cnpj       CHAR(14),
  orgao_nome       TEXT NOT NULL,
  uf               CHAR(2) NOT NULL,
  municipio_ibge   CHAR(7),
  esfera           TEXT NOT NULL DEFAULT 'municipal',
  objeto           TEXT NOT NULL,
  modalidade_codigo INT,
  valor_estimado   NUMERIC(15,2),
  data_publicacao  DATE NOT NULL,
  data_abertura    TIMESTAMPTZ,
  situacao         TEXT,
  url_fonte        TEXT NOT NULL,
  raw_html_hash    TEXT,
  is_active        BOOLEAN NOT NULL DEFAULT TRUE,
  ingested_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_external_bid_source UNIQUE(source_name, external_id)
);

CREATE UNIQUE INDEX uq_external_bids_content_hash
  ON external_bids(content_hash)
  WHERE content_hash IS NOT NULL;

CREATE INDEX idx_external_bids_objeto_fts
  ON external_bids USING GIN(to_tsvector('portuguese', objeto));

CREATE INDEX idx_external_bids_uf_date
  ON external_bids(uf, data_publicacao DESC);

CREATE INDEX idx_external_bids_active_date
  ON external_bids(is_active, data_publicacao DESC)
  WHERE is_active = TRUE;
```

**Valores para `source_name` e `source_priority`:**
| source_name | source_priority |
|---|---|
| `querido_diario` | 4 |
| `bnc` | 5 |
| `ipm_atende` | 6 |
| `comprasgov_historico` | 7 |

**RPC:**
```sql
CREATE OR REPLACE FUNCTION search_external_bids(
  query_text TEXT,
  filters JSONB DEFAULT '{}'::JSONB
)
RETURNS SETOF external_bids
LANGUAGE sql STABLE
AS $$
  SELECT * FROM external_bids
  WHERE
    is_active = TRUE
    AND (query_text = '' OR to_tsvector('portuguese', objeto) @@ plainto_tsquery('portuguese', query_text))
    AND (filters->>'uf' IS NULL OR uf = filters->>'uf')
    AND (filters->>'data_inicio' IS NULL OR data_publicacao >= (filters->>'data_inicio')::DATE)
    AND (filters->>'data_fim' IS NULL OR data_publicacao <= (filters->>'data_fim')::DATE)
    AND (filters->>'modalidade_codigo' IS NULL OR modalidade_codigo = (filters->>'modalidade_codigo')::INT)
  ORDER BY data_publicacao DESC
  LIMIT COALESCE((filters->>'limit')::INT, 100);
$$;
```

---

## Tarefas

- [ ] Criar `supabase/migrations/{timestamp}_create_external_bids.sql` com schema completo
- [ ] Criar `supabase/migrations/{timestamp}_create_external_bids.down.sql` com DROP TABLE
- [ ] Adicionar RLS policies (anon SELECT, service_role ALL)
- [ ] Criar RPC `search_external_bids` na migration
- [ ] Criar `backend/tests/test_external_bids_schema.py` com testes de integração
- [ ] Documentar tabela em `supabase/migrations/README.md` (adicionar linha na tabela de migrations)

---

## Referência de Implementação

- Migration pattern: ver `supabase/migrations/` para formato existente (timestamp, comentários, down.sql)
- RLS pattern: ver tabela `pncp_raw_bids` — política similar (anon pode ler, service_role pode tudo)
- RPC pattern: ver função `search_datalake` existente para modelo de full-text search
- Teste de integração: ver `backend/tests/test_ingestion/` para padrões de teste de database

---

## Riscos

- **R1 (Baixo):** `content_hash` UNIQUE index parcial pode causar confusão — documentar claramente que NULL não viola unique (comportamento correto e esperado)
- **R2 (Baixo):** `source_priority` como INT não tem constraint de range — validar no loader (EXT-006), não no DB

---

## Dependências

- **Nenhuma** — story fundação, sem dependências de outras EXT stories
- `supabase/migrations/README.md` deve existir (já existe)
- Acesso ao Supabase project com `SUPABASE_ACCESS_TOKEN` em `.env`

---

## Arquivos Relevantes

| Arquivo | Ação |
|---------|------|
| `supabase/migrations/{ts}_create_external_bids.sql` | Criar |
| `supabase/migrations/{ts}_create_external_bids.down.sql` | Criar |
| `backend/tests/test_external_bids_schema.py` | Criar |
| `supabase/migrations/README.md` | Atualizar (adicionar linha) |

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-23 | @sm | Story criada — EPIC-EXT-001 |
| 2026-04-23 | @po | Validação 10-pontos: **9/10 → GO** — ponto 7 (business value) implícito no epic; aceito. Status: Draft → Ready |
