# Analista Processual Squad

> Analise processual baseada em jurisprudencia, precedentes judiciais, diretrizes do CNJ, projeto DATAJUD, com estrutura de dados inspirada no JUSBRASIL.

**Version:** 1.0.0
**Status:** Production

---

## O Que Este Squad Faz

O Analista Processual Squad e um **sistema de analise juridica processual** que pesquisa, classifica e analisa processos judiciais aplicando rigorosamente as diretrizes do CNJ, jurisprudencias consolidadas e precedentes dos Relatores.

**Filosofia Central:**
- **JURISPRUDENCIA > OPINIAO** — Toda analise fundamentada em julgados reais e precedentes
- **CNJ-COMPLIANT** — Diretrizes do CNJ, Resolucoes e Recomendacoes integradas ao pipeline
- **DATAJUD-FIRST** — Estrutura de dados alinhada ao projeto DATAJUD do CNJ
- **JUSBRASIL-INSPIRED** — Organizacao e navegabilidade de dados semelhante ao JUSBRASIL
- **RELATOR-AWARE** — Analise de tendencias e posicionamentos dos Ministros Relatores

**Nao e apenas busca de jurisprudencia.** Este squad aplica 14 agentes especializados em um pipeline sistematico para garantir analise processual completa e fundamentada.

---

## Arquitetura

```
+-------------------------------------------------------------+
|  CAMADA 1: MOTOR PERMANENTE (frameworks juridicos)           |
|  +-- CNJ Resolucoes, DATAJUD Schema, CPC/CPP               |
|  +-- Taxonomia de Classes/Assuntos (TPU/SGT)               |
|  +-- Checklists de conformidade (12 total)                  |
|  +-- Templates (10 YAML)                                     |
+-------------------------------------------------------------+
|  CAMADA 2: DOMINIO VARIAVEL (por caso/processo)              |
|  +-- Area do Direito (Civil, Penal, Trabalhista, etc.)      |
|  +-- Tribunal/Instancia (STF, STJ, TJ, TRF, TRT, TST)     |
|  +-- Relator(es) relevante(s)                               |
|  +-- Contexto processual (partes, pedidos, causa de pedir)  |
+-------------------------------------------------------------+

PIPELINE: Triagem -> Pesquisa -> Analise -> Fundamentacao -> Validacao -> Entrega
```

**Design em duas camadas:** Motor juridico permanente (Camada 1) + dominio processual variavel (Camada 2) = excelencia consistente em qualquer ramo do Direito.

---

## Agentes (14 Total)

### Tier 0: Triagem e Classificacao (3 agentes)

| Agente | Mente | Funcao | Framework Principal |
|--------|-------|--------|---------------------|
| **@barbosa-classifier** | Min. Joaquim Barbosa | Classificacao processual e triagem | TPU/SGT CNJ + DATAJUD Schema |
| **@fux-procedural** | Min. Luiz Fux | Analise de requisitos processuais e admissibilidade | CPC/CPP + Regimentos Internos |
| **@cnj-compliance** | CNJ/DATAJUD | Conformidade com resolucoes CNJ e padrao DATAJUD | Resolucoes CNJ + DATAJUD API |

### Tier 1: Pesquisa Jurisprudencial (4 agentes)

| Agente | Mente | Funcao | Framework Principal |
|--------|-------|--------|---------------------|
| **@mendes-researcher** | Min. Gilmar Mendes | Pesquisa de jurisprudencia constitucional | Controle de Constitucionalidade |
| **@toffoli-aggregator** | Min. Dias Toffoli | Agregacao e consolidacao de jurisprudencia | IRDR/IAC + Precedentes Vinculantes |
| **@moraes-analyst** | Min. Alexandre de Moraes | Analise de direitos fundamentais e garantias | CF/88 + Tratados Internacionais |
| **@weber-indexer** | Min. Rosa Weber | Indexacao e categorizacao tematica | Tesauro Juridico + TPU |

