# Analista Processual Squad — Base de Conhecimento

> Referencia completa: missao, arquitetura, frameworks, conformidade CNJ, pipeline de agentes.

---

## Missao e Filosofia

**O que fazemos:** Analise processual sistematica baseada em jurisprudencia, precedentes judiciais, diretrizes do CNJ, projeto DATAJUD, com organizacao estilo JUSBRASIL.

**Filosofia Central:**
- **JURISPRUDENCIA > OPINIAO** — Toda analise fundamentada em julgados reais
- **CNJ-COMPLIANT** — Resolucoes do CNJ integradas ao pipeline
- **DATAJUD-FIRST** — Estrutura de dados alinhada ao DATAJUD
- **RELATOR-AWARE** — Posicionamento do Relator mapeado e considerado
- **PRECEDENTE E LEI** — Sistema de precedentes do CPC (Art. 926-928)

---

## Pipeline de Agentes

### Fase 0: Triagem
- @barbosa-classifier — Classificacao TPU/SGT
- @fux-procedural — Admissibilidade
- @cnj-compliance — Conformidade CNJ

### Fase 1: Pesquisa
- @mendes-researcher — Jurisprudencia constitucional/infraconstitucional
- @toffoli-aggregator — Consolidacao de precedentes
- @moraes-analyst — Direitos fundamentais
- @weber-indexer — Indexacao tematica

### Fase 2: Analise (Paralela)
- @barroso-strategist — Estrategia argumentativa
- @fachin-precedent — Ratio decidendi / distinguishing
- @nunes-quantitative — Jurimetria
- @carmem-relator — Perfil de Relatores

### Fase 3: Fundamentacao
- @barroso-strategist — Construcao CPC Art. 489
- @fachin-precedent — Qualificacao de citacoes

### Fase 4: Validacao
- @theodoro-validator — Teoria Geral do Processo
- @marinoni-quality — Stare decisis
- @cnj-compliance — Conformidade final
- @datajud-formatter — DATAJUD schema

### Fase 5: Entrega
- @legal-chief — Montagem final
- @datajud-formatter — Formatacao JUSBRASIL

---

## Fundamentacao Legal

### CPC Art. 489 par. 1o — Requisitos de Fundamentacao

Nao se considera fundamentada qualquer decisao judicial, seja ela interlocutoria, sentenca ou acordao, que:

I — se limitar a indicacao, a reproducao ou a parafrases de ato normativo, sem explicar sua relacao com a causa ou a questao decidida;

II — empregar conceitos juridicos indeterminados, sem explicar o motivo concreto de sua incidencia no caso;

III — invocar motivos que se prestariam a justificar qualquer outra decisao;

IV — nao enfrentar todos os argumentos deduzidos no processo capazes de, em tese, infirmar a conclusao adotada pelo julgador;

V — se limitar a invocar precedente ou enunciado de sumula, sem identificar seus fundamentos determinantes nem demonstrar que o caso sob julgamento se ajusta aqueles fundamentos;

VI — deixar de seguir enunciado de sumula, jurisprudencia ou precedente invocado pela parte, sem demonstrar a existencia de distincao no caso em julgamento ou a superacao do entendimento.

### CPC Art. 926-928 — Sistema de Precedentes

**Art. 926.** Os tribunais devem uniformizar sua jurisprudencia e mante-la estavel, integra e coerente.

**Art. 927.** Os juizes e os tribunais observarao:
I — as decisoes do STF em controle concentrado de constitucionalidade;
II — os enunciados de sumula vinculante;
III — os acordaos em IRDR e IAC;
IV — os enunciados das sumulas do STF em materia constitucional e do STJ em materia infraconstitucional;
V — a orientacao do plenario ou do orgao especial aos quais estiverem vinculados.

**Art. 928.** Para os fins deste Codigo, considera-se julgamento de casos repetitivos a decisao proferida em:
I — IRDR;
II — recursos especial e extraordinario repetitivos.

---

