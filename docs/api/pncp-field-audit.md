# PNCP API Field Audit

**Date:** 2026-02-22
**Sample:** 200 items from Pregão Eletrônico (modalidade 6), various UFs
**Story:** CRIT-FLT-008

## Field Presence Summary

### Always Present (100%)

| Field | Type | Notes |
|-------|------|-------|
| `objetoCompra` | string | Main procurement description |
| `valorTotalEstimado` | number | Always present, but **25% have R$ 0.00** (CRIT-FLT-003) |
| `dataPublicacaoPncp` | string | ISO datetime |
| `dataAberturaProposta` | string | ISO datetime |
| `dataEncerramentoProposta` | string | ISO datetime |
| `situacaoCompraNome` | string | **99.5% = "Divulgada no PNCP"** (see Dead Fields) |
| `srp` | boolean | 38% true, 62% false |
| `orgaoEntidade` | object | Contains `razaoSocial`, `cnpj` |
| `unidadeOrgao` | object | Contains `ufSigla`, `municipioNome`, `nomeUnidade` |
| `codigoModalidadeContratacao` | integer | Modality code (1-15) |
| `numeroControlePNCP` | string | Format: `{CNPJ}-{TIPO}-{SEQ}/{ANO}` |

### Sometimes Present

| Field | Presence | Notes |
|-------|----------|-------|
| `linkSistemaOrigem` | **86%** | Primary link to source system. Our main URL for "Ver na fonte". |
| `informacaoComplementar` | 59% | Additional text, useful for keyword matching |
| `valorTotalHomologado` | 2% | Only 4/200 items. Not reliable as value fallback. |

### Dead Fields (0% — Never Populated)

| Field | Presence | Status |
|-------|----------|--------|
| `linkProcessoEletronico` | **0%** | **DEAD.** Never populated in any sampled record. |
| `situacaoCompraNome` (effective) | 0% useful | 99.5% = "Divulgada no PNCP" — functionally useless for status inference. |

## API Contract Changes (Detected 2026-02-22)

### 1. `codigoModalidadeContratacao` Now Required

- **Before:** Optional — could search across all modalities
- **Now:** **Required** — omitting returns HTTP 400
- **Impact:** Our code already sends it (one call per modality). Guard added in CRIT-FLT-008 AC1.
- **Smoke test:** `scripts/pncp_api_smoke_test.py` verifies this weekly

### 2. `tamanhoPagina` Max = 50

- **Before:** Allowed up to 500
- **Now:** Max 50 — values >50 return HTTP 400
- **Impact:** Addressed in GTM-FIX-031. All calls use `tamanhoPagina=50`.

## Link Field Strategy

```
Priority chain for bid URLs:
  1. linkSistemaOrigem (86% populated) — real URL to source system
  2. linkProcessoEletronico (0% — dead) — kept as defensive fallback
  3. Constructed URL from numeroControlePNCP → pncp.gov.br/app/editais/{CNPJ}/{ANO}/{SEQ}
```

## Status Inference Strategy

Since `situacaoCompraNome` is always "Divulgada no PNCP" (useless), we infer status from dates:

```python
# Implemented in status_inference.py:enriquecer_com_status_inferido()
if dataAberturaProposta > now:       → "Aguardando abertura"
elif dataEncerramentoProposta > now:  → "Recebendo propostas"
elif dataEncerramentoProposta < now:  → "Encerrada"
```

## Monitoring

- **Weekly smoke test:** `python scripts/pncp_api_smoke_test.py`
- **Alerts on:** Missing required fields, dead fields becoming alive, new unknown fields
- **Health canary:** `AsyncPNCPClient.health_canary()` — runs before every search

## Recommendations

1. **Do NOT rely on `linkProcessoEletronico`** — it has been 0% for the entire sample
2. **Do NOT use `valorTotalHomologado`** as value fallback — only 2% populated
3. **Do NOT use `situacaoCompraNome`** for status — infer from dates instead
4. **Always send `codigoModalidadeContratacao`** — API returns 400 without it
5. **Always use `tamanhoPagina <= 50`** — API returns 400 for larger values