### Tier 2: Analise de Relatores e Precedentes (4 agentes)

| Agente | Mente | Funcao | Framework Principal |
|--------|-------|--------|---------------------|
| **@barroso-strategist** | Min. Luis Roberto Barroso | Estrategia argumentativa e ponderacao | Proporcionalidade + Ponderacao |
| **@fachin-precedent** | Min. Edson Fachin | Analise de precedentes e distinguishing | CPC Art. 489 + Overruling |
| **@nunes-quantitative** | Min. Ricardo Lewandowski | Analise quantitativa de julgados | Estatistica Jurimetrica |
| **@carmem-relator** | Min. Carmen Lucia | Perfil e tendencia de Relatores | Analise de Votos + Divergencias |

### Tier 3: Validacao e Entrega (3 agentes)

| Agente | Mente | Funcao | Framework Principal |
|--------|-------|--------|---------------------|
| **@theodoro-validator** | Humberto Theodoro Jr. | Validacao de fundamentacao processual | Teoria Geral do Processo |
| **@marinoni-quality** | Luiz Guilherme Marinoni | Controle de qualidade de precedentes | Stare Decisis Brasileiro |
| **@datajud-formatter** | DATAJUD/JUSBRASIL | Formatacao e estruturacao de dados | DATAJUD Schema + JUSBRASIL UX |

### Orquestrador

| Agente | Funcao | Frameworks |
|--------|--------|------------|
| **@legal-chief** | Orquestracao do pipeline, quality gates, conformidade CNJ | Todos os 13 frameworks |

---

## Quick Start

### Analise Processual Completa (Recomendado)

```bash
/legal-analyst
*analisar-processo "Responsabilidade civil por danos morais em relacoes de consumo"
```

**Processo:**
1. Ativa @legal-chief
2. Classifica area do direito e tribunal competente
3. Executa pipeline de 6 fases (Triagem -> Pesquisa -> Analise -> Fundamentacao -> Validacao -> Entrega)
4. Produz relatorio completo + mapa de jurisprudencia

---

### Pesquisar Jurisprudencia

```bash
/legal-analyst
*pesquisar-jurisprudencia "Dano moral coletivo ambiental" --tribunal=STJ
```

**Agentes:** @mendes-researcher + @toffoli-aggregator + @weber-indexer

**Output:** Mapa de jurisprudencia com precedentes, Relatores, tendencias

---

### Analisar Relator

```bash
/legal-analyst
*analisar-relator "Min. Luis Roberto Barroso" --tema="liberdade de expressao"
```

**Agente:** @carmem-relator

**Output:** Perfil do Relator, tendencias de voto, divergencias, historico

---

### Validar Fundamentacao

```bash
/legal-analyst
*validar-fundamentacao output/legal/{caso}/fundamentacao.md
```

**Processo:**
- Executa 8 checklists de conformidade juridica
- Executa 4 checklists CNJ/DATAJUD
- Gera relatorio de qualidade com scores e recomendacoes

---

## Comandos Disponiveis

### Workflows Principais

| Comando | Descricao | Duracao |
|---------|-----------|---------|
| `*analisar-processo {tema}` | Pipeline completo (triagem -> entrega) | 2-4 horas |
| `*pesquisar-jurisprudencia {tema}` | Fase 1-2 apenas (pesquisa + analise) | 30-60 min |
| `*analisar-relator {relator}` | Perfil e tendencia de Relator | 15-30 min |
| `*validar-fundamentacao {path}` | Auditoria de qualidade + conformidade | 10-20 min |

### Tarefas por Agente