## Resolucoes CNJ Integradas

| Resolucao | Tema | Ano | Impacto |
|-----------|------|-----|---------|
| 331/2020 | DATAJUD — Base Nacional de Dados | 2020 | Schema obrigatorio |
| 335/2020 | PDPJ — Plataforma Digital | 2020 | Integracao |
| 332/2020 | Etica e IA no Judiciario | 2020 | Limites de automacao |
| 396/2021 | TPU — Tabelas Processuais Unificadas | 2021 | Classificacao |
| 235/2016 | Padronizacao de dados | 2016 | Formato |
| 185/2013 | PJe — Processo Eletronico | 2013 | Integracao |

---

## Hierarquia de Precedentes

```
1. Sumulas Vinculantes (CF Art. 103-A)
   -> Vinculam TODOS os orgaos do Judiciario e Administracao Publica
   |
2. Decisoes em Controle Concentrado (ADI, ADC, ADPF)
   -> Eficacia erga omnes e efeito vinculante
   |
3. Temas de Repercussao Geral (STF)
   -> Vinculam instancias inferiores
   |
4. Recursos Repetitivos (STJ/STF)
   -> Vinculam TJs e TRFs
   |
5. IRDR / IAC
   -> Vinculam juizes do respectivo tribunal
   |
6. Sumulas do STF (materia constitucional)
   -> Persuasivas com forte peso
   |
7. Sumulas do STJ (materia infraconstitucional)
   -> Persuasivas com forte peso
   |
8. Jurisprudencia Dominante
   -> Persuasiva
   |
9. Decisoes Monocraticas
   -> Menor peso
```

---

## Estrutura de Tribunais Brasileiros

```
PODER JUDICIARIO
|
+-- Justica Comum
|   +-- STF (Supremo Tribunal Federal) — guardiao da CF
|   +-- STJ (Superior Tribunal de Justica) — uniformizador de lei federal
|   +-- TJs (Tribunais de Justica estaduais) — 27 TJs
|   +-- TRFs (Tribunais Regionais Federais) — 6 TRFs
|
+-- Justica Especializada
|   +-- TST (Tribunal Superior do Trabalho)
|   +-- TRTs (Tribunais Regionais do Trabalho) — 24 TRTs
|   +-- TSE (Tribunal Superior Eleitoral)
|   +-- TREs (Tribunais Regionais Eleitorais) — 27 TREs
|   +-- STM (Superior Tribunal Militar)
|
+-- CNJ (Conselho Nacional de Justica) — controle administrativo
```

---

## Glossario Juridico-Tecnico

| Termo | Definicao |
|-------|-----------|
| **Ratio decidendi** | Razao de decidir — fundamento determinante que vincula |
| **Obiter dictum** | Comentario incidental — nao vincula |
| **Distinguishing** | Tecnica de distincao de precedente (CPC Art. 489, par. 1o, VI) |
| **Overruling** | Superacao de precedente (CPC Art. 927, par. 2-4) |
| **IRDR** | Incidente de Resolucao de Demandas Repetitivas (CPC Art. 976-987) |
| **IAC** | Incidente de Assuncao de Competencia (CPC Art. 947) |
| **TPU** | Tabelas Processuais Unificadas do CNJ |
| **SGT** | Sistema de Gestao de Tabelas do CNJ |
| **DATAJUD** | Base Nacional de Dados do Poder Judiciario |
| **PJe** | Processo Judicial Eletronico |
| **PDPJ** | Plataforma Digital do Poder Judiciario |
| **Stare decisis** | Principio de respeito aos precedentes |
| **Jurimetria** | Aplicacao de metodos estatisticos ao Direito |
| **Erga omnes** | Eficacia contra todos |
| **Inter partes** | Eficacia apenas entre as partes |
| **Repercussao geral** | Requisito de admissibilidade do RE (CF Art. 102, par. 3o) |
| **Prequestionamento** | Debater materia no acordao para admissibilidade de RE/REsp |
