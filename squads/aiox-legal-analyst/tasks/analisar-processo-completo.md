# Task: Analisar Processo Completo

**Task ID:** analisar-processo-completo
**Versao:** 1.0
**Agente:** legal-chief
**Squad:** legal-analyst

## Proposito
Pipeline completo de analise processual: da triagem a entrega. Produz documento altamente tecnico, fundamentado em jurisprudencia e precedentes, com amplo fundamento juridico.

## Inputs
| Parametro | Tipo | Obrigatorio | Descricao |
|-----------|------|-------------|-----------|
| tema | string | Sim | Tema ou descricao do processo |
| pdf_path | string | Nao | Caminho para PDF do processo |
| objetivo | string | Nao | Objetivo especifico |
| tribunal | string | Nao | Tribunal alvo |

## Etapas

### Fase 0: Triagem
- @barbosa-classifier: Classificacao TPU/SGT
- @fux-procedural: Verificacao de admissibilidade
- @cnj-compliance: Carga de Resolucoes CNJ

### Fase 1: Pesquisa Jurisprudencial
- @mendes-researcher: Pesquisa STF/STJ/TJs
- @toffoli-aggregator: Consolidacao de precedentes
- @moraes-analyst: Direitos fundamentais (se aplicavel)
- @weber-indexer: Indexacao tematica

### Fase 2: Analise (PARALELA)
- @barroso-strategist: Linhas argumentativas
- @fachin-precedent: Ratio decidendi / distinguishing
- @nunes-quantitative: Jurimetria
- @carmem-relator: Perfil de Relatores

### Fase 3: Fundamentacao
- @barroso-strategist: Construcao da fundamentacao (CPC Art. 489)
- @fachin-precedent: Qualificacao de citacoes

### Fase 4: Validacao
- @theodoro-validator: Teoria Geral do Processo
- @marinoni-quality: Qualidade de precedentes
- @cnj-compliance: Conformidade CNJ
- @datajud-formatter: DATAJUD schema

### Fase 5: Entrega
- @legal-chief: Montagem final
- @datajud-formatter: Formatacao JUSBRASIL

## Output
- **Localizacao:** `output/legal/{processo}/`
- **Conteudo:**
  - `relatorio-executivo.md` — Resumo executivo
  - `classificacao-processual.md` — Classificacao TPU/DATAJUD
  - `mapa-jurisprudencia.md` — Precedentes e sumulas
  - `perfil-relatores.md` — Tendencias dos Relatores
  - `jurimetria.md` — Dados estatisticos
  - `fundamentacao.md` — Fundamentacao tecnica completa
  - `estrategia.md` — Estrategia argumentativa
  - `conformidade-cnj.md` — Relatorio de conformidade
  - `dados-datajud.yaml` — Dados estruturados DATAJUD

## Criterios de Conclusao
- [ ] Todas as 6 fases executadas
- [ ] Todos os quality gates aprovados
- [ ] Fundamentacao atende CPC Art. 489 par. 1o
- [ ] Conformidade CNJ verificada
- [ ] Dados formatados DATAJUD
- [ ] Relatorio final entregue
