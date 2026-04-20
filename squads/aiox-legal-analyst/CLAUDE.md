# Legal Analyst Squad — Analista Processual

## Entry Point Unico

**O usuario NAO precisa saber comandos ou nomes de agentes.** Basta descrever o que quer em linguagem natural.

```
@legal-analyst {qualquer descricao em linguagem natural}
```

Legal Analyst automaticamente:
1. **Recebe o PDF** do processo (upload via webapp ou pasta `webapp/uploads/`)
2. **Classifica** o processo (TPU/SGT, admissibilidade, CNJ)
3. **Pesquisa** jurisprudencia e precedentes
4. **Analisa** relatores, jurimetria e direitos fundamentais
5. **Constroi** a estrategia argumentativa com fundamentacao CPC Art. 489
6. **Valida** qualidade, conformidade CNJ e formato DATAJUD
7. **Entrega** relatorio completo + pecas + dados estruturados

---

## Como Enviar um Arquivo

### Opcao 1: Webapp (interface visual)

```bash
cd squads/legal-analyst/webapp
./deploy.sh local
# Acesse http://localhost:3000
# Faca upload do PDF pela interface
# Digite *intake no chat
```

### Opcao 2: API (curl)

```bash
# 1. Criar sessao
SESSION=$(curl -s -X POST http://localhost:8000/api/sessions | jq -r '.session_id')

# 2. Upload do PDF
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@/caminho/para/processo.pdf" \
  -H "X-Session-Id: $SESSION"

# 3. Iniciar pipeline
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION\", \"message\": \"*intake\"}"
```

### Opcao 3: CLI (script direto)

```bash
./scripts/intake.sh /caminho/para/processo.pdf
```

---

## Comandos Disponiveis

| Comando | Agente | Fase | Descricao |
|---------|--------|------|-----------|
| `*intake` | @legal-chief | 0-5 | Pipeline completo automatico |
| `*analisar-processo {tema}` | @legal-chief | 0-5 | Pipeline completo com tema |
| `*classificar-processo {desc}` | @barbosa-classifier | 0 | Classificacao TPU/SGT |
| `*pesquisar-jurisprudencia {tema}` | @mendes-researcher | 1 | Pesquisa de precedentes |
| `*estrategia-argumentativa {caso}` | @barroso-strategist | 3 | Estrategia completa |
| `*ponderar-principios {p1} vs {p2}` | @barroso-strategist | 3 | Ponderacao de Alexy |
| `*analisar-relator {ministro}` | @carmem-relator | 2 | Perfil do relator |
| `*jurimetria {tema}` | @nunes-quantitative | 2 | Analise quantitativa |
| `*minutar {tipo}` | @barroso-strategist | 3 | Minuta de peca processual |
| `*validar-fundamentacao` | @theodoro-validator | 4 | Validacao CPC Art. 489 |
| `*cnj-check {processo}` | @cnj-compliance | 4 | Conformidade CNJ |
| `*relatorio` | @legal-chief | 5 | Relatorio estrategico |
| `*agentes` | — | — | Listar todos os agentes |

---

## Exemplos de Uso Natural

| O usuario diz | Legal Analyst faz |
|---------------|-------------------|
| "analisa esse processo de dano moral" | *intake → pipeline completo |
| "negativacao indevida por banco" | *estrategia-argumentativa → @barroso-strategist |
| "pesquisa jurisprudencia sobre usucapiao" | *pesquisar → @mendes-researcher + @toffoli-aggregator |
| "qual o perfil do Min. Barroso nesse tema?" | *analisar-relator → @carmem-relator |
| "elabora contrarrazoes" | *minutar contrarrazoes → @barroso-strategist |
| "ta conforme o CNJ?" | *cnj-check → @cnj-compliance |

---

## Pipeline Completo (6 Fases)

```
PDF Upload
    |
FASE 0: TRIAGEM
  @barbosa-classifier → @fux-procedural → @cnj-compliance
  Gate: Classificado? Admissivel? CNJ carregado?
    |
FASE 1: PESQUISA
  @mendes-researcher → @toffoli-aggregator → @weber-indexer
  Gate: 5+ acordaos relevantes?
    |
FASE 2: ANALISE (paralelo)
  @fachin-precedent | @nunes-quantitative | @carmem-relator | @barroso-strategist | @moraes-analyst
  Gate: Precedentes analisados? Jurimetria OK? Relatores mapeados?
    |
FASE 3: FUNDAMENTACAO
  @barroso-strategist → @fachin-precedent
  Gate: CPC Art. 489 atendido? [REVISAO HUMANA]
    |
FASE 4: VALIDACAO
  @theodoro-validator → @marinoni-quality → @cnj-compliance → @datajud-formatter
  Gate: Qualidade OK? CNJ PASS? DATAJUD schema OK?
    |
FASE 5: ENTREGA
  @legal-chief → Relatorio final + DATAJUD + minds/{tema}/
```

---

## 15 Agentes Especializados

### Tier 0: Triagem
| Agente | Mente | Funcao |
|--------|-------|--------|
| @barbosa-classifier | Min. Joaquim Barbosa | Classificacao TPU/SGT |
| @fux-procedural | Min. Luiz Fux | Admissibilidade CPC |
| @cnj-compliance | CNJ/DATAJUD | Conformidade CNJ |

### Tier 1: Pesquisa
| Agente | Mente | Funcao |
|--------|-------|--------|
| @mendes-researcher | Min. Gilmar Mendes | Pesquisa constitucional |
| @toffoli-aggregator | Min. Dias Toffoli | Consolidacao de precedentes |
| @weber-indexer | Min. Rosa Weber | Indexacao tematica |

### Tier 2: Analise
| Agente | Mente | Funcao |
|--------|-------|--------|
| @moraes-analyst | Min. Alexandre de Moraes | Direitos fundamentais |
| @barroso-strategist | Min. Luis Roberto Barroso | Estrategia argumentativa |
| @fachin-precedent | Min. Edson Fachin | Analise de precedentes |
| @nunes-quantitative | Min. Ricardo Lewandowski | Jurimetria |
| @carmem-relator | Min. Carmen Lucia | Perfil de relatores |

### Tier 3: Validacao e Entrega
| Agente | Mente | Funcao |
|--------|-------|--------|
| @theodoro-validator | Humberto Theodoro Jr. | Validacao processual |
| @marinoni-quality | Luiz Guilherme Marinoni | Qualidade de precedentes |
| @datajud-formatter | DATAJUD/JUSBRASIL | Formatacao de dados |

### Orquestrador
| Agente | Funcao |
|--------|--------|
| @legal-chief | Pipeline completo, routing, quality gates |

---

## Principios

- **JURISPRUDENCIA > OPINIAO** — Toda analise fundamentada em julgados reais
- **CNJ-COMPLIANT** — Resolucoes do CNJ sao gates obrigatorios
- **DATAJUD-FIRST** — Dados estruturados conforme padrao DATAJUD
- **RELATOR-AWARE** — Posicionamento do Relator influencia resultado
- **CPC Art. 489** — Fundamentacao qualificada obrigatoria
