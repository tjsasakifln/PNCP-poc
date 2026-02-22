# CRIT-FLT-006 — Synonym Dedup Força LLM Calls Desnecessárias

**Prioridade:** P2 — Custo LLM + Latência
**Estimativa:** 2h
**Origem:** Auditoria de Pipeline 2026-02-22
**Track:** Backend

## Problema

O synonym matching deduplica matches por keyword canônica. Múltiplos sinônimos da mesma keyword contam como **1 match**, mas o auto-approval exige **2+ matches**.

### Cenário
```
Objeto: "Aquisição de fardamento e indumentária profissional para servidores"
Setor: vestuario

Sinônimos matchados:
  - "fardamento" → canônica "uniforme" (match 1)
  - "indumentária" → canônica "uniforme" (match 2, mas MESMO canônico)

Resultado: 1 match canônico (não 2)
→ NÃO auto-aprova (precisa 2+)
→ Envia para LLM (custo + latência desnecessários)
```

### Contraste com o Esperado
O bid claramente é sobre vestuário (2 termos sinônimos distintos presentes). O LLM vai aprovar com 95%+ de confiança, mas gastamos uma chamada API desnecessária.

## Acceptance Criteria

- [x] **AC1:** No `synonyms.py`, contar matches por **sinônimo distinto** (não por keyword canônica). Se 2+ sinônimos distintos matcham (mesmo que da mesma canônica) → auto-approve
- [x] **AC2:** Manter log de sinônimos matchados para auditoria: `{synonym_matches: ["fardamento→uniforme", "indumentária→uniforme"]}`
- [x] **AC3:** Adicionar stat `synonyms_auto_approved` ao filter stats
- [x] **AC4:** Testes unitários: 2 sinônimos do mesmo canônico = auto-approve; 1 sinônimo = LLM
- [x] **AC5:** Documentar a mudança de lógica no docstring de `find_synonym_matches()`

## Impacto

- **Economia:** ~5-15% de chamadas LLM economizadas por busca
- **Latência:** -200-400ms por bid que seria enviado ao LLM
- **Risco de regressão:** BAIXO (apenas muda threshold de auto-approve, não de reject)

## Arquivos

- `backend/synonyms.py` (lógica de dedup)
- `backend/filter.py` (integração com synonym results)
- `backend/tests/test_synonyms.py`
