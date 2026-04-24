# EXT-006: Loader + Dedup Pipeline para `external_bids`

**Status:** Ready
**Origem:** EPIC-EXT-001 — Fontes Externas de Licitações
**Prioridade:** P0 — Habilitador (crawlers não persistem sem o loader)
**Complexidade:** M (Medium) — ~8h
**Sprint:** EXT-sprint-02
**Owner:** @dev + @data-engineer
**Tipo:** Backend / Data Pipeline

---

## Problema

Os crawlers (EXT-003, EXT-004, EXT-005) produzem `List[ExternalBidRaw]` mas não têm responsabilidade de persisti-los. Precisamos de um loader centralizado que:
1. Normalize os dados (CNPJ, texto do objeto) para dedup consistente
2. Calcule `content_hash` para dedup cross-fonte
3. Execute upsert em batch com strategy de precedência de fonte
4. Faça soft-delete de registros expirados

Sem normalização padronizada, dois crawlers diferentes descrevendo o mesmo edital com capitalização ou espaçamento diferente vão criar duplicatas.

---

## Critérios de Aceite

- [ ] **AC1:** `ExternalBidLoader.load(bids: list[ExternalBidRaw], source_name: str, source_priority: int)` persiste no Supabase sem erros
- [ ] **AC2:** Normalização antes do hash: `objeto` → lowercase + strip + colapsar múltiplos espaços + remover pontuação; `orgao_cnpj` → apenas dígitos 14 chars; `data_publicacao` → `date.isoformat()`
- [ ] **AC3:** `content_hash = SHA256(objeto_norm + "|" + cnpj_norm + "|" + data_publicacao_iso)` — função pura e testável separadamente
- [ ] **AC4:** Upsert batch de 100 rows: `INSERT ... ON CONFLICT (source_name, external_id) DO UPDATE SET situacao=EXCLUDED.situacao, data_abertura=EXCLUDED.data_abertura, raw_html_hash=EXCLUDED.raw_html_hash, updated_at=NOW()` — atualiza campos mutáveis (situação muda conforme edital progride)
- [ ] **AC5:** Cross-source dedup: `ON CONFLICT (content_hash) DO UPDATE` apenas se `EXCLUDED.source_priority < existing.source_priority` (fonte mais confiável vence)
- [ ] **AC6:** Registros sem `content_hash` (campos insuficientes para hash) ainda são salvos — conflict apenas por `(source_name, external_id)`
- [ ] **AC7:** ARQ cron job `external_bids_cleanup_job` diário às 6am BRT: `UPDATE external_bids SET is_active=FALSE WHERE data_publicacao < NOW() - INTERVAL '15 days' AND is_active=TRUE`
- [ ] **AC8:** Métrica `smartlic_external_bids_upserted_total{source}` incrementada por load
- [ ] **AC9:** Métrica `smartlic_external_bids_dedup_skipped_total{reason}` onde `reason` ∈ `{content_hash_conflict, source_id_conflict}`
- [ ] **AC10:** `pytest tests/ingestion/external/test_loader.py` com testes de: normalização, hash, upsert conflict intra-fonte, conflict cross-fonte

### Anti-requisitos

- Não fazer upsert row-por-row — sempre em batch de 100 (performance)
- Não calcular `content_hash` com campos opcionais ausentes — apenas quando `objeto + cnpj + data_publicacao` todos presentes
- Não deletar fisicamente registros expirados — soft-delete (is_active=FALSE) para auditoria

---

## Normalização

```python
import re
import hashlib
from datetime import date

def normalize_objeto(objeto: str) -> str:
    s = objeto.lower().strip()
    s = re.sub(r'[^\w\s]', ' ', s)   # remove pontuação
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def normalize_cnpj(cnpj: str | None) -> str:
    if not cnpj:
        return ""
    return re.sub(r'\D', '', cnpj).zfill(14)[:14]

def compute_content_hash(
    objeto: str,
    orgao_cnpj: str | None,
    data_publicacao: date,
) -> str | None:
    obj_norm = normalize_objeto(objeto)
    cnpj_norm = normalize_cnpj(orgao_cnpj)
    if not obj_norm or not data_publicacao:
        return None
    raw = f"{obj_norm}|{cnpj_norm}|{data_publicacao.isoformat()}"
    return hashlib.sha256(raw.encode()).hexdigest()
```

---

## Tarefas

- [ ] Criar `backend/ingestion/external/loader.py` com `ExternalBidLoader`
- [ ] Implementar funções de normalização (`normalize_objeto`, `normalize_cnpj`, `compute_content_hash`)
- [ ] Implementar `load()` com upsert batch via Supabase client
- [ ] Implementar cleanup job com soft-delete
- [ ] Registrar cleanup ARQ job em `backend/job_queue.py`
- [ ] Adicionar métricas Prometheus
- [ ] Criar `backend/tests/ingestion/external/test_loader.py`
- [ ] Atualizar crawlers EXT-003/004/005 para usar `ExternalBidLoader` (se implementados antes desta story)

---

## Referência de Implementação

- Upsert pattern Supabase: ver `backend/ingestion/loader.py` (função `upsert_pncp_raw_bids` — batch 500 rows via RPC)
- Supabase client: `from backend.supabase_client import get_supabase` (authenticated service_role)
- ARQ cron job cleanup: ver `backend/cron_jobs.py` — pattern similar ao `cleanup_search_cache_job`

---

## Riscos

- **R1 (Médio):** `normalize_objeto` pode colidir textos que são objetos diferentes mas com palavras similares (ex: "aquisição computadores" vs "aquisição computadores portáteis"). Mitigação: `cnpj_orgao` no hash diferencia — mesmo objeto em órgãos diferentes = hashes diferentes.
- **R2 (Baixo):** Upsert cross-source com `content_hash` pode silenciosamente descartar um registro de fonte mais confiável se o source_priority check falhar por race condition. Nível de risco aceitável para MVP.

---

## Dependências

- **EXT-001** — tabela `external_bids` com constraints UNIQUE já criadas
- Supabase service_role key configurada em `.env` (já existe)

---

## Arquivos Relevantes

| Arquivo | Ação |
|---------|------|
| `backend/ingestion/external/loader.py` | Criar |
| `backend/job_queue.py` | Atualizar (cleanup job) |
| `backend/metrics.py` | Atualizar |
| `backend/tests/ingestion/external/test_loader.py` | Criar |

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-23 | @sm | Story criada — EPIC-EXT-001 |
| 2026-04-23 | @po | Validação 10-pontos: **9/10 → GO** — normalização bem especificada, dedup logic clara. Status: Draft → Ready |
