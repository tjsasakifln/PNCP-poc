# Epic: Fontes Externas de Licitações (Beyond PNCP)

## Metadados
- **ID:** EPIC-EXT-001
- **Owner:** @architect + @pm
- **Status:** PLANNED
- **Prioridade:** Alta
- **Sprint:** EXT-sprint-01 a EXT-sprint-03
- **Data:** 2026-04-23
- **Fonte:** `docs/research/2026-04-23-fontes-externas-licitacoes.md`

---

## Problema

O PNCP (fonte primária do SmartLic) tem cobertura estruturalmente incompleta:

- **TCU 2025:** 86,4% dos atos publicados em portais credenciados não chegam ao PNCP
- **~3.000 municípios** com prazo legal até abril/2027 para aderir ao PNCP (Lei 14.133, Art. 176)
- PCP v2 e ComprasGov v3 (fontes atuais) cobrem sobreposição parcial mas não resolvem o gap municipal

Fontes identificadas com editais não cobertos pelo PNCP:
- **Querido Diário (OKBR):** API REST pública, ~350 municípios, texto não estruturado → LLM extrai campos
- **BNC (Bolsa Nacional de Compras):** 23 estados, 1.500+ órgãos, portal HTML público
- **IPM/Atende.Net:** 850+ municípios RS/SC/PR/MG, Vue.js portal com padrão URL identificado
- **ComprasGov histórico:** pre-2023 gap (antes da Lei 14.133), API REST pública

---

## Objetivo

Implementar pipeline de ingestão de fontes externas com:
1. **Descoberta** de URLs de editais em fontes fora do PNCP
2. **Extração estruturada** via Playwright + LLM (GPT-4.1-nano)
3. **Deduplicação** robusta (intra-fonte e cross-fonte)
4. **Integração gradual** no search pipeline via feature flag

---

## Arquitetura

```
Tier A (Descoberta)              Tier B (Extração)           Supabase
─────────────────────────        ────────────────────────    ──────────────────
Querido Diário API        ──→    PlaywrightExtractor  ──→   external_bids
BNC portal scraping       ──→    LLM extrai campos    ──→   (deduped)
IPM/Atende.Net            ──→    PDF parser           ──→
                                                            ↓
                                                       Search Pipeline
                                                       (fallback layer)
```

**Dedup strategy:**
- Intra-fonte: `UNIQUE(source_name, external_id)`
- Cross-fonte: `content_hash = SHA256(objeto_norm + cnpj_orgao + data_publicacao)`
- Hierarquia: `source_priority` determina qual versão manter (menor = mais confiável)

---

## Stories

| ID | Título | Complexidade | Dependência | Sprint |
|----|--------|--------------|-------------|--------|
| EXT-001 | Schema `external_bids` — Fundação Supabase | M | — | 1 |
| EXT-002 | Playwright Extractor Engine | M | EXT-001 | 1 |
| EXT-003 | Crawler Querido Diário | M | EXT-001, EXT-002 | 2 |
| EXT-004 | Crawler BNC | M | EXT-001, EXT-002 | 2 |
| EXT-005 | Crawler IPM/Atende.Net | L | EXT-001, EXT-002 | 2 |
| EXT-006 | Loader + Dedup Pipeline | M | EXT-001 | 2 |
| EXT-007 | Integração no Search Pipeline | M | EXT-001, EXT-006 | 3 |

---

## Critérios de Sucesso

| Métrica | Meta |
|---------|------|
| Editais novos por dia (Querido Diário) | ≥ 50 |
| Editais novos por dia (BNC) | ≥ 200 |
| Editais novos por dia (IPM) | ≥ 100 |
| Taxa de dedup cross-fonte (duplicatas eliminadas) | ≥ 85% |
| Latência search com external_bids | ≤ +3s (timeout guarda) |
| Downtime do pipeline existente por deploy | 0 |

---

## Riscos

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| BNC/IPM introduzem CAPTCHA | Alto | Playwright stealth mode + fallback para Querido Diário |
| Querido Diário baixa cobertura (<350 municípios relevantes) | Médio | Priorizar municípios de interesse de clientes do SmartLic |
| LLM extraction campos ausentes | Médio | Pydantic validation com campos mínimos obrigatórios |
| ToS / robots.txt de BNC/IPM | Crítico | Verificar ANTES do deploy; User-Agent identificador obrigatório |
| Mudança de estrutura HTML sem aviso | Alto | Structural hash detection + Sentry alerts |
| Playwright consumer de memória em worker Railway | Médio | Pool de browsers limitado (max 3 concurrent) |

---

## Fora de Escopo

- Scraping de Licitanet (CAPTCHA confirmado — fase futura)
- Betha Sistemas (URL patterns não identificados — investigação pendente)
- DOM/SC completo (apenas Querido Diário cobre municípios SC para MVP)
- ComprasGov histórico API (pre-2023) — fase futura P3

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-23 | @sm | Epic criado a partir de pesquisa aiox-deep-research |
