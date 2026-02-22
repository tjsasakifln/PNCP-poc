# CRIT-022 — Evidence Validation no LLM Arbiter Descarta Evidencias Validas (Normalizacao)

**Tipo:** Bug / Auditabilidade
**Prioridade:** P1 (Nao afeta recall, afeta auditabilidade)
**Criada:** 2026-02-22
**Status:** Concluído
**Origem:** Investigacao P0 — warnings "Discarding hallucinated evidence (not substring)" nos logs
**Dependencias:** Nenhuma
**Estimativa:** XS (usar normalize_text() existente)

---

## Problema

A validacao de evidencias em `llm_arbiter.py:312-330` usa apenas `.lower()` para comparacao:

```python
objeto_lower = objeto.lower()           # lowercase, acentos PRESERVADOS
if ev.lower() in objeto_lower:          # substring check sem normalizar acentos
```

O LLM (GPT-4.1-nano) frequentemente retorna evidencias sem acentos ou com whitespace normalizado, gerando mismatch:

| `objeto` contem | LLM retorna | `.lower()` match? | Motivo |
|---|---|---|---|
| "servicos de engenharia" | "servicos de engenharia" | NAO | cedilha removida pelo LLM |
| "manutencao predial" | "manutencao predial" | NAO | til removido pelo LLM |
| "reforma  e  ampliacao" | "reforma e ampliacao" | NAO | double space normalizado |
| "ENGENHARIA - PROJETOS" | "ENGENHARIA PROJETOS" | NAO | hifen removido |

### Impacto

- **NAO afeta recall** — a decisao SIM/NAO e baseada em `classification.classe`, nao nas evidencias
- **Afeta auditabilidade** — decisoes "SIM conf=100%" aparecem com lista de evidencias vazia
- **Gera ruido nos logs** — centenas de warnings "Discarding hallucinated evidence" por busca
- **Impossibilita explicabilidade** — usuario nao tem como saber POR QUE a bid foi aprovada

### Solucao Existente no Codebase

`filter.py:585-628` ja tem `normalize_text()` que:
- Faz lowercase
- Remove acentos via NFD decomposition
- Remove pontuacao
- Normaliza whitespace

---

## Solucao

### Abordagem: Usar `normalize_text()` na comparacao de evidencias

### Criterios de Aceitacao

- [x] **AC1:** Evidence validation em `llm_arbiter.py:312-330` usa `normalize_text()` (importado de filter.py) ao inves de `.lower()`
- [x] **AC2:** Evidencia "servicos de engenharia" e aceita quando objeto contem "servicos de engenharia"
- [x] **AC3:** Evidencia "manutencao predial" e aceita quando objeto contem "manutencao predial"
- [x] **AC4:** Evidencia completamente inventada (sem relacao com objeto) continua sendo rejeitada
- [x] **AC5:** Teste unitario com 5+ cenarios de mismatch de acentos/whitespace
- [x] **AC6:** Warning log de "hallucinated evidence" cai drasticamente em producao

---

## Arquivos Envolvidos

| Arquivo | Mudanca |
|---|---|
| `backend/llm_arbiter.py` | L312-330 — importar e usar `normalize_text()` |
| `backend/tests/test_llm_arbiter.py` | Testes de evidence validation com acentos |

---

## Notas de Implementacao

- `normalize_text()` esta em `filter.py`. Considerar mover para `utils/` se criar dependencia circular.
- A comparacao deve ser: `normalize_text(ev) in normalize_text(objeto)`
- Manter o log de warning para evidencias REALMENTE inventadas (que falham mesmo apos normalizacao)
- Nao alterar o threshold de tamanho (`len(ev) <= 100`)