| Comando | Agente | Output |
|---------|--------|--------|
| `*classificar-processo {descricao}` | @barbosa-classifier | Classificacao TPU/SGT + DATAJUD |
| `*verificar-admissibilidade {processo}` | @fux-procedural | Relatorio de admissibilidade |
| `*pesquisar-constitucional {tema}` | @mendes-researcher | Jurisprudencia constitucional |
| `*consolidar-precedentes {tema}` | @toffoli-aggregator | Mapa de precedentes consolidados |
| `*analisar-direitos-fundamentais {caso}` | @moraes-analyst | Analise de direitos fundamentais |
| `*indexar-jurisprudencia {acordaos}` | @weber-indexer | Indice tematico categorizado |
| `*estrategia-argumentativa {caso}` | @barroso-strategist | Estrategia de argumentacao |
| `*analisar-precedente {acordao}` | @fachin-precedent | Analise de distinguishing/overruling |
| `*jurimetria {tema}` | @nunes-quantitative | Analise quantitativa/estatistica |
| `*perfil-relator {ministro}` | @carmem-relator | Perfil completo do Relator |
| `*validar-processo {fundamentacao}` | @theodoro-validator | Validacao processual |
| `*qualidade-precedente {analise}` | @marinoni-quality | Score de qualidade |
| `*formatar-datajud {dados}` | @datajud-formatter | Dados formatados DATAJUD/JUSBRASIL |

### Gestao de Dominio

| Comando | Descricao |
|---------|-----------|
| `*criar-dominio-juridico {area}` | Criar novo dominio (ex: Direito Ambiental) |
| `*carregar-dominio {area}` | Ativar dominio existente |
| `*listar-dominios` | Mostrar dominios disponiveis |

### Conformidade CNJ

| Comando | Descricao |
|---------|-----------|
| `*validar-cnj {processo}` | Verificacao de conformidade CNJ |
| `*gerar-relatorio-datajud {dados}` | Gerar relatorio padrao DATAJUD |
| `*audit-resolucoes {processo}` | Auditoria contra Resolucoes CNJ |

---

## Estrutura de Arquivos

```
squads/legal-analyst/
+-- agents/
|   +-- legal-chief.md                  # Orquestrador
|   +-- barbosa-classifier.md           # Classificacao processual (TPU/SGT)
|   +-- fux-procedural.md               # Admissibilidade e requisitos
|   +-- cnj-compliance.md               # Conformidade CNJ/DATAJUD
|   +-- mendes-researcher.md            # Pesquisa constitucional
|   +-- toffoli-aggregator.md           # Consolidacao de precedentes
|   +-- moraes-analyst.md               # Direitos fundamentais
|   +-- weber-indexer.md                # Indexacao tematica
|   +-- barroso-strategist.md           # Estrategia argumentativa
|   +-- fachin-precedent.md             # Analise de precedentes
|   +-- nunes-quantitative.md           # Jurimetria
|   +-- carmem-relator.md              # Perfil de Relatores
|   +-- theodoro-validator.md           # Validacao processual
|   +-- marinoni-quality.md             # Qualidade de precedentes
|   +-- datajud-formatter.md            # Formatacao DATAJUD/JUSBRASIL
|
+-- tasks/
|   +-- classificar-processo.md
|   +-- verificar-admissibilidade.md
|   +-- pesquisar-jurisprudencia.md
|   +-- consolidar-precedentes.md
|   +-- analisar-direitos-fundamentais.md
|   +-- indexar-jurisprudencia.md
|   +-- estrategia-argumentativa.md
|   +-- analisar-precedente.md
|   +-- jurimetria.md
|   +-- perfil-relator.md
|   +-- validar-fundamentacao.md
|   +-- qualidade-precedente.md
|   +-- formatar-datajud.md
|   +-- analisar-processo-completo.md
|
+-- templates/
|   +-- processo-analise-tmpl.yaml      # Analise processual completa
|   +-- jurisprudencia-mapa-tmpl.yaml   # Mapa de jurisprudencia
|   +-- relator-perfil-tmpl.yaml        # Perfil de Relator
|   +-- precedente-ficha-tmpl.yaml      # Ficha de precedente
|   +-- datajud-output-tmpl.yaml        # Output DATAJUD
|   +-- fundamentacao-tmpl.yaml         # Fundamentacao juridica
|   +-- jurimetria-report-tmpl.yaml     # Relatorio jurimetrico
|   +-- cnj-compliance-report-tmpl.yaml # Relatorio conformidade CNJ
|   +-- estrategia-tmpl.yaml            # Estrategia argumentativa
|   +-- parecer-tmpl.yaml               # Parecer juridico
|
+-- checklists/
|   +-- classificacao-processual-check.md
|   +-- admissibilidade-check.md
|   +-- fundamentacao-quality-check.md
|   +-- precedente-quality-check.md
|   +-- cnj-resolucoes-check.md
|   +-- datajud-schema-check.md
|   +-- jurimetria-check.md
|   +-- relator-analysis-check.md
|   +-- direitos-fundamentais-check.md
|   +-- argumentacao-check.md
|   +-- citacao-check.md
|   +-- entrega-final-check.md
|
+-- workflows/
|   +-- wf-analise-processual-completa.yaml
|   +-- wf-pesquisa-jurisprudencial.yaml
|   +-- wf-analise-relator.yaml
|   +-- wf-validacao.yaml
|
+-- data/
|   +-- legal-kb.md                     # Knowledge Base completa
|   +-- tpu-classes-reference.md        # Tabela Processual Unificada
|   +-- datajud-schema-reference.md     # Schema DATAJUD
|   +-- cnj-resolucoes-reference.md     # Resolucoes CNJ relevantes
|   +-- tribunais-reference.md          # Estrutura dos Tribunais
|   +-- relatores-reference.md          # Referencia de Relatores
|
+-- scripts/
|   +-- datajud-query.py                # Consulta DATAJUD API
|   +-- jurimetria-calc.py              # Calculos jurimetricos
|   +-- precedent-parser.py             # Parser de acordaos
```

