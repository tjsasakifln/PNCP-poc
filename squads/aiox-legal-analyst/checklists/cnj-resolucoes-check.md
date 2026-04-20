# Checklist: Conformidade com Resolucoes CNJ

**Versao:** 1.0
**Agente:** cnj-compliance
**Quando usar:** Fase 0 (carga) e Fase 4 (validacao final)
**Threshold de aprovacao:** 5/6 itens minimo

---

## Itens

- [ ] **Res. 331/2020 — DATAJUD** — Dados conforme schema DATAJUD | PASS: Campos obrigatorios preenchidos no formato correto
- [ ] **Res. 396/2021 — TPU** — Classificacao conforme Tabelas Processuais Unificadas | PASS: Classe e assuntos com codigos TPU validos
- [ ] **Res. 332/2020 — IA Etica** — Limites eticos de IA respeitados | PASS: Analise com supervisao humana prevista, transparencia
- [ ] **Res. 235/2016 — Padronizacao** — Dados padronizados conforme CNJ | PASS: Formato de datas, numeros, nomes conforme padrao
- [ ] **Res. 185/2013 — PJe** — Compativel com PJe (se aplicavel) | PASS: Formato compativel ou N/A
- [ ] **Numero CNJ** — Numero do processo no formato CNJ correto | PASS: NNNNNNN-DD.AAAA.J.TR.OOOO

## Condicoes de Veto
- Classificacao TPU ausente ou incorreta
- Dados fora do schema DATAJUD
- Violacao de limites eticos de IA (Res. 332/2020)

## Pontuacao
- **CONFORME:** 5/6 ou mais
- **PARCIAL:** 3-4/6
- **NAO CONFORME:** 2/6 ou menos
