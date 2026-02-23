# CRIT-035 — LLM Arbiter: Strip de Prefixo "Objeto:" em Evidências

**Status:** Done
**Priority:** P2 — Important
**Severity:** Funcional (recall potencialmente reduzido)
**Created:** 2026-02-23
**Relates to:** CRIT-022 (Evidence Validation Normalization — concluído)

---

## Problema

GPT-4.1-nano sistematicamente adiciona o prefixo `Objeto:` às evidências retornadas, causando falha na validação de substring (D-02 AC6). A evidência é descartada como "alucinação" quando o conteúdo real está correto — apenas o prefixo é inventado.

### Padrão Observado (Railway Logs 2026-02-23)

```log
D-02 AC6: Discarding hallucinated evidence (not substring):
  evidence='Objeto: Registro de preços para aquisição de materiais de higiene e limpeza'
  not found in objeto

D-02 AC6: Discarding hallucinated evidence (not substring):
  evidence='Objeto: Registro de Preços para Aquisição de Gêneros Alimentícios Não Perecíveis'
  not found in objeto

D-02 AC6: Discarding hallucinated evidence (not substring):
  evidence='Objeto: [LICITANET] - Registro de Preços para futura e eventual aquisição de kits de lanches'
  not found in objeto

D-02 AC6: Discarding hallucinated evidence (not substring):
  evidence='Objeto: Registro de Preços para eventual Aquisição de Materiais de Construção - I'
  not found in objeto

D-02 AC6: Discarding hallucinated evidence (not substring):
  evidence='conforme demandas da Administração'
  not found in objeto
```

### Tipos de Prefixo Identificados

| Prefixo | Frequência | Ação |
|---------|-----------|------|
| `Objeto: ` | Alta | Strip |
| `Objeto:` (sem espaço) | Média | Strip |
| `OBJETO: ` | Baixa | Strip (case-insensitive) |
| Frases genéricas (`conforme demandas...`) | Baixa | Manter rejeição (alucinação real) |

### Diferença com CRIT-022

CRIT-022 tratou normalização de **acentos e whitespace**. Este bug é sobre **prefixo de campo JSON** que o LLM adiciona ao copiar texto do contexto.

```
CRIT-022: "serviços" vs "servicos" → normalização de caracteres ✓ RESOLVIDO
CRIT-035: "Objeto: Registro..." vs "Registro..." → prefixo de campo ✗ NOVO
```

## Impacto

| Cenário | Decisão Atual | Decisão Correta |
|---------|--------------|-----------------|
| Vestuário + "Gêneros Alimentícios" | NAO (evidence descartada) | NAO (rejeitaria de qualquer forma) |
| Saúde + evidência médica válida | NAO conf=0% (evidence descartada) | Potencialmente SIM (evidence confirmaria) |
| Qualquer setor + evidence com prefixo | conf reduzida | conf mantida |

**Risco:** Itens relevantes perdem a evidência de suporte, resultando em `conf=0%` quando poderiam ter `conf>0%` e passar o threshold de aceitação.

## Acceptance Criteria

- [x] **AC1**: Em `llm_arbiter.py`, antes do substring check, strip prefixos comuns: `Objeto:`, `Descrição:`, `Título:`
- [x] **AC2**: Strip case-insensitive e com/sem espaço após `:`
- [x] **AC3**: Log quando strip é aplicado: `"Evidence prefix stripped: 'Objeto:' → checking cleaned evidence"`
- [x] **AC4**: Métrica: `filter_evidence_prefix_stripped_total` (counter)
- [x] **AC5**: Test: evidence com `Objeto: texto real` → match encontrado após strip
- [x] **AC6**: Test: evidence com `texto realmente alucinado` → continua sendo descartada
- [x] **AC7**: Test: evidence sem prefixo → comportamento inalterado (zero regression)

## Solução Proposta

```python
# Em llm_arbiter.py, antes do substring check
KNOWN_PREFIXES = ["objeto:", "descrição:", "descrição:", "título:", "title:"]

def _strip_evidence_prefix(evidence: str) -> str:
    """Strip common field-name prefixes that GPT adds to evidence."""
    ev_lower = evidence.strip().lower()
    for prefix in KNOWN_PREFIXES:
        if ev_lower.startswith(prefix):
            stripped = evidence.strip()[len(prefix):].strip()
            logger.debug(f"Evidence prefix stripped: '{prefix}' → checking cleaned evidence")
            return stripped
    return evidence
```

## Files Envolvidos

- `backend/llm_arbiter.py` — Evidence validation (~line 312-330)
- `backend/tests/test_llm_arbiter.py` — Evidence strip tests