---

## Workflows

### 1. Analise Processual Completa (`wf-analise-processual-completa.yaml`)

**Duracao:** 2-4 horas

**Fases:**
1. **Triagem (Fase 0)** — Classificacao TPU/SGT + verificacao admissibilidade + carga CNJ
2. **Pesquisa (Fase 1)** — Pesquisa jurisprudencial + consolidacao de precedentes
3. **Analise (Fase 2)** — Analise de Relatores + jurimetria + direitos fundamentais
4. **Fundamentacao (Fase 3)** — Estrategia argumentativa + construcao da fundamentacao
5. **Validacao (Fase 4)** — Auditoria de qualidade + conformidade CNJ/DATAJUD
6. **Entrega (Fase 5)** — Pacote final formatado DATAJUD + relatorio JUSBRASIL-style

**Agentes envolvidos:** Todos os 14

---

### 2. Pesquisa Jurisprudencial (`wf-pesquisa-jurisprudencial.yaml`)

**Duracao:** 30-60 min

**Fases:** 0-2 apenas (antes da fundamentacao)

**Output:** Mapa de jurisprudencia, precedentes consolidados, perfil de Relatores

---

### 3. Analise de Relator (`wf-analise-relator.yaml`)

**Duracao:** 15-30 min

**Processo:** Levantamento de votos -> Analise de tendencias -> Divergencias -> Perfil

**Agentes:** @carmem-relator + @nunes-quantitative + @fachin-precedent

---

### 4. Validacao (`wf-validacao.yaml`)

**Duracao:** 10-20 min

**Processo:** 12 checklists (8 juridicos + 4 CNJ/DATAJUD) + scoring + recomendacoes

**Agente:** @theodoro-validator + @marinoni-quality + @legal-chief

---

## Sistema de Conformidade CNJ

**Resolucoes CNJ Integradas:**

