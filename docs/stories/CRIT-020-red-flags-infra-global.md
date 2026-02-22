# CRIT-020 — RED_FLAGS_INFRASTRUCTURE Aplicado Globalmente Mata Setores de Engenharia

**Tipo:** Bug Critico / Falso Negativo em Massa
**Prioridade:** P0 (Setor engenharia efetivamente morto em producao)
**Criada:** 2026-02-22
**Status:** Concluida
**Origem:** Investigacao P0 — busca de engenharia retornando 0 resultados
**Dependencias:** CRIT-019 (setor precisa ser passado para solucao ser completa)
**Estimativa:** S (condicional por setor + testes)

---

## Problema

O conjunto `RED_FLAGS_INFRASTRUCTURE` em `filter.py:649-652` contem 8 termos:

```python
RED_FLAGS_INFRASTRUCTURE: Set[str] = {
    "pavimentacao", "drenagem", "saneamento", "terraplanagem",
    "recapeamento", "asfalto", "esgoto", "bueiro",
}
```

Estes termos foram projetados para proteger o setor **vestuario** de falsos positivos — quando keywords de roupa aparecem em contexto de infraestrutura.

**O problema:** O check `has_red_flags()` em `filter.py:2700-2732` e aplicado a **TODOS os setores**, incluindo engenharia, onde estes termos sao as **keywords primarias do setor**.

### Cadeia de Destruicao

1. PNCP retorna: *"Pavimentacao asfaltica e drenagem pluvial na BR-101"*
2. Keywords batem: "pavimentacao", "drenagem", "asfalto"
3. Densidade cai na zona 1-5% (descricao verbosa tipica de obras)
4. `has_red_flags()` encontra 3 termos de RED_FLAGS_INFRASTRUCTURE (threshold=2)
5. Bid rejeitada silenciosamente (`stats["rejeitadas_red_flags"] += 1`)
6. **Nunca chega ao LLM arbiter**

### Setores Diretamente Afetados

| Setor | Severidade | Motivo |
|---|---|---|
| `engenharia` | FATAL | Termos primarios = red flags |
| `engenharia_rodoviaria` | FATAL | 100% infraestrutura |
| `manutencao_predial` | SEVERO | "drenagem", "saneamento" frequentes |
| `materiais_hidraulicos` | ALTO | "saneamento", "esgoto", "drenagem" sao core |

### Evidencia no Codigo

- **Definicao:** `filter.py:649-652` — `RED_FLAGS_INFRASTRUCTURE`
- **has_red_flags():** `filter.py:655-679` — threshold=2, retorna True se 2+ matches de qualquer set
- **Aplicacao (zona 2-5%):** `filter.py:2700-2713` — `if flagged: continue` (silently skip)
- **Aplicacao (zona 1-2%):** `filter.py:2720-2732` — mesma logica

---

## Solucao

### Opcoes (PM deve escolher)

**Opcao A (Recomendada): Exemption por setor**
- Nao aplicar `RED_FLAGS_INFRASTRUCTURE` quando `setor` pertence a um conjunto de setores de infra
- Set de exemption: `{"engenharia", "engenharia_rodoviaria", "manutencao_predial", "materiais_hidraulicos"}`
- Complexidade: XS. Risco: baixo.

**Opcao B: Red flags por setor em sectors_data.yaml**
- Mover definicao de red flags para YAML, cada setor define seus proprios
- Complexidade: M. Risco: medio (precisa migrar vestuario/informatica/saude).

**Opcao C: Inverter logica — red flags como "bonus" para setores relacionados**
- Se o setor e infra E tem red flags infra, BOOST ao inves de penalizar
- Complexidade: M. Risco: alto (muda semantica).

### Criterios de Aceitacao

- [x] **AC1:** Busca por `engenharia` em qualquer UF retorna resultados quando PNCP tem dados
- [x] **AC2:** Bids com "pavimentacao" + "drenagem" no objeto NAO sao rejeitadas quando setor=engenharia
- [x] **AC3:** Bids com "pavimentacao" + "drenagem" + keyword de vestuario CONTINUAM sendo rejeitadas para setor=vestuario
- [x] **AC4:** `has_red_flags()` recebe parametro `setor` para decidir quais sets aplicar
- [x] **AC5:** Teste unitario com bid tipica de engenharia (contendo termos de infra) passa pelo filtro
- [x] **AC6:** Teste de regressao — vestuario continua protegido contra falsos positivos de infra
- [x] **AC7:** Log/metrica de `rejeitadas_red_flags` cai drasticamente para setor=engenharia em producao

### Verificacao Pos-Deploy

- [ ] Busca "engenharia" em 5+ UFs retorna > 0 resultados
- [ ] Busca "vestuario" com bid de infraestrutura e corretamente rejeitada
- [ ] Metricas `rejeitadas_red_flags` por setor mostram distribuicao saudavel

---

## Arquivos Envolvidos

| Arquivo | Mudanca |
|---|---|
| `backend/filter.py` | L649-679 (has_red_flags), L2700-2732 (aplicacao) — `setor` param + exemption sets |
| `backend/tests/test_red_flag_exemptions.py` | 35 testes: infra exemptions, vestuario protection, medical exemptions |

---

## Notas de Implementacao

- O `setor` param precisa chegar ate `has_red_flags()`. Hoje a funcao nao recebe setor.
- **Depende de CRIT-019** para que `setor` chegue a `aplicar_todos_filtros()`.
- Existem 3 sets de red flags: `RED_FLAGS_MEDICAL`, `RED_FLAGS_ADMINISTRATIVE`, `RED_FLAGS_INFRASTRUCTURE`
- Considerar tambem exemptions de `RED_FLAGS_MEDICAL` para setor=saude e `RED_FLAGS_ADMINISTRATIVE` para setores de consultoria
- Threshold e 2 (`has_red_flags(..., threshold=2)` L659)
