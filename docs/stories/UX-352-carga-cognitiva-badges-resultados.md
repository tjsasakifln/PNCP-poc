# UX-352 — Reduzir Carga Cognitiva: Badges, Alertas e Hierarquia Visual

**Status:** pending
**Priority:** P2 — Polish pre-GTM
**Created:** 2026-02-22
**Origin:** Auditoria UX area logada (2026-02-22-ux-audit-area-logada.md)
**Dependencias:** UX-348 (viabilidade precisa estar ligada primeiro)
**Estimativa:** M

---

## Problema

### Badges que poluem sem agregar
- **"Palavra-chave"**: Jargao tecnico interno. Usuario nao sabe o que significa.
- **"FONTE OFICIAL"**: Todas as fontes sao oficiais (PNCP, ComprasGov). E como restaurante dizer "comida de verdade".
- **"Alta-confianca"** (sem cedilha): Conceito vago para o usuario. Confianca de que?

### Dobra de resultados = enxurrada cognitiva
Quando resultados carregam, TUDO aparece simultaneamente: summary card + badges + alertas urgentes + metadata + fontes + timestamp + LLM source. Sem agrupamento, sem legendas, sem hierarquia visual. Carga cognitiva extrema.

### Detalhes tecnicos expostos
- "Ultimos 10 dias" — detalhe de implementacao, nao informacao util
- "Dados de cache" — jargao de desenvolvedor
- "302 resultados eliminados" — numero tecnico sem contexto

---

## Solucao

### Criterios de Aceitacao

**Badges**
- [ ] **AC1:** Remover badge "FONTE OFICIAL" (redundante — todas sao oficiais)
- [ ] **AC2:** Remover badge "Palavra-chave" (jargao interno)
- [ ] **AC3:** "Alta-confianca" → "Alta relevancia" (com cedilha correta: "Alta relevancia")
- [ ] **AC4:** Manter badges que AGREGAM: viabilidade (Alta/Media/Baixa) e prazo (dias restantes com cor)

**Hierarquia visual da dobra de resultados**
- [ ] **AC5:** Summary hero card primeiro (resumo executivo + valor total + contagem de oportunidades)
- [ ] **AC6:** Separacao clara entre summary e lista de oportunidades (divider visual ou espaco)
- [ ] **AC7:** Lista de oportunidades com cards que tem informacao ESSENCIAL visivel: titulo, valor, UF, prazo, viabilidade
- [ ] **AC8:** Detalhes adicionais em expansao/collapse por card (nao tudo visivel de uma vez)

**Remover jargao tecnico**
- [ ] **AC9:** "Ultimos 10 dias" → remover ou substituir por "Oportunidades recentes"
- [ ] **AC10:** "Dados de cache" → "Atualizado em [hora]" ou remover
- [ ] **AC11:** Adicionar convite: "Novas oportunidades sao publicadas diariamente. Volte amanha para conferir."
- [ ] **AC12:** "302 resultados eliminados" → ja tratado em UX-348 AC7 (framing positivo)

**Testes**
- [ ] **AC13:** Teste: badges "FONTE OFICIAL" e "Palavra-chave" nao renderizam
- [ ] **AC14:** Teste: relevancia badge com acentuacao correta
- [ ] **AC15:** Zero regressoes

---

## Arquivos Envolvidos

| Arquivo | Mudanca |
|---------|---------|
| `frontend/app/buscar/components/ReliabilityBadge.tsx` | AC3 renomear |
| `frontend/app/buscar/components/LlmSourceBadge.tsx` | AC1-AC2 remover badges |
| `frontend/app/buscar/components/SearchResults.tsx` | AC5-AC12 hierarquia + remover jargao |
| `frontend/app/buscar/components/CacheBanner.tsx` | AC10 ajustar texto |
| `frontend/__tests__/` | Testes AC13-AC15 |

---

## Wireframe (antes/depois)

### ANTES (atual)
```
[ALERTA URGENTE] [ALERTA] [ALERTA]
[Badge: FONTE OFICIAL] [Badge: Palavra-chave] [Badge: Alta-confianca]
[Summary Card com LLM badge + resumo + valor + metricas]
[Banner: Ultimos 10 dias] [Banner: Dados de cache]
[302 resultados eliminados]
[Resultado 1 - tudo expandido]
[Resultado 2 - tudo expandido]
...
```

### DEPOIS (proposto)
```
+------------------------------------------+
| RESUMO                                    |
| X oportunidades selecionadas              |
| Valor total: R$ XXX | Y estados           |
+------------------------------------------+

  Resultado 1                [Alta viab.] [15 dias]
  Pregao Eletronico — Titulo...
  R$ 380.000 | SP | Ver edital >
  [v Expandir detalhes]

  Resultado 2                [Media viab.] [8 dias]
  ...

[Volte amanha para novas oportunidades]
```

---

## Referencias

- Audit: H02, H04, H05
- UX-348: Framing positivo (dependencia)