| Resolucao | Tema | Impacto no Pipeline |
|-----------|------|---------------------|
| Res. 331/2020 | Base Nacional de Dados do Poder Judiciario (DATAJUD) | Schema de dados obrigatorio |
| Res. 335/2020 | Plataforma Digital do Poder Judiciario (PDPJ) | Integracao de sistemas |
| Res. 332/2020 | Etica e IA no Poder Judiciario | Limites de automacao |
| Res. 396/2021 | Tabelas Processuais Unificadas (TPU) | Classificacao obrigatoria |
| Res. 235/2016 | Padronizacao de dados | Formato de dados |
| Res. 185/2013 | Processo Judicial Eletronico (PJe) | Integracao com PJe |

---

## Padrao de Qualidade

**Todo entregavel passa por:**

1. **Classificacao TPU/SGT** — Processo classificado conforme tabelas unificadas
2. **Admissibilidade** — Requisitos processuais verificados (CPC/CPP)
3. **Fundamentacao Art. 489** — Decisao fundamentada conforme CPC Art. 489 ss 1o
4. **Precedentes Qualificados** — Jurisprudencia citada e qualificada (ratio decidendi vs obiter dictum)
5. **Relator-Aware** — Posicionamento do Relator mapeado e considerado
6. **Jurimetria Validada** — Dados estatisticos verificados e significativos
7. **CNJ-Compliant** — Conformidade com Resolucoes CNJ aplicaveis
8. **DATAJUD-Schema** — Dados estruturados conforme schema DATAJUD
9. **Citacao Completa** — Todas as citacoes com numero do processo, Relator, orgao julgador, data
10. **Argumentacao Coerente** — Estrategia argumentativa logica e fundamentada

**Plus:**
11. **Conformidade LGPD** — Dados pessoais anonimizados conforme LGPD
12. **Acessibilidade** — Formato acessivel e navegavel (estilo JUSBRASIL)

**Falha em qualquer gate = BLOQUEIO. Sem excecoes.**

---

## Frameworks Principais

| Framework | Fonte | O Que Faz | Quando Usar |
|-----------|-------|-----------|-------------|
| **TPU/SGT** | CNJ Res. 396/2021 | Classificacao processual unificada | Toda classificacao |
| **DATAJUD Schema** | CNJ Res. 331/2020 | Estrutura de dados padronizada | Todo dado processual |
| **CPC Art. 489** | Lei 13.105/2015 | Requisitos de fundamentacao | Toda fundamentacao |
| **Precedentes (CPC 926-928)** | Lei 13.105/2015 | Sistema de precedentes vinculantes | Toda analise de precedente |
| **Proporcionalidade** | Doutrina/STF | Ponderacao de principios | Conflitos de direitos |
| **Jurimetria** | ABJ/CONPEDI | Analise quantitativa de decisoes | Tendencias e previsoes |
| **Stare Decisis** | Marinoni/Common Law | Respeito a precedentes | Coerencia decisoria |
| **Distinguishing** | CPC Art. 489 ss 1o VI | Diferenciacao de precedentes | Afastamento de precedente |
| **IRDR/IAC** | CPC Art. 976-987 | Resolucao de demandas repetitivas | Temas repetitivos |
| **Controle Concentrado** | CF/88 Art. 102-103 | Constitucionalidade de normas | Questoes constitucionais |

---

## Links

- **Knowledge Base:** `squads/legal-analyst/data/legal-kb.md`
- **TPU Reference:** `squads/legal-analyst/data/tpu-classes-reference.md`
- **DATAJUD Schema:** `squads/legal-analyst/data/datajud-schema-reference.md`
- **CNJ Resolucoes:** `squads/legal-analyst/data/cnj-resolucoes-reference.md`
- **Tribunais:** `squads/legal-analyst/data/tribunais-reference.md`
- **Relatores:** `squads/legal-analyst/data/relatores-reference.md`

---

## Historico de Versoes

| Versao | Data | Descricao |
|--------|------|-----------|
| 1.0.0 | 2026-03-11 | Lancamento inicial — Pipeline completo de analise processual |

---

**Analista Processual Squad v1.0.0** — Analise processual fundamentada em jurisprudencia e precedentes, em escala.
